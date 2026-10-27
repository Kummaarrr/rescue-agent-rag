"""The v1 pipeline, assembled from rescue-ladder steps that can be switched on one at a time.

Each ladder configuration is measured on its own (the ablation); steps are cumulative:
- S1 structure-aware chunks / S2 table-aware chunks: a different index (collection);
- S3 hybrid retrieval: BM25 + dense, fused with reciprocal rank fusion;
- S4 query understanding: per-company retrieval restricted to the relevant filings;
- S8 grounded answers: citations, numeric grounding check, abstain path (agent/grounded.py).
The answer step is unchanged from v0 until the grounding step (S8), so retrieval changes are
measured in isolation. Later steps add fields to LadderConfig.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
from qdrant_client import models as qm

from rag_eval.adapters import Context, Response
from rescue_rag import llm
from rescue_rag.agent import grounded
from rescue_rag.baseline.v0 import PROMPT as V0_PROMPT
from rescue_rag.config import load_yaml
from rescue_rag.embed import PRICE_PER_M_TOKENS, embed
from rescue_rag.ingest.chunk import Chunk
from rescue_rag.ingest.index import dense_search
from rescue_rag.retrieval.hybrid import rrf
from rescue_rag.retrieval.query import allowed_years, understand
from rescue_rag.retrieval.rerank import rerank, rerank_cost
from rescue_rag.retrieval.sparse import sparse_index


@dataclass(frozen=True)
class LadderConfig:
    name: str
    collection: str
    k: int
    model_role: str = "small_model"  # cost rescue: the small model carries the traffic
    hybrid: bool = False  # S3
    filters: bool = False  # S4
    grounded: bool = False  # S8
    rerank: str | None = None  # S5: Voyage rerank model name
    calculator: bool = False  # S7
    candidates: int = 30  # per retriever, before fusion
    extra: dict = field(default_factory=dict)


# Context budget is held near v0's (top-5 x 1,000 tokens): structured chunks are ~400 tokens.
LADDER = {
    "s1": LadderConfig("s1", "s1_struct", k=10),
    "s2": LadderConfig("s2", "s2_tables", k=10),
    "s3": LadderConfig("s3", "s2_tables", k=10, hybrid=True),
    "s4": LadderConfig("s4", "s2_tables", k=10, hybrid=True, filters=True),
    # S4 without S3 (hybrid hurt evidence recall on dev): isolates the filter effect
    "s4-dense": LadderConfig("s4-dense", "s2_tables", k=10, filters=True),
    "s8": LadderConfig("s8", "s2_tables", k=10, filters=True, grounded=True),
    "s7": LadderConfig("s7", "s2_tables", k=10, filters=True, grounded=True, calculator=True),
    # S5 measured on top of S8: 20 dense candidates per company, reranked to k
    "s5": LadderConfig(
        "s5",
        "s2_tables",
        k=10,
        filters=True,
        grounded=True,
        rerank="rerank-2.5-lite",
        candidates=20,
    ),
}


def _filter(ticker: str | None, fys: set[int] | None) -> qm.Filter | None:
    must: list[qm.Condition] = []
    if ticker:
        must.append(qm.FieldCondition(key="ticker", match=qm.MatchValue(value=ticker)))
    if fys:
        must.append(qm.FieldCondition(key="fy", match=qm.MatchAny(any=sorted(fys))))
    return qm.Filter(must=must) if must else None


class RescuePipeline:
    def __init__(self, config: LadderConfig) -> None:
        models = load_yaml("models.yaml")
        self.config = config
        self.name = config.name
        self.embedding_model = models["embedding_model"]
        self.model = models[config.model_role]
        self.small_model = models["small_model"]

    def _retrieve(
        self, question: str, qvec: np.ndarray, ticker: str | None, fys: set[int] | None, k: int
    ) -> tuple[list[tuple[Chunk, float]], int, float]:
        """Hits, plus rerank tokens and rerank latency (0 without S5). Thread-safe: no state."""
        cfg = self.config
        n = cfg.candidates if (cfg.hybrid or cfg.rerank) else k
        dense = dense_search(cfg.collection, qvec, n, _filter(ticker, fys))
        if cfg.hybrid:
            sparse_idx = sparse_index(cfg.collection)
            sparse = sparse_idx.search(
                question, n, sparse_idx.mask({ticker} if ticker else None, fys)
            )
            pool = rrf([dense, sparse], n)
        else:
            pool = dense
        if cfg.rerank:
            return rerank(question, [c for c, _ in pool], k, cfg.rerank)
        return pool[:k], 0, 0.0

    def __call__(self, question: str) -> Response:
        cfg = self.config
        start = time.perf_counter()
        meta: dict = {}
        cost = 0.0
        rr_tokens, rr_latency, understand_s = 0, 0.0, 0.0
        qvec, q_tokens = embed([question], model=self.embedding_model, input_type="query")

        if cfg.filters:
            # per-call cost/latency (the global ledger mixes concurrent questions)
            plan, call = understand(question, self.small_model)
            cost += call.cost_usd
            understand_s = call.latency_s
            meta["plan"] = plan.model_dump()
            if not plan.companies:
                if plan.mentions_other_companies:
                    hits: list[tuple[Chunk, float]] = []
                else:
                    hits, rr_tokens, rr_latency = self._retrieve(
                        question, qvec[0], None, None, cfg.k
                    )
            else:
                # one or two companies: full k each (comparisons need both statements)
                n_co = len(plan.companies)
                per = cfg.k if n_co <= 2 else max(4, 2 * cfg.k // n_co)
                hits = []
                for t in plan.companies:
                    fys = allowed_years(t, plan.fiscal_years)
                    if fys is not None and not fys:
                        continue  # no filing covers the requested year(s)
                    found, tok, lat = self._retrieve(question, qvec[0], t, fys, per)
                    hits += found
                    rr_tokens, rr_latency = rr_tokens + tok, rr_latency + lat
        else:
            hits, rr_tokens, rr_latency = self._retrieve(question, qvec[0], None, None, cfg.k)
        # reranking: count the original API latency even when the result came from cache
        retrieval_s = time.perf_counter() - start + rr_latency + understand_s
        if cfg.rerank:
            cost += rerank_cost(rr_tokens, cfg.rerank)
            meta["rerank_tokens"] = rr_tokens

        embed_cost = max(q_tokens, len(question) // 3) * PRICE_PER_M_TOKENS / 1e6
        contexts = [Context(c.chunk_id, c.text, c.accession) for c, _ in hits]

        if cfg.grounded:
            g = grounded.answer(
                question, [c for c, _ in hits], self.model, calculator=cfg.calculator
            )
            return Response(
                answer=g.text,
                contexts=contexts,
                citations=g.citations,
                cost_usd=(g.call.cost_usd if g.call else 0.0) + embed_cost + cost,
                latency_s=retrieval_s + (g.call.latency_s if g.call else 0.0),
                meta={"status": g.status, "guardrail": g.guardrail, **meta},
            )

        context = "\n\n".join(chunk.text for chunk, _ in hits)
        out = llm.generate(self.model, V0_PROMPT.format(context=context, question=question))
        return Response(
            answer=out.text,
            contexts=contexts,
            cost_usd=out.cost_usd + embed_cost + cost,
            latency_s=retrieval_s + out.latency_s,
            meta={"model": out.model, "usage": out.usage, "cached": out.cached, **meta},
        )
