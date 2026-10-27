"""Voyage AI embeddings with batching, retries and an on-disk cache keyed by text hash.

The cache means every distinct chunk is embedded once, however many chunking variants or
index rebuilds the ablation needs.
"""

from __future__ import annotations

import hashlib
import sqlite3
import threading
import time
from collections.abc import Callable
from functools import cache
from typing import Literal

import numpy as np
import voyageai
import voyageai.error

from rescue_rag.config import get_env, project_path

InputType = Literal["document", "query"]
MAX_BATCH_TEXTS = 128
MAX_BATCH_TOKENS = 100_000  # stays well under Voyage's per-request token limit
PRICE_PER_M_TOKENS = 0.06  # voyage-3.5 list price after the free tier, used for cost reporting


@cache
def _client() -> voyageai.Client:
    key = get_env().voyage_api_key
    if not key:
        raise RuntimeError("VOYAGE_API_KEY is not set in .env")
    return voyageai.Client(api_key=key, max_retries=3)


class EmbeddingCache:
    """SQLite store: (model, input_type, sha256(text)) -> float32 vector."""

    def __init__(self) -> None:
        path = project_path("data/cache/embeddings.sqlite")
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.execute("CREATE TABLE IF NOT EXISTS emb (key TEXT PRIMARY KEY, vec BLOB NOT NULL)")
        self._lock = threading.Lock()

    @staticmethod
    def key(model: str, input_type: str, text: str) -> str:
        return hashlib.sha256(f"{model}|{input_type}|{text}".encode()).hexdigest()

    def get_many(self, keys: list[str]) -> dict[str, np.ndarray]:
        out: dict[str, np.ndarray] = {}
        with self._lock:
            for i in range(0, len(keys), 500):
                part = keys[i : i + 500]
                q = f"SELECT key, vec FROM emb WHERE key IN ({','.join('?' * len(part))})"
                for k, blob in self._db.execute(q, part):
                    out[k] = np.frombuffer(blob, dtype=np.float32)
        return out

    def put_many(self, items: dict[str, np.ndarray]) -> None:
        with self._lock:
            self._db.executemany(
                "INSERT OR REPLACE INTO emb VALUES (?, ?)",
                [(k, v.astype(np.float32).tobytes()) for k, v in items.items()],
            )
            self._db.commit()


@cache
def _cache() -> EmbeddingCache:
    return EmbeddingCache()


def _batches(texts: list[str], token_counts: list[int]) -> list[list[int]]:
    batches: list[list[int]] = []
    current: list[int] = []
    tokens = 0
    for i, n in enumerate(token_counts):
        if current and (len(current) >= MAX_BATCH_TEXTS or tokens + n > MAX_BATCH_TOKENS):
            batches.append(current)
            current, tokens = [], 0
        current.append(i)
        tokens += n
    if current:
        batches.append(current)
    return batches


def embed(
    texts: list[str],
    *,
    model: str,
    input_type: InputType,
    token_counts: list[int] | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> tuple[np.ndarray, int]:
    """Embeddings for texts (cached), plus the number of tokens actually sent to the API."""
    store = _cache()
    keys = [EmbeddingCache.key(model, input_type, t) for t in texts]
    found = store.get_many(keys)
    missing = [i for i, k in enumerate(keys) if k not in found]
    billed = 0
    if missing:
        counts = token_counts or [len(t) // 3 for t in texts]
        sub_counts = [counts[i] for i in missing]
        done = 0
        for batch in _batches([texts[i] for i in missing], sub_counts):
            idx = [missing[j] for j in batch]
            result = _embed_with_backoff([texts[i] for i in idx], model, input_type)
            billed += result.total_tokens
            new = {
                keys[i]: np.asarray(v, dtype=np.float32)
                for i, v in zip(idx, result.embeddings, strict=True)
            }
            store.put_many(new)
            found.update(new)
            done += len(idx)
            if progress:
                progress(done, len(missing))
    return np.stack([found[k] for k in keys]), billed


def _embed_with_backoff(texts: list[str], model: str, input_type: InputType):  # type: ignore[no-untyped-def]
    delay = 20.0
    for attempt in range(8):
        try:
            return _client().embed(texts, model=model, input_type=input_type, truncation=True)
        except voyageai.error.RateLimitError:
            if attempt == 7:
                raise
            time.sleep(delay)
            delay = min(delay * 1.5, 120)
    raise AssertionError("unreachable")
