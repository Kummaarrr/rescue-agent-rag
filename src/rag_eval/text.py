"""Text normalisation shared by dataset building and scoring.

Evidence spans are stored normalised, and retrieved chunks are normalised the same way before
matching, so line breaks and quote styles from HTML extraction never cause false misses.
"""

from __future__ import annotations

import re

_QUOTES = str.maketrans(
    {chr(0x2019): "'", chr(0x2018): "'", chr(0x201C): '"', chr(0x201D): '"', chr(0xA0): " "}
)


def normalize(text: str) -> str:
    """Collapse whitespace, unify quotes, drop spaces before punctuation. Case is kept."""
    text = re.sub(r"\s+", " ", text.translate(_QUOTES))
    # only drop a space before punctuation that ends a token: keeps "corresponding .z ECCNs"
    text = re.sub(r" ([,.;:)%])(?=\s|$)", r"\1", text)
    text = re.sub(r"([($]) ", r"\1", text)
    return text.strip()


def contains(haystack: str, needle: str) -> bool:
    """Case-insensitive containment after normalisation."""
    return normalize(needle).lower() in normalize(haystack).lower()


def contains_number(haystack: str, number: str) -> bool:
    """'416,161' appears as a whole number (not inside '1,416,161' or '416,161.5')."""
    pattern = rf"(?<![\d,.]){re.escape(number)}(?![\d,]|\.\d)"
    return re.search(pattern, haystack) is not None
