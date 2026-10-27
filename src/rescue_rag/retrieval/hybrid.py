"""Reciprocal rank fusion of ranked result lists (rescue step S3).

RRF scores each chunk by sum(1 / (k + rank)) over the lists it appears in. It needs no score
calibration between BM25 and cosine similarity, which live on unrelated scales.
"""

from __future__ import annotations

from rescue_rag.ingest.chunk import Chunk

RRF_K = 60  # the constant from Cormack et al. (2009); dampens the weight of top ranks


def rrf(result_lists: list[list[tuple[Chunk, float]]], k: int) -> list[tuple[Chunk, float]]:
    scores: dict[str, float] = {}
    by_id: dict[str, Chunk] = {}
    for results in result_lists:
        for rank, (chunk, _) in enumerate(results, start=1):
            scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1.0 / (RRF_K + rank)
            by_id[chunk.chunk_id] = chunk
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:k]
    return [(by_id[cid], score) for cid, score in ranked]
