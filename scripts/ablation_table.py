"""Collect the latest run of each pipeline on a split into one markdown table.

uv run python scripts/ablation_table.py --split dev > evals/results/ABLATION_dev.md
"""

from __future__ import annotations

import argparse
import json
import sys

from rescue_rag.config import project_path

ORDER = [
    "v0",
    "v0-small",
    "s1",
    "s2",
    "s3",
    "s4",
    "s4-dense",
    "s8",
    "s5",
    "s7",
    "s6",
    "s9",
    "v1",
]
LABELS = {
    "v0": "v0: naive RAG, Opus 5.5",
    "v0-small": "v0-small: naive RAG, Haiku 5.5",
    "s1": "+ S1 structure-aware chunks (Haiku)",
    "s2": "+ S2 table-aware chunks",
    "s3": "+ S3 hybrid retrieval (BM25 + dense)",
    "s4": "+ S4 company/year filters (on S3)",
    "s4-dense": "S2 + S4 filters, without S3 (v1 path)",
    "s8": "+ S8 grounded answers (citations, numeric check)",
    "s5": "S8 + S5 reranking (Voyage rerank-2.5-lite)",
    "s7": "S8 + S7 calculator tool",
    "v1": "v1 = S2 + S4 + S7 + S8 as a LangGraph agent (S6)",
}
COLUMNS = [
    ("Overall", "overall_accuracy", True),
    ("Numeric", "numeric_accuracy", True),
    ("Comparisons", ("accuracy_by_type", "comparison"), True),
    ("Text", "text_pass_rate", True),
    ("Halluc.", "hallucination_rate_unanswerable", True),
    ("False abstain", "false_abstain_rate_answerable", True),
    ("Evidence retrieved", "evidence_recall", True),
    ("Citations OK", "citation_accuracy", True),
    ("p50 s", "latency_p50_s", False),
    ("$/1k queries", "cost_per_1000_queries_usd", False),
]


def value(summary: dict, key: str | tuple[str, str]) -> float | None:
    if isinstance(key, tuple):
        return summary.get(key[0], {}).get(key[1])
    return summary.get(key)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", default="dev")
    args = parser.parse_args()

    results = project_path("evals/results")
    latest: dict[str, dict] = {}
    for path in sorted(results.glob(f"*_{args.split}_*/summary.json")):
        pipeline = path.parent.name.split(f"_{args.split}_")[0]
        latest[pipeline] = json.loads(path.read_text(encoding="utf-8"))  # sorted: last wins

    names = [p for p in ORDER if p in latest] + sorted(set(latest) - set(ORDER))
    print(f"# Ablation - {args.split} split\n")
    print("| Configuration | " + " | ".join(c[0] for c in COLUMNS) + " | Run |")
    print("|---|" + "---|" * (len(COLUMNS) + 1))
    for p in names:
        s = latest[p]
        cells = []
        for _, key, pct in COLUMNS:
            v = value(s, key)
            cells.append("n/a" if v is None else (f"{100 * v:.0f}%" if pct else f"{v:.2f}"))
        print(f"| {LABELS.get(p, p)} | " + " | ".join(cells) + f" | `{s['run_id']}` |")
    print(
        "\nEach step adds to the one above. Differences of 1-2 points are within run-to-run noise"
        " (one comparison question = 10 points of that column)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
