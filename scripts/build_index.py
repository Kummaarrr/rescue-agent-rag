"""Chunk the corpus and build a vector index.

uv run python scripts/build_index.py --variant v0
"""

from __future__ import annotations

import argparse
import sys
import time

from tqdm import tqdm

from rescue_rag.config import get_corpus, get_settings, load_yaml
from rescue_rag.corpus import filing_text, load_manifest
from rescue_rag.embed import PRICE_PER_M_TOKENS
from rescue_rag.ingest.blocks import blocks_to_text, html_to_blocks
from rescue_rag.ingest.chunk import Chunk, naive_chunks, structured_chunks
from rescue_rag.ingest.index import build_index
from rescue_rag.ingest.parse_html import split_items

COLLECTIONS = {"v0": "v0_naive", "s1": "s1_struct", "s2": "s2_tables"}


def v0_chunks() -> list[Chunk]:
    cfg = get_settings()["baseline"]
    chunks: list[Chunk] = []
    for f in load_manifest():
        chunks += naive_chunks(
            filing_text(f),
            size=cfg["chunk_tokens"],
            overlap=cfg["chunk_overlap"],
            ticker=f.ticker,
            fy=f.fy,
            accession=f.accession,
        )
    return chunks


def structured(variant: str) -> list[Chunk]:
    """S1: Item-aware paragraph chunks with context headers, tables flattened as in v0.
    S2: the same, with tables as markdown rows (own chunks, header rows repeated)."""
    names = {c.ticker: c.name for c in get_corpus().companies}
    tables = "markdown" if variant == "s2" else "flat"
    chunks: list[Chunk] = []
    for f in tqdm(load_manifest(), desc=f"chunking {variant}", unit="filing"):
        text = blocks_to_text(html_to_blocks(f.path.read_bytes()), tables=tables)
        chunks += structured_chunks(
            text,
            split_items(text),
            company=names[f.ticker],
            ticker=f.ticker,
            fy=f.fy,
            accession=f.accession,
            variant=variant,
        )
    return chunks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=sorted(COLLECTIONS), default="v0")
    args = parser.parse_args()

    t = time.time()
    chunks = v0_chunks() if args.variant == "v0" else structured(args.variant)
    model = load_yaml("models.yaml")["embedding_model"]
    print(f"{len(chunks):,} chunks -> collection {COLLECTIONS[args.variant]} ({model})")
    bar = tqdm(total=len(chunks), unit="chunk")

    def progress(done: int, total: int) -> None:
        bar.total = total
        bar.n = done
        bar.refresh()

    billed = build_index(COLLECTIONS[args.variant], chunks, model, progress=progress)
    bar.close()
    print(
        f"Done in {time.time() - t:.0f}s. Embedding tokens billed: {billed:,} "
        f"(list price ${billed * PRICE_PER_M_TOKENS / 1e6:.2f}; covered by the free tier)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
