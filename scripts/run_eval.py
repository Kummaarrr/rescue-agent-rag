"""Evaluate a pipeline on a split of the eval set.

    uv run python scripts/run_eval.py --pipeline v0 --split dev [--limit 10] [--faithfulness]

The test split is held out: it is only run at the end of a release (pass --i-mean-it).
"""

from __future__ import annotations

import argparse
import sys

from rag_eval.runner import CostCapExceeded, evaluate, summary_markdown
from rag_eval.schema import read_jsonl
from rescue_rag import llm
from rescue_rag.agent.graph import V1Agent
from rescue_rag.baseline.v0 import V0Pipeline
from rescue_rag.config import get_env, load_yaml, project_path
from rescue_rag.pipeline import LADDER, RescuePipeline

PIPELINES = {
    "v0": lambda: V0Pipeline("large_model"),
    "v0-small": lambda: V0Pipeline("small_model"),
    **{name: (lambda c=cfg: RescuePipeline(c)) for name, cfg in LADDER.items()},
    "v1": lambda: V1Agent(),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipeline", choices=sorted(PIPELINES), required=True)
    parser.add_argument("--split", choices=["dev", "test"], default="dev")
    parser.add_argument("--limit", type=int, help="only the first N items (smoke test)")
    parser.add_argument("--faithfulness", action="store_true", help="also judge faithfulness")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--i-mean-it", action="store_true", help="required for the test split")
    parser.add_argument(
        "--repeats", type=int, default=1,
        help="independent runs (fresh model calls per repeat); faithfulness on the first only",
    )  # fmt: skip
    args = parser.parse_args()

    if args.split == "test" and not args.i_mean_it:
        print("The test split is held out until the end of a release. Pass --i-mean-it.")
        return 1

    items = [
        i for i in read_jsonl(project_path("evals/data/dataset.jsonl")) if i.split == args.split
    ]
    if args.limit:
        items = items[:: max(1, len(items) // args.limit)][: args.limit]  # spread over types
    models = load_yaml("models.yaml")
    cap = get_env().max_run_cost_usd
    print(f"{args.pipeline} on {args.split}: {len(items)} items, cost cap ${cap:.2f}")

    for rep in range(1, args.repeats + 1):
        if args.repeats > 1:
            llm.set_cache_namespace(f"{args.split}-rep{rep}")
        try:
            summary = evaluate(
                PIPELINES[args.pipeline](),
                items,
                project_path("evals/results"),
                reader_model=models["small_model"],
                judge_model=models["judge_model"],
                with_faithfulness=args.faithfulness and rep == 1,
                spent=lambda: llm.LEDGER.cost_usd,
                cost_cap_usd=cap * rep,  # the cap applies per repeat
                workers=args.workers,
                run_suffix=f"_rep{rep}" if args.repeats > 1 else "",
            )
        except CostCapExceeded as e:
            print(f"Aborted: {e}. Spent so far: {llm.LEDGER.summary()}")
            return 1
        print(summary_markdown(summary["run_id"], summary))
    print(f"API spend this run: {llm.LEDGER.summary()}")
    for model, cost in sorted(llm.LEDGER.by_model.items()):
        print(f"  {model}: ${cost:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
