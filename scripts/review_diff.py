"""Write a review file listing only items that are new or changed since a reviewed dataset.

    uv run python scripts/review_diff.py evals/data/review_round1/dataset_reviewed.jsonl \
        evals/data/REVIEW_ROUND2.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from rag_eval.schema import read_jsonl
from rag_eval.text import normalize
from rescue_rag.config import project_path


def text_key(d: dict) -> tuple[str, str, str]:
    """Identity of a text question: source filing + Item + reference answer."""
    g = d["gold"]
    return (g["accessions"][0], (g.get("items") or [""])[0], normalize(str(d["answer"])))


def main() -> int:
    old_path, out_path = Path(sys.argv[1]), Path(sys.argv[2])
    old = [json.loads(line) for line in old_path.read_text(encoding="utf-8").splitlines() if line]
    new = read_jsonl(project_path("evals/data/dataset.jsonl"))
    old_text = {text_key(d): d for d in old if d["type"] == "factual_text"}
    old_other = {d["id"]: d for d in old if d["type"] != "factual_text"}

    new_items, changed, unchanged = [], [], 0
    for it in new:
        d = it.model_dump()
        prev = old_text.get(text_key(d)) if it.type == "factual_text" else old_other.get(it.id)
        if prev is None:
            new_items.append((it, None))
        elif prev["question"] != it.question or prev["gold"]["evidence"] != it.gold.evidence:
            changed.append((it, prev))
        else:
            unchanged += 1

    lines = [
        f"# Eval set review - changes since {old_path.parent.name}",
        "",
        "Only items that are new or changed since the previous review round are listed. "
        f"{unchanged} items are unchanged and keep their earlier verdict.",
        "Write OK or the problem after each **Review:** line.",
        "",
    ]
    text_changed = [c for c in changed if c[0].type == "factual_text"]
    templated = [c for c in changed if c[0].type != "factual_text"]
    groups = (
        ("New items (replacements and re-paired comparisons)", new_items),
        ("Changed text items (wording or evidence)", text_changed),
    )
    for title, group in groups:
        lines += [f"## {title} ({len(group)})", ""]
        for it, prev in group:
            lines += [f"### {it.id} ({it.type}, {it.split})"]
            if prev and prev["question"] != it.question:
                lines += [f"**Was ({prev['id']}):** {prev['question']}"]
            lines += [
                f"**Q:** {it.question}",
                f"**A:** {it.answer} {it.unit or ''}".rstrip(),
                f"**Expected:** {it.expected_behavior}",
                f"**Evidence:** {' || '.join(it.gold.evidence) or '-'}",
                *([f"**Values:** {it.notes}"] if it.type == "comparison" else []),
                "**Review:** ",
                "",
            ]
    lines += [
        f"## Template rewording, code-generated items ({len(templated)})",
        "",
        "Systematic wording changes from template fixes (see the review feedback files).",
        "Skim; answers are unchanged.",
        "",
    ]
    lines += [f"- {it.id}: {it.question}" for it, _ in templated]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(new_items)} new, {len(changed)} changed, {unchanged} unchanged -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
