"""Cross-encoder reranking via the Voyage rerank API (rescue step S5).

A cross-encoder reads the question and each candidate chunk together, so it judges relevance
better than comparing two independent embeddings. The plan's local cross-encoder would need
PyTorch (~1 GB) on a 2-core, 8 GB laptop; the hosted reranker is the same model class, runs
in well under a second and is covered by Voyage's free tokens.

Results are cached on disk (keyed by model, query and candidate chunk ids), like LLM calls.
"""

from __future__ import annotations

import hashlib
import json
import time
from functools import cache

import voyageai

from rescue_rag.config import get_env, project_path
from rescue_rag.ingest.chunk import Chunk

CACHE_DIR = project_path("data/cache/rerank")
# USD per 1M tokens, Voyage list prices (Oct 2026) - verify at https://docs.voyageai.com/docs/pricing
PRICES = {"rerank-2.5": 0.05, "rerank-2.5-lite": 0.02}


@cache
def _client() -> voyageai.Client:
    return voyageai.Client(api_key=get_env().voyage_api_key, max_retries=3)


def rerank(
    query: str, candidates: list[Chunk], k: int, model: str
) -> tuple[list[tuple[Chunk, float]], int, float]:
    """Top-k candidates by cross-encoder relevance, plus tokens billed and latency (s)."""
    if len(candidates) <= 1:
        return [(c, 1.0) for c in candidates], 0, 0.0
    key = hashlib.sha256(
        json.dumps([model, query, [c.chunk_id for c in candidates]]).encode()
    ).hexdigest()[:32]
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        rec = json.loads(path.read_text(encoding="utf-8"))
    else:
        start = time.perf_counter()
        r = _client().rerank(query, [c.text for c in candidates], model=model, top_k=k)
        rec = {
            "results": [[x.index, x.relevance_score] for x in r.results],
            "tokens": r.total_tokens,
            "latency_s": time.perf_counter() - start,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(rec), encoding="utf-8")
    ranked = [(candidates[i], float(s)) for i, s in rec["results"][:k]]
    return ranked, int(rec["tokens"]), float(rec["latency_s"])


def rerank_cost(tokens: int, model: str) -> float:
    return tokens * PRICES[model] / 1e6
