"""Aggregate repeated runs on a split: mean and range per metric, per system.

uv run python scripts/final_table.py --split test > evals/results/FINAL_test.md
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict

from rescue_rag.config import project_path

SYSTEMS = [
    ("v0", "v0: naive RAG, Claude Opus 5.5"),
    ("v0-small", "v0-small: naive RAG, Claude Haiku 5.5"),
    ("v1", "v1: rescued, Claude Haiku 5.5"),
]
METRICS = [
    ("Overall accuracy", "overall_accuracy", "pct"),
    ("Numeric accuracy (lookup + compute)", "numeric_accuracy", "pct"),
    ("Cross-company comparisons", ("accuracy_by_type", "comparison"), "pct"),
    ("Text answers passing judge", "text_pass_rate", "pct"),
    ("Unanswerable handled correctly", ("accuracy_by_type", "unanswerable"), "pct"),
    ("Hallucination rate (unanswerable)", "hallucination_rate_unanswerable", "pct"),
    ("False abstain rate (answerable)", "false_abstain_rate_answerable", "pct"),
    ("Gold evidence retrieved", "evidence_recall", "pct"),
    ("Citations contain the evidence", "citation_accuracy", "pct"),
    ("Faithfulness (Opus judge, run 1)", "faithfulness", "pct"),
    ("Latency p50 (s)", "latency_p50_s", "num"),
    ("Latency p95 (s)", "latency_p95_s", "num"),
    ("Cost per 1,000 queries (USD)", "cost_per_1000_queries_usd", "usd"),
]


def get(summary: dict, key: str | tuple[str, str]) -> float | None:
    if isinstance(key, tuple):
        return summary.get(key[0], {}).get(key[1])
    return summary.get(key)


def fmt(values: list[float], kind: str) -> str:
    if not values:
        return "n/a"
    scale = 100 if kind == "pct" else 1
    vals = [v * scale for v in values]
    mean = statistics.mean(vals)
    unit = "%" if kind == "pct" else ""
    prefix = "$" if kind == "usd" else ""
    digits = 1 if kind == "pct" else 2
    if len(vals) == 1 or max(vals) - min(vals) < 1e-9:
        return f"{prefix}{mean:.{digits}f}{unit}"
    return f"{prefix}{mean:.{digits}f}{unit} ({min(vals):.{digits}f}-{max(vals):.{digits}f})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split", default="test")
    args = parser.parse_args()

    runs: dict[str, list[dict]] = defaultdict(list)
    for path in sorted(project_path("evals/results").glob(f"*_{args.split}_*_rep*/summary.json")):
        system = path.parent.name.split(f"_{args.split}_")[0]
        runs[system].append(json.loads(path.read_text(encoding="utf-8")))

    systems = [(k, label) for k, label in SYSTEMS if k in runs]
    n_items = runs[systems[0][0]][0]["n"]
    print(f"# Final results - held-out {args.split} split\n")
    print(
        f"{n_items} questions never used during development. Each system was run "
        f"{len(runs[systems[0][0]])} times with fresh model calls; cells show the mean and, "
        "in brackets, the range across runs. One question is 2 points of overall accuracy.\n"
    )
    print("| Metric | " + " | ".join(label for _, label in systems) + " |")
    print("|---|" + "---|" * len(systems))
    for name, key, kind in METRICS:
        cells = []
        for k, _ in systems:
            vals = [v for s in runs[k] if (v := get(s, key)) is not None]
            cells.append(fmt(vals, kind))
        print(f"| {name} | " + " | ".join(cells) + " |")
    print("\nRuns: " + ", ".join(f"`{s['run_id']}`" for k, _ in systems for s in runs[k]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
