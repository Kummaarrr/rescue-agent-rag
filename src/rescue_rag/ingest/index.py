"""Build and query vector indexes (Qdrant; embedded local mode unless QDRANT_URL is set).

One collection per chunking variant (e.g. "v0_naive"), so ablation steps don't overwrite each
other. Chunk text and provenance are stored as payload; provenance is used for scoring, and
only pipelines that enable metadata filters (S4) use it for retrieval.
"""

from __future__ import annotations

import atexit
import json
import os
import threading
import uuid
from collections.abc import Iterable
from dataclasses import asdict
from functools import cache
from pathlib import Path

import numpy as np
from qdrant_client import QdrantClient, models

from rescue_rag.config import get_env, project_path
from rescue_rag.embed import embed
from rescue_rag.ingest.chunk import Chunk, count_tokens

_lock = threading.Lock()  # embedded Qdrant is not safe for concurrent writers/readers


@cache
def qdrant() -> QdrantClient:
    env = get_env()
    if env.qdrant_url:
        client = QdrantClient(url=env.qdrant_url)
    else:
        client = QdrantClient(path=str(project_path(env.qdrant_path)))
    atexit.register(client.close)  # avoids a noisy close during interpreter shutdown
    return client


def _point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def build_index(collection: str, chunks: list[Chunk], model: str, progress=None) -> int:  # type: ignore[no-untyped-def]
    """(Re)create a collection from chunks. Returns embedding tokens billed (0 if all cached)."""
    vectors, billed = embed(
        [c.text for c in chunks],
        model=model,
        input_type="document",
        token_counts=[count_tokens(c.text) for c in chunks],
        progress=progress,
    )
    client = qdrant()
    with _lock:
        if client.collection_exists(collection):
            client.delete_collection(collection)
        client.create_collection(
            collection,
            vectors_config=models.VectorParams(
                size=vectors.shape[1], distance=models.Distance.COSINE
            ),
        )
        for start in range(0, len(chunks), 256):
            part = chunks[start : start + 256]
            client.upsert(
                collection,
                points=[
                    models.PointStruct(
                        id=_point_id(c.chunk_id), vector=v.tolist(), payload=asdict(c)
                    )
                    for c, v in zip(part, vectors[start : start + 256], strict=True)
                ],
            )
    return billed


class NumpyIndex:
    """Exact cosine search over an exported collection (the public demo ships this instead of
    Qdrant's storage: ~11K vectors, same results as Qdrant's exact search in local mode)."""

    def __init__(self, directory: Path) -> None:
        vectors = np.load(directory / "vectors.npy").astype(np.float32)
        self.vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        with (directory / "chunks.jsonl").open(encoding="utf-8") as f:
            self.chunks = [Chunk(**json.loads(line)) for line in f]
        self.tickers = np.array([c.ticker for c in self.chunks])
        self.fys = np.array([c.fy for c in self.chunks])

    def search(
        self, query_vector: np.ndarray, k: int, flt: models.Filter | None
    ) -> list[tuple[Chunk, float]]:
        mask = np.ones(len(self.chunks), dtype=bool)
        for cond in (flt.must or []) if flt else []:  # the two filters the pipeline uses
            assert isinstance(cond, models.FieldCondition)
            if cond.key == "ticker" and isinstance(cond.match, models.MatchValue):
                mask &= self.tickers == cond.match.value
            elif cond.key == "fy" and isinstance(cond.match, models.MatchAny):
                mask &= np.isin(self.fys, [int(y) for y in cond.match.any])  # type: ignore[arg-type]
            else:
                raise NotImplementedError(f"filter on {cond.key}")
        q = query_vector / np.linalg.norm(query_vector)
        scores = np.where(mask, self.vectors @ q, -np.inf)
        top = np.argsort(-scores)[:k]
        return [(self.chunks[i], float(scores[i])) for i in top if np.isfinite(scores[i])]


@cache
def numpy_index(collection: str) -> NumpyIndex:
    return NumpyIndex(Path(os.environ["RESCUE_RAG_INDEX_DIR"]) / collection)


def dense_search(
    collection: str, query_vector: np.ndarray, k: int, flt: models.Filter | None = None
) -> list[tuple[Chunk, float]]:
    if os.environ.get("RESCUE_RAG_INDEX_DIR"):  # demo / deployment: exported NumPy index
        return numpy_index(collection).search(query_vector, k, flt)
    with _lock:
        hits = (
            qdrant()
            .query_points(
                collection,
                query=query_vector.tolist(),
                limit=k,
                query_filter=flt,
                with_payload=True,
            )
            .points
        )
    return [(Chunk(**h.payload), float(h.score)) for h in hits if h.payload]


def all_chunks(collection: str) -> Iterable[Chunk]:
    offset = None
    while True:
        with _lock:
            points, offset = qdrant().scroll(
                collection, limit=512, offset=offset, with_payload=True
            )
        for p in points:
            if p.payload:
                yield Chunk(**p.payload)
        if offset is None:
            break
