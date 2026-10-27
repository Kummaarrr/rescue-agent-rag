"""Run a pipeline over eval items, grade the responses, summarise the metrics.

Outputs under <out_dir>/<run_id>/:
    responses.jsonl   answer + context ids/sources (no context text, to keep results small)
    scores.jsonl      one Score per item
    summary.json      the metrics
    summary.md        the metrics as a table
"""

from __future__ import annotations

import json
import statistics
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from rag_eval.adapters import Pipeline, Response
from rag_eval.grading import Score, grade
from rag_eval.schema import EvalItem


class CostCapExceeded(RuntimeError):
    pass


def run_pipeline(
    pipeline: Pipeline,
    items: list[EvalItem],
    *,
    workers: int,
    spent: Callable[[], float],
    cost_cap_usd: float,
) -> dict[str, Response | Exception]:
    """Answers for every item. Stops submitting new work once `spent()` passes the cap."""
    out: dict[str, Response | Exception] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {}
        for it in items:
            if spent() > cost_cap_usd:
                break
            futures[pool.submit(pipeline, it.question)] = it.id
        for f in as_completed(futures):
            try:
                out[futures[f]] = f.result()
            except Exception as e:  # recorded per item; one failure must not stop the run
                out[futures[f]] = e
    if len(out) < len(items):
        raise CostCapExceeded(f"stopped after {len(out)}/{len(items)} items (cost cap)")
    return out


def _pct(xs: list[float], q: float) -> float | None:
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(len(xs) - 1, round(q * (len(xs) - 1)))]


def _rate(flags: list[bool | None]) -> float | None:
    vals = [f for f in flags if f is not None]
    return sum(vals) / len(vals) if vals else None


def summarize(scores: list[Score]) -> dict[str, Any]:
    by_type: dict[str, list[Score]] = {}
    for s in scores:
        by_type.setdefault(s.type, []).append(s)
    answerable = [s for s in scores if s.type != "unanswerable"]
    unans = by_type.get("unanswerable", [])

    # abstain F1: positive class = "system declined" (abstained or rejected the premise)
    declined = {s.id for s in scores if s.behavior != "answered"}
    tp = sum(1 for s in unans if s.id in declined)
    fp = sum(1 for s in answerable if s.id in declined)
    fn = len(unans) - tp
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    costs = [s.cost_usd for s in scores if s.cost_usd is not None]
    lat = [s.latency_s for s in scores if s.latency_s is not None]
    faith = [s.faithfulness for s in scores if s.faithfulness is not None]
    return {
        "n": len(scores),
        "errors": sum(1 for s in scores if s.error),
        "accuracy_by_type": {t: _rate([s.correct for s in g]) for t, g in sorted(by_type.items())},
        "numeric_accuracy": _rate(
            [s.correct for s in scores if s.type in ("numeric_lookup", "numeric_compute")]
        ),
        "text_pass_rate": _rate([s.correct for s in by_type.get("factual_text", [])]),
        "overall_accuracy": _rate([s.correct for s in scores]),
        "hallucination_rate_unanswerable": _rate([s.behavior == "answered" for s in unans]),
        "false_abstain_rate_answerable": _rate([s.id in declined for s in answerable]),
        "abstain_f1": f1,
        "doc_recall": _rate([s.doc_hit for s in answerable]),
        "evidence_recall": _rate([s.evidence_hit for s in answerable]),
        "citation_accuracy": _rate([s.citation_hit for s in answerable if s.correct]),
        "faithfulness": statistics.mean(faith) if faith else None,
        "latency_p50_s": _pct(lat, 0.5),
        "latency_p95_s": _pct(lat, 0.95),
        "cost_per_1000_queries_usd": 1000 * statistics.mean(costs) if costs else None,
    }


def summary_markdown(run_id: str, summary: dict[str, Any]) -> str:
    def fmt(v: Any, pct: bool = True) -> str:
        if v is None:
            return "n/a"
        return f"{100 * v:.1f}%" if pct else f"{v:.2f}"

    rows = [
        ("Overall accuracy", fmt(summary["overall_accuracy"])),
        ("Numeric accuracy (lookup + compute)", fmt(summary["numeric_accuracy"])),
        *[(f"  - {t}", fmt(v)) for t, v in summary["accuracy_by_type"].items()],
        ("Text answers passing judge (>=4/5)", fmt(summary["text_pass_rate"])),
        ("Hallucination rate (unanswerable)", fmt(summary["hallucination_rate_unanswerable"])),
        ("False abstain rate (answerable)", fmt(summary["false_abstain_rate_answerable"])),
        ("Abstain F1", fmt(summary["abstain_f1"], pct=False)),
        ("Retrieval: gold filing retrieved", fmt(summary["doc_recall"])),
        ("Retrieval: gold evidence retrieved", fmt(summary["evidence_recall"])),
        ("Citation accuracy (correct answers)", fmt(summary.get("citation_accuracy"))),
        ("Faithfulness", fmt(summary["faithfulness"])),
        ("Latency p50 / p95 (s)",
         f"{fmt(summary['latency_p50_s'], False)} / {fmt(summary['latency_p95_s'], False)}"),
        ("Cost per 1,000 queries (USD)", fmt(summary["cost_per_1000_queries_usd"], False)),
    ]  # fmt: skip
    lines = [f"# {run_id}", "", f"{summary['n']} items, {summary['errors']} errors", ""]
    lines += ["| Metric | Value |", "|---|---|"] + [f"| {k} | {v} |" for k, v in rows]
    return "\n".join(lines) + "\n"


def evaluate(
    pipeline: Pipeline,
    items: list[EvalItem],
    out_dir: Path,
    *,
    reader_model: str,
    judge_model: str,
    with_faithfulness: bool,
    spent: Callable[[], float],
    cost_cap_usd: float,
    workers: int = 4,
    run_suffix: str = "",
) -> dict[str, Any]:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    run_id = f"{pipeline.name}_{items[0].split or 'all'}_{stamp}{run_suffix}"
    run_dir = out_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    responses = run_pipeline(
        pipeline, items, workers=workers, spent=spent, cost_cap_usd=cost_cap_usd
    )
    with (run_dir / "responses.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for it in items:
            r = responses[it.id]
            rec: dict[str, Any] = {"id": it.id}
            if isinstance(r, Exception):
                rec["error"] = repr(r)
            else:
                rec |= {
                    "answer": r.answer,
                    "contexts": [{"id": c.chunk_id, "source": c.accession} for c in r.contexts],
                    "citations": r.citations,
                    "cost_usd": r.cost_usd,
                    "latency_s": r.latency_s,
                    "meta": r.meta,
                }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def grade_one(it: EvalItem) -> Score:
        r = responses[it.id]
        if isinstance(r, Exception):
            return Score(it.id, it.type, it.split, "answered", False, error=repr(r))
        return grade(
            it, r, reader_model=reader_model, judge_model=judge_model,
            with_faithfulness=with_faithfulness,
        )  # fmt: skip

    with ThreadPoolExecutor(max_workers=workers) as pool:
        scores = list(pool.map(grade_one, items))
    with (run_dir / "scores.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for s in scores:
            f.write(json.dumps(s.to_dict(), ensure_ascii=False) + "\n")

    summary = summarize(scores)
    summary["run_id"] = run_id
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (run_dir / "summary.md").write_text(summary_markdown(run_id, summary), encoding="utf-8")
    return summary
