"""Pre-compute the demo's answers from finished evaluation runs (no new API calls).

    uv run python scripts/build_demo_examples.py   # -> app/examples.json

Every one of the 150 eval questions is included with the answers v0, v0-small and v1 actually
gave in the runs reported in the README (dev runs for dev questions, run 1 for test questions),
so visitors can browse everything - misses included - without the demo making any API call.
"""

from __future__ import annotations

import json
import sys

from rag_eval.schema import EvalItem, read_jsonl
from rescue_rag.config import project_path

RUNS = {
    "dev": {
        "v0": "v0_dev_20261026-225136",
        "v0-small": "v0-small_dev_20261026-225227",
        "v1": "v1_dev_20261026-235534",
    },
    "test": {
        "v0": "v0_test_20261027-001212_rep1",
        "v0-small": "v0-small_test_20261027-000916_rep1",
        "v1": "v1_test_20261027-000433_rep1",
    },
}
HIGHLIGHTS = [
    ("num-0028", "Structure-aware chunks: v0's fixed-size chunk cut the cash-flow table in half"),
    ("num-0026", "Structure-aware chunks: the balance sheet total is retrieved as a labelled row"),
    ("calc-0007", "Calculator tool: the formula is evaluated in code, inputs cited"),
    ("comp-a35732", "Per-company retrieval: both companies' statements are retrieved"),
    ("unans-0016", "Grounding: the cheap naive model answers from memory; v1 says 'not found'"),
    ("unans-0012", "Grounding: a year outside the corpus - nothing retrieved, no guessing"),
    ("text-99b505", "Year filters: v1 answers from the right fiscal year's filing"),
    ("comp-feb2ad", "Honest miss: v1 didn't retrieve J&J's revenue line, so it says 'not found'"),
]
TYPE_LABELS = {
    "numeric_lookup": "Number lookup",
    "numeric_compute": "Calculation",
    "comparison": "Comparison",
    "factual_text": "Text fact",
    "unanswerable": "Unanswerable",
}


def expected(it: EvalItem) -> str:
    """Gold answer as a reader would write it."""
    a = it.answer
    if it.type == "unanswerable":
        return "Not answerable from the filings (should say so, not guess)"
    if isinstance(a, str):
        return a
    if it.unit == "percent":
        return f"{a:.2f}%"
    if it.unit == "USD/shares":
        return f"${a:,.2f} per share"
    return f"${a / 1e6:,.0f} million"


def _load(run: str) -> tuple[dict, dict]:
    d = project_path(f"evals/results/{run}")
    resp = {r["id"]: r for r in map(json.loads, (d / "responses.jsonl").open(encoding="utf-8"))}
    sc = {s["id"]: s for s in map(json.loads, (d / "scores.jsonl").open(encoding="utf-8"))}
    return resp, sc


def main() -> int:
    items = read_jsonl(project_path("evals/data/dataset.jsonl"))
    chunk_text = {}
    with project_path("app/index/s2_tables/chunks.jsonl").open(encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            chunk_text[c["chunk_id"]] = c["text"]
    loaded = {split: {k: _load(r) for k, r in runs.items()} for split, runs in RUNS.items()}
    lessons = dict(HIGHLIGHTS)

    entries = []
    for it in items:
        assert it.split is not None
        entry = {
            "id": it.id,
            "split": it.split,
            "type": TYPE_LABELS[it.type],
            "question": it.question,
            "expected": expected(it),
            "lesson": lessons.get(it.id, ""),
            "systems": {},
        }
        for name, (resp, sc) in loaded[it.split].items():
            r, s = resp[it.id], sc[it.id]
            entry["systems"][name] = {
                "answer": r.get("answer", r.get("error", "")),
                "correct": s["correct"],
                "cost_usd": r.get("cost_usd"),
                "latency_s": r.get("latency_s"),
                "citations": [
                    {"id": cid, "text": chunk_text.get(cid, "")[:600]}
                    for cid in r.get("citations", [])
                ],
            }
        entries.append(entry)
    out = {"highlights": [i for i, _ in HIGHLIGHTS], "items": entries}
    path = project_path("app/examples.json")
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(entries)} questions ({len(HIGHLIGHTS)} highlights) -> {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
