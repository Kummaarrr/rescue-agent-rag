"""Build the 150-question evaluation set and freeze the dev/test split.

    uv run python scripts/build_evalset.py            # full build (Claude drafts text questions)
    uv run python scripts/build_evalset.py --no-llm   # only the code-generated question types

Outputs (committed):
    evals/data/dataset.jsonl        the dataset
    evals/data/generation_log.txt   every rejected candidate and why
    evals/data/REVIEW.md            with --review: all text questions + 15 random others
    (for later review rounds, scripts/review_diff.py lists only new or changed items)
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter

from rag_eval.schema import EvalItem, write_jsonl
from rescue_rag import llm
from rescue_rag.config import get_corpus, get_env, project_path
from rescue_rag.corpus import load_manifest
from rescue_rag.evalset.text_questions import text_questions
from rescue_rag.evalset.unanswerable import unanswerable_questions
from rescue_rag.evalset.xbrl_questions import (
    comparison_questions,
    compute_questions,
    legacy_comparison_draws,
    lookup_questions,
    validated_values,
)

SEED = 20261026
COUNTS = {
    "numeric_lookup": 45,
    "numeric_compute": 20,
    "comparison": 15,
    "factual_text": 40,
    "unanswerable": 30,
}
TEST_COUNTS = {
    "numeric_lookup": 15,
    "numeric_compute": 7,
    "comparison": 5,
    "factual_text": 13,
    "unanswerable": 10,
}
TEXT_CANDIDATES = 60
GENERATOR, CHECKER = "claude-opus-5-5", "claude-sonnet-5-5"
OUT = project_path("evals/data")


SPLITS_FILE = OUT / "splits.json"


def assign_splits(items: list[EvalItem], rng: random.Random) -> None:
    """Frozen split: an item listed in splits.json keeps its split forever. Only items not yet
    listed (replacements) are assigned, filling whatever each type's dev/test quota still needs.
    (A shuffle-based split moved 12 items between dev and test when one item was replaced.)"""
    frozen: dict[str, str] = (
        json.loads(SPLITS_FILE.read_text(encoding="utf-8")) if SPLITS_FILE.exists() else {}
    )
    by_type: dict[str, list[EvalItem]] = {}
    for it in items:
        by_type.setdefault(it.type, []).append(it)
    for t, group in by_type.items():
        n_test = round(TEST_COUNTS[t] * len(group) / COUNTS[t])
        for it in group:
            if it.id in frozen:
                it.split = frozen[it.id]  # type: ignore[assignment]
        new = rng.sample(
            [it for it in group if it.split is None], sum(it.split is None for it in group)
        )
        free_test = max(0, n_test - sum(it.split == "test" for it in group))
        for i, it in enumerate(new):
            it.split = "test" if i < free_test else "dev"
    SPLITS_FILE.write_text(
        json.dumps({it.id: it.split for it in sorted(items, key=lambda x: x.id)}, indent=1),
        encoding="utf-8",
    )


def review_markdown(items: list[EvalItem], rng: random.Random) -> str:
    text = [i for i in items if i.type == "factual_text"]
    others = rng.sample([i for i in items if i.type != "factual_text"], 15)
    lines = [
        "# Eval set review",
        "",
        "Mark each item OK or describe the problem. Text questions were drafted by Claude and",
        "checked by code and a second model; numeric ones come from XBRL.",
        "Fix or drop anything wrong. Note: about half the text questions come from Item 1A.",
        "",
    ]
    for title, group in (("Text questions", text), ("Random sample of other types", others)):
        lines += [f"## {title} ({len(group)})", ""]
        for it in group:
            lines += [
                f"### {it.id} ({it.type}, {it.split})",
                f"**Q:** {it.question}",
                f"**A:** {it.answer} {it.unit or ''}".rstrip(),
                f"**Evidence:** {' | '.join(it.gold.evidence) or '-'}",
                f"**Source:** {it.source}  {it.notes}".rstrip(),
                "**Review:** ",
                "",
            ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-llm", action="store_true", help="skip Claude-drafted text questions")
    parser.add_argument("--review", action="store_true", help="also write a full REVIEW.md")
    args = parser.parse_args()

    rng = random.Random(SEED)
    filings = load_manifest()
    names = {c.ticker: c.name for c in get_corpus().companies}
    log: list[str] = []

    values, value_log = validated_values(filings)
    log += value_log
    items = lookup_questions(values, filings, names, COUNTS["numeric_lookup"], rng)
    items += compute_questions(filings, names, 10, 10, rng)
    legacy_comparison_draws(values, COUNTS["comparison"], rng)  # keeps later draws unchanged
    items += comparison_questions(
        values, names, COUNTS["comparison"], random.Random(f"{SEED}-comparison"), filings
    )
    items += unanswerable_questions(filings, names, rng)

    if not args.no_llm:
        # rough projection: Opus draft ~2.5K in / 1.5K out, Sonnet check ~2.5K in / 1K out
        projected = TEXT_CANDIDATES * (2500 * 4 + 1500 * 20 + 2500 * 2 + 1000 * 10) / 1e6
        cap = get_env().max_run_cost_usd
        print(f"Text questions: {TEXT_CANDIDATES} candidates, projected <= ${projected:.2f}")
        if projected > cap:
            print(f"Projected cost exceeds MAX_RUN_COST_USD={cap}; aborting.")
            return 1
        text_items, text_log = text_questions(
            filings, names, COUNTS["factual_text"], TEXT_CANDIDATES, GENERATOR, CHECKER, rng
        )
        items += text_items
        log += text_log
        print(f"LLM usage: {llm.LEDGER.summary()}")

    assign_splits(items, rng)

    ids = [i.id for i in items]
    questions = [i.question for i in items]
    assert len(set(ids)) == len(ids), "duplicate ids"
    assert len(set(questions)) == len(questions), "duplicate questions"

    write_jsonl(OUT / "dataset.jsonl", items)
    (OUT / "generation_log.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    if args.review and not args.no_llm:
        (OUT / "REVIEW.md").write_text(review_markdown(items, rng), encoding="utf-8")

    print(f"\nWrote {len(items)} items to {OUT / 'dataset.jsonl'}")
    counts = Counter((i.type, i.split) for i in items)
    for t, target in COUNTS.items():
        got = counts[(t, "dev")] + counts[(t, "test")]
        flag = "" if got == target else f"   <-- target {target}"
        print(f"  {t:16} {got:3}  (dev {counts[(t, 'dev')]}, test {counts[(t, 'test')]}){flag}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
