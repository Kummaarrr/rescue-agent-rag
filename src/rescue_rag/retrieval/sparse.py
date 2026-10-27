"""BM25 keyword retrieval over a collection's chunks (rescue step S3).

Built once per collection from the chunks stored in Qdrant and saved under
data/processed/bm25/<collection>/. Dense embeddings can blur exact terms ("diluted earnings
per share", a segment or product name); BM25 matches them literally.
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict
from functools import cache

import bm25s
import numpy as np

from rescue_rag.config import project_path
from rescue_rag.ingest.chunk import Chunk
from rescue_rag.ingest.index import all_chunks

_lock = threading.Lock()


def _dir(collection: str):  # type: ignore[no-untyped-def]
    return project_path(f"data/processed/bm25/{collection}")


def build_bm25(collection: str) -> int:
    chunks = list(all_chunks(collection))
    retriever = bm25s.BM25()
    retriever.index(
        bm25s.tokenize([c.text for c in chunks], show_progress=False), show_progress=False
    )
    out = _dir(collection)
    out.mkdir(parents=True, exist_ok=True)
    retriever.save(str(out), show_progress=False)
    with (out / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
    return len(chunks)


class SparseIndex:
    def __init__(self, collection: str) -> None:
        d = _dir(collection)
        if not (d / "chunks.jsonl").exists():
            build_bm25(collection)  # one-off, ~1 minute for the full corpus
        self.retriever = bm25s.BM25.load(str(d), show_progress=False)
        with (d / "chunks.jsonl").open(encoding="utf-8") as f:
            self.chunks = [Chunk(**json.loads(line)) for line in f]

    def mask(self, tickers: set[str] | None, fys: set[int] | None) -> np.ndarray | None:
        """1.0 for chunks allowed by the (S4) metadata filter, else 0.0. None = no filter."""
        if not tickers and not fys:
            return None
        return np.array(
            [
                float((not tickers or c.ticker in tickers) and (not fys or c.fy in fys))
                for c in self.chunks
            ],
            dtype=np.float32,
        )

    def search(
        self, query: str, k: int, mask: np.ndarray | None = None
    ) -> list[tuple[Chunk, float]]:
        if mask is not None and not mask.any():
            return []
        tokens = bm25s.tokenize([query], show_progress=False)
        with _lock:
            ids, scores = self.retriever.retrieve(
                tokens, k=min(k, len(self.chunks)), show_progress=False, weight_mask=mask
            )
        return [
            (self.chunks[int(i)], float(s)) for i, s in zip(ids[0], scores[0], strict=True) if s > 0
        ]


@cache
def sparse_index(collection: str) -> SparseIndex:
    return SparseIndex(collection)
