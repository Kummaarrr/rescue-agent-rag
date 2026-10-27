"""Block-level 10-K parsing for v1 (rescue steps S1/S2).

v0 uses html_to_text(): one line per HTML text node, so sentences break wherever a <span> ends
and tables become one cell per line. Here the document is walked into blocks instead:
- paragraphs: the text of a leaf block element (p/div/li/h*), joined with spaces;
- tables: rows of non-empty cells, with "$", "%" and ")" cells merged into their neighbours.
  Layout tables (at most one non-empty cell per row) are treated as paragraphs.
Blocks are joined with blank lines, so Item segmentation (parse_html.split_items) still works.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from bs4 import BeautifulSoup, NavigableString, Tag

from rescue_rag.ingest.parse_html import HIDDEN_STYLE_RE, decode_html

BLOCK_TAGS = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table", "ul", "ol", "br"}
_WS = re.compile(r"\s+")


@dataclass(frozen=True)
class Block:
    kind: str  # "para" | "table"
    text: str  # paragraph text, or for tables: not used (see rows)
    rows: tuple[tuple[str, ...], ...] = ()


def _clean(s: str) -> str:
    return _WS.sub(" ", s.replace("\xa0", " ").replace("​", "")).strip()


def _tidy_cell(c: str) -> str:
    """'( 321 )' -> '(321)', '$ 1,234' -> '$1,234'."""
    return c.replace("( ", "(").replace(" )", ")").replace("$ ", "$")


def _table_rows(table: Tag) -> list[list[str]]:
    rows = []
    for tr in table.find_all("tr"):
        cells = [_tidy_cell(_clean(td.get_text(" "))) for td in tr.find_all(["td", "th"])]
        merged: list[str] = []
        for c in cells:
            if not c:
                continue
            if c in ("$", "(", "($") and merged is not None:
                merged.append(c)  # prefix: attach to the next cell below
                continue
            if c in ("%", ")", ")%", "%)") and merged:
                merged[-1] += c
                continue
            if merged and merged[-1] in ("$", "(", "($"):
                merged[-1] = (merged[-1] + c).replace("$ ", "$")
                continue
            merged.append(c)
        if merged:
            rows.append(merged)
    return rows


def _walk(node: Tag, out: list[Block]) -> None:
    inline: list[str] = []

    def flush() -> None:
        text = _clean(" ".join(inline))
        if text:
            out.append(Block("para", text))
        inline.clear()

    for child in node.children:
        if isinstance(child, NavigableString):
            inline.append(str(child))
            continue
        if not isinstance(child, Tag):
            continue
        if child.name == "table":
            flush()
            rows = _table_rows(child)
            if not rows:
                continue
            if max(len(r) for r in rows) <= 1:  # layout table: really paragraphs
                for r in rows:
                    out.append(Block("para", r[0]))
            else:
                out.append(Block("table", "", tuple(tuple(r) for r in rows)))
        elif child.name in BLOCK_TAGS:
            flush()
            if child.find(BLOCK_TAGS):
                _walk(child, out)
            else:
                text = _clean(child.get_text(" "))
                if text:
                    out.append(Block("para", text))
        else:
            inline.append(child.get_text(" "))
    flush()


def html_to_blocks(html: bytes | str) -> list[Block]:
    if isinstance(html, bytes):
        html = decode_html(html)
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()
    for tag in soup.find_all(style=HIDDEN_STYLE_RE):
        tag.decompose()
    out: list[Block] = []
    _walk(soup.body or soup, out)
    return out


def table_markdown(rows: tuple[tuple[str, ...], ...]) -> str:
    return "\n".join("| " + " | ".join(r) + " |" for r in rows)


def table_flat(rows: tuple[tuple[str, ...], ...]) -> str:
    """S1-only rendering: v0-style flattening (one cell per line), to isolate S2's effect."""
    return "\n".join(c for r in rows for c in r)


def blocks_to_text(blocks: list[Block], tables: str = "markdown") -> str:
    render = table_markdown if tables == "markdown" else table_flat
    return "\n\n".join(b.text if b.kind == "para" else render(b.rows) for b in blocks)
