"""Chunkers. v0 is the deliberately naive "tutorial RAG" chunker; v1 chunkers come with S1/S2.

Token counts use tiktoken's cl100k_base as a provider-neutral proxy for chunk sizing. Billing is
taken from the APIs' own usage numbers, never from this count.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cache

import tiktoken


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str
    # Provenance is kept for scoring retrieval; the v0 pipeline itself never uses it.
    ticker: str
    fy: int
    accession: str
    item: str | None = None


@cache
def _encoder() -> tiktoken.Encoding:
    return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_encoder().encode(text, disallowed_special=()))


def naive_chunks(
    text: str, *, size: int, overlap: int, ticker: str, fy: int, accession: str
) -> list[Chunk]:
    """Fixed-size token windows with overlap, ignoring sections, sentences and tables."""
    if not 0 <= overlap < size:
        raise ValueError("need 0 <= overlap < size")
    enc = _encoder()
    tokens = enc.encode(text, disallowed_special=())
    step = size - overlap
    chunks = []
    for i, start in enumerate(range(0, max(len(tokens) - overlap, 1), step)):
        window = tokens[start : start + size]
        chunks.append(
            Chunk(
                chunk_id=f"{ticker}_FY{fy}_{i:05d}",
                text=enc.decode(window),
                ticker=ticker,
                fy=fy,
                accession=accession,
            )
        )
    return chunks


# --- v1 chunkers (rescue steps S1 and S2) ----------------------------------------------------

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")


def _is_heading(par: str) -> bool:
    """Short line without sentence punctuation, e.g. 'CONSOLIDATED BALANCE SHEETS'."""
    return len(par) <= 100 and not par.rstrip().endswith((".", ":", ";", ",")) and "|" not in par


def _split_long(par: str, limit: int) -> list[str]:
    """Split an over-long paragraph at sentence boundaries (or hard-wrap as a last resort)."""
    if count_tokens(par) <= limit:
        return [par]
    parts, current = [], ""
    for sent in _SENTENCE_END.split(par):
        candidate = f"{current} {sent}".strip()
        if current and count_tokens(candidate) > limit:
            parts.append(current)
            current = sent
        else:
            current = candidate
    if current:
        parts.append(current)
    out = []
    for p in parts:  # sentences longer than the limit (rare): token windows
        if count_tokens(p) > limit:
            enc = _encoder()
            toks = enc.encode(p, disallowed_special=())
            out += [enc.decode(toks[i : i + limit]) for i in range(0, len(toks), limit)]
        else:
            out.append(p)
    return out


def _table_groups(table: str, limit: int, header_rows: int = 2) -> list[str]:
    """Split a markdown table into row groups under `limit` tokens, repeating the header rows."""
    if count_tokens(table) <= limit:
        return [table]
    lines = table.split("\n")
    head, body = lines[:header_rows], lines[header_rows:]
    groups, current = [], list(head)
    for line in body:
        if len(current) > len(head) and count_tokens("\n".join([*current, line])) > limit:
            groups.append("\n".join(current))
            current = list(head)
        current.append(line)
    if len(current) > len(head):
        groups.append("\n".join(current))
    return groups


def structured_chunks(
    text: str,
    sections: list,  # list[parse_html.Section]; untyped here to avoid an import cycle
    *,
    company: str,
    ticker: str,
    fy: int,
    accession: str,
    variant: str,
    target: int = 500,
    table_limit: int = 800,
) -> list[Chunk]:
    """Chunks that never cross an Item, built from whole paragraphs and whole table rows.

    Each chunk starts with a context header ("Apple FY2025 Form 10-K | Item 8: Financial
    Statements | CONSOLIDATED STATEMENTS OF OPERATIONS") so the embedding knows the company,
    year, section and nearest heading even when the chunk text itself never names them.
    Markdown tables (lines starting with "|") become their own chunks.
    """
    spans = [(s.item, s.title, s.start, s.end) for s in sections]
    if not spans or spans[0][2] > 0:
        spans.insert(
            0, ("cover", "Cover page and front matter", 0, spans[0][2] if spans else len(text))
        )
    chunks: list[Chunk] = []

    def emit(item: str, title: str, heading: str, body: str) -> None:
        header = f"{company} FY{fy} Form 10-K | Item {item}: {title[:80]}"
        if heading and heading.lower() not in title.lower():
            header += f" | {heading[:100]}"
        chunks.append(
            Chunk(
                chunk_id=f"{ticker}_FY{fy}_{variant}_{len(chunks):05d}",
                text=f"{header}\n\n{body}",
                ticker=ticker,
                fy=fy,
                accession=accession,
                item=item,
            )
        )

    def section(item: str, title: str, body_text: str) -> None:
        heading = ""
        buffer: list[str] = []

        def flush() -> None:
            if buffer:
                emit(item, title, heading, "\n\n".join(buffer))
                buffer.clear()

        for par in (p.strip() for p in body_text.split("\n\n")):
            if not par:
                continue
            if par.startswith("|"):  # a table: its own chunk(s), headed by the last heading
                if all(_is_heading(b) for b in buffer):
                    buffer.clear()  # headings only: already in the table chunk's header line
                flush()
                for group in _table_groups(par, table_limit):
                    emit(item, title, heading, group)
                continue
            if _is_heading(par):
                # a heading starts a new chunk only once the current one is reasonably full
                if buffer and count_tokens("\n\n".join(buffer)) >= target // 2:
                    flush()
                heading = par
                buffer.append(par)
                continue
            for piece in _split_long(par, target):
                if buffer and count_tokens("\n\n".join([*buffer, piece])) > target:
                    flush()
                buffer.append(piece)
        flush()

    for item, title, start, end in spans:
        section(item, title, text[start:end])
    return chunks
