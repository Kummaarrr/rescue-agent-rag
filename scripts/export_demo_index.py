"""Export a Qdrant collection to vectors.npy + chunks.jsonl for the public demo.

uv run python scripts/export_demo_index.py --collection s2_tables --out app/index
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

from rescue_rag.ingest.chunk import Chunk
from rescue_rag.ingest.index import _lock, qdrant


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection", default="s2_tables")
    parser.add_argument("--out", type=Path, default=Path("app/index"))
    args = parser.parse_args()

    vectors, chunks, offset = [], [], None
    while True:
        with _lock:
            points, offset = qdrant().scroll(
                args.collection, limit=512, offset=offset, with_payload=True, with_vectors=True
            )
        for p in points:
            if p.payload and p.vector is not None:
                vectors.append(np.asarray(p.vector, dtype=np.float32))
                chunks.append(Chunk(**p.payload))
        if offset is None:
            break
    out = args.out / args.collection
    out.mkdir(parents=True, exist_ok=True)
    np.save(out / "vectors.npy", np.stack(vectors))
    with (out / "chunks.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for c in chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
    print(f"{len(chunks)} chunks -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
