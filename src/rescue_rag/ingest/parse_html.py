"""10-K HTML to text, and segmentation into Items (1, 1A, 7, 8, ...).

10-K filings are inline-XBRL HTML. Hidden XBRL header blocks are removed before extracting text.
Every Item heading appears twice: in the table of contents and at the start of the real section.
TOC entries are recognised as dense clusters of headings and dropped; of the remaining headings
we keep the longest run that follows the standard Item order (drops stray cross-references).
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass
from itertools import pairwise

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

ITEM_ORDER = [
    "1", "1A", "1B", "1C", "2", "3", "4", "5", "6", "7", "7A", "8",
    "9", "9A", "9B", "9C", "10", "11", "12", "13", "14", "15", "16",
]  # fmt: skip

# "Item 7." / "ITEM 1A:" / "Item 12\n." at the start of a line, optionally followed by a title.
# Headings often run into the section's first sentence on the same line, so no end-of-line anchor.
# The separator class allows ".", ":", em dash, en dash and hyphen. A leading "|" (and "|"
# separators) allow headings laid out as table cells ("| Item 1. | Business |", AMZN/WMT) in
# the block-level text; the TOC filter still drops table-of-contents rows.
ITEM_RE = re.compile(
    r"(?im)^[ \t|]*item[ \t]+(\d{1,2}[ABC]?)\b[ \t]*\n?[ \t]*"
    "[.:" + chr(0x2014) + chr(0x2013) + "-]?"
    r"[ \t|]*([^\n]{0,120})"
)
HIDDEN_STYLE_RE = re.compile(r"display:\s*none", re.I)


@dataclass(frozen=True)
class Section:
    item: str
    title: str
    start: int
    end: int
    text: str


def decode_html(raw: bytes) -> str:
    """Filings are UTF-8 or Windows-1252; decode explicitly instead of letting the parser guess."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def html_to_text(html: bytes | str) -> str:
    if isinstance(html, bytes):
        html = decode_html(html)
    soup = BeautifulSoup(html, "lxml")
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()
    for tag in soup.find_all(style=HIDDEN_STYLE_RE):
        tag.decompose()
    text = soup.get_text("\n")
    text = text.replace("\xa0", " ").replace("​", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n[ \n]*", "\n", text)
    return text.strip()


def _candidates(text: str) -> list[tuple[str, int, str]]:
    out = []
    for m in ITEM_RE.finditer(text):
        item = m.group(1).upper()
        if item in ITEM_ORDER:
            out.append((item, m.start(), m.group(2).strip()))
    return out


# A table of contents lists many Items within a short span; real sections are far apart.
TOC_WINDOW_CHARS = 3000
TOC_MIN_ITEMS = 8
TOC_MAX_GAP = 2500  # a TOC entry is close to the next heading; a real section heading usually isn't


def _drop_toc(cands: list[tuple[str, int, str]]) -> list[tuple[str, int, str]]:
    gaps = [b[1] - a[1] for a, b in pairwise(cands)] + [10**9]
    in_toc = [False] * len(cands)
    for i, (_, pos, _) in enumerate(cands):
        j = i
        while j < len(cands) and cands[j][1] - pos <= TOC_WINDOW_CHARS:
            j += 1
        if len({c[0] for c in cands[i:j]}) >= TOC_MIN_ITEMS:
            for k in range(i, j):
                if gaps[k] < TOC_MAX_GAP:
                    in_toc[k] = True
    return [c for c, toc in zip(cands, in_toc, strict=True) if not toc]


def _longest_ordered_run(cands: list[tuple[str, int, str]]) -> list[tuple[str, int, str]]:
    """Longest subsequence (in document order) whose Items strictly follow ITEM_ORDER."""
    if not cands:
        return []
    rank = [ITEM_ORDER.index(c[0]) for c in cands]
    best_len = [1] * len(cands)
    prev = [-1] * len(cands)
    for i in range(len(cands)):
        for j in range(i):
            if rank[j] < rank[i] and best_len[j] + 1 > best_len[i]:
                best_len[i], prev[i] = best_len[j] + 1, j
    i = max(range(len(cands)), key=lambda k: best_len[k])
    run = []
    while i != -1:
        run.append(cands[i])
        i = prev[i]
    return run[::-1]


def split_items(text: str) -> list[Section]:
    """Split a 10-K's text into Item sections. Returns [] if no Item headings are found."""
    ordered = _longest_ordered_run(_drop_toc(_candidates(text)))
    sections = []
    for i, (item, pos, title) in enumerate(ordered):
        end = ordered[i + 1][1] if i + 1 < len(ordered) else len(text)
        sections.append(Section(item, title, pos, end, text[pos:end]))
    return sections
