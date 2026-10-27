"""RAGAS cross-check of a finished run (faithfulness, context precision, context recall).

    uv run python scripts/ragas_eval.py --run evals/results/v1_test_..._rep1 --collection s2_tables
        [--limit 5]

RAGAS is used as an independent, widely known reference next to the project's own metrics.
Claude is plugged in through RAGAS's LLM interface (langchain-anthropic requires anthropic<1,
which conflicts with the current SDK). The judge is the same model as the project's judge.
Only answerable questions are scored (RAGAS metrics need a reference answer).
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import uuid
import warnings
from pathlib import Path
from typing import Any

from langchain_core.outputs import Generation, LLMResult
from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.llms.base import BaseRagasLLM
from ragas.run_config import RunConfig

from rag_eval.schema import EvalItem, read_jsonl
from rescue_rag import llm
from rescue_rag.config import load_yaml, project_path
from rescue_rag.ingest.index import _lock, qdrant

warnings.filterwarnings("ignore", category=DeprecationWarning)
from ragas.metrics import (  # noqa: E402  (deprecated path still the stable one in 0.4)
    Faithfulness,
    LLMContextPrecisionWithReference,
    LLMContextRecall,
)


class ClaudeForRagas(BaseRagasLLM):
    """Minimal RAGAS LLM adapter over rescue_rag.llm (cached, costed, no temperature)."""

    def __init__(self, model: str) -> None:
        super().__init__(run_config=RunConfig(max_workers=4, timeout=300))
        self.model = model

    def generate_text(self, prompt: Any, n: int = 1, temperature: Any = None,
                      stop: Any = None, callbacks: Any = None) -> LLMResult:  # fmt: skip
        out = llm.generate(self.model, prompt.to_string(), max_tokens=8000)
        return LLMResult(generations=[[Generation(text=out.text)] * n])

    async def agenerate_text(self, prompt: Any, n: int = 1, temperature: Any = None,
                             stop: Any = None, callbacks: Any = None) -> LLMResult:  # fmt: skip
        return await asyncio.to_thread(self.generate_text, prompt, n)

    def is_finished(self, response: LLMResult) -> bool:
        return True


def reference_text(item: EvalItem) -> str:
    """A natural-language reference answer for RAGAS (numeric gold values are numbers)."""
    a = item.answer
    if item.type == "numeric_lookup" and isinstance(a, float):
        value = f"${a:,.2f}" if item.unit == "USD/shares" else f"${a / 1e6:,.0f} million"
        return f"{value}."
    if item.type == "numeric_compute" and isinstance(a, float):
        return f"{a:.2f}%."
    if item.type == "comparison":
        return f"{a} reported the higher figure ({item.notes.split(';')[0]})."
    return str(a)


def stratified_ids(pool: list[EvalItem], n: int) -> set[str]:
    """Deterministic sample, proportional by question type; ranked by a hash of the id, so
    every system's run is scored on the same questions."""
    by_type: dict[str, list[EvalItem]] = {}
    for it in pool:
        by_type.setdefault(it.type, []).append(it)
    chosen: set[str] = set()
    for _type, group in sorted(by_type.items()):
        quota = max(1, round(n * len(group) / len(pool)))
        ranked = sorted(group, key=lambda i: hashlib.sha1(i.id.encode()).hexdigest())
        chosen |= {i.id for i in ranked[:quota]}
    return chosen


def fetch_texts(collection: str, chunk_ids: list[str]) -> dict[str, str]:
    ids = [str(uuid.uuid5(uuid.NAMESPACE_URL, c)) for c in chunk_ids]
    with _lock:
        points = qdrant().retrieve(collection, ids=ids, with_payload=True)
    return {p.payload["chunk_id"]: p.payload["text"] for p in points if p.payload}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--collection", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--sample",
        type=int,
        help="stratified sample of N answerable questions (same ids for any run)",
    )
    args = parser.parse_args()

    items = {i.id: i for i in read_jsonl(project_path("evals/data/dataset.jsonl"))}
    responses = [json.loads(line) for line in (args.run / "responses.jsonl").open(encoding="utf-8")]
    responses = [
        r for r in responses if items[r["id"]].type != "unanswerable" and r.get("contexts")
    ]
    if args.sample:
        keep = stratified_ids([items[r["id"]] for r in responses], args.sample)
        responses = [r for r in responses if r["id"] in keep]
    if args.limit:
        responses = responses[: args.limit]

    samples = []
    for r in responses:
        texts = fetch_texts(args.collection, [c["id"] for c in r["contexts"]])
        samples.append(
            SingleTurnSample(
                user_input=items[r["id"]].question,
                response=r["answer"],
                retrieved_contexts=[texts[c["id"]] for c in r["contexts"] if c["id"] in texts],
                reference=reference_text(items[r["id"]]),
            )
        )
    judge = ClaudeForRagas(load_yaml("models.yaml")["judge_model"])
    metrics = [Faithfulness(llm=judge), LLMContextPrecisionWithReference(llm=judge),
               LLMContextRecall(llm=judge)]  # fmt: skip
    run_config = RunConfig(max_workers=4, timeout=300)
    dataset = EvaluationDataset(samples=samples)
    result = evaluate(
        dataset, metrics=metrics, llm=judge, run_config=run_config, show_progress=False
    )
    df = result.to_pandas()
    cols = [c for c in df.columns if c in ("faithfulness", "llm_context_precision_with_reference",
                                           "context_recall")]  # fmt: skip
    means = {c: float(df[c].mean()) for c in cols}
    out = {"run": args.run.name, "n": len(samples), "ragas_version": "0.4.3", **means,
           "judge": judge.model, "api_spend_usd": round(llm.LEDGER.cost_usd, 4)}  # fmt: skip
    (args.run / "ragas.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    print(f"API spend: {llm.LEDGER.summary()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
