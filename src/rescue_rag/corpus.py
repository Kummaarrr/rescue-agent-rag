"""The frozen corpus: manifest rows plus cached plain text, Item sections and XBRL facts."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

from rescue_rag.config import get_settings, project_path
from rescue_rag.ingest.parse_html import Section, html_to_text, split_items


@dataclass(frozen=True)
class CorpusFiling:
    ticker: str
    cik: int
    fy: int
    accession: str
    filing_date: str
    report_date: str
    path: Path

    @property
    def key(self) -> str:
        return f"{self.ticker}_FY{self.fy}"


def load_manifest() -> list[CorpusFiling]:
    path = project_path(get_settings()["paths"]["manifest"])
    with path.open(newline="", encoding="utf-8") as f:
        return [
            CorpusFiling(
                ticker=r["ticker"],
                cik=int(r["cik"]),
                fy=int(r["fy"]),
                accession=r["accession"],
                filing_date=r["filing_date"],
                report_date=r["report_date"],
                path=project_path(r["path"]),
            )
            for r in csv.DictReader(f)
        ]


def _text_cache(filing: CorpusFiling) -> Path:
    return project_path(get_settings()["paths"]["processed"]) / "text" / f"{filing.key}.txt"


def filing_text(filing: CorpusFiling) -> str:
    """Plain text of a filing, cached under data/processed/text/."""
    cache_path = _text_cache(filing)
    if cache_path.exists() and cache_path.stat().st_mtime >= filing.path.stat().st_mtime:
        return cache_path.read_text(encoding="utf-8")
    text = html_to_text(filing.path.read_bytes())
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(text, encoding="utf-8")
    return text


def filing_sections(filing: CorpusFiling) -> list[Section]:
    return split_items(filing_text(filing))


@cache
def company_facts(ticker: str) -> dict[str, Any]:
    path = project_path(get_settings()["paths"]["xbrl"]) / f"{ticker}.json"
    with path.open(encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data
