"""XBRL companyfacts: fetch and fact-matching rules.

Rules (docs/PROJECT_PLAN.md, section 5.1):
- only facts from 10-K filings in the corpus (matched by accession number);
- flow items (income/cash-flow) need a ~1-year duration; balance items are point-in-time;
- the value is taken as reported in that filing (later restatements are ignored);
- fiscal year is the company's own fiscal year.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Any

COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

# Duration window (days) accepted as "one fiscal year" for flow items (52/53-week years included).
ANNUAL_MIN_DAYS = 350
ANNUAL_MAX_DAYS = 380


@dataclass(frozen=True)
class Fact:
    concept: str
    value: float
    unit: str
    accession: str
    fy: int | None
    fp: str | None
    form: str
    start: str | None
    end: str


def iter_facts(companyfacts: dict[str, Any], taxonomy: str = "us-gaap"):
    for concept, body in companyfacts.get("facts", {}).get(taxonomy, {}).items():
        for unit, rows in body.get("units", {}).items():
            for r in rows:
                yield Fact(
                    concept=concept,
                    value=r["val"],
                    unit=unit,
                    accession=r["accn"],
                    fy=r.get("fy"),
                    fp=r.get("fp"),
                    form=r.get("form", ""),
                    start=r.get("start"),
                    end=r["end"],
                )


def duration_days(fact: Fact) -> int | None:
    if fact.start is None:
        return None
    return (date.fromisoformat(fact.end) - date.fromisoformat(fact.start)).days


def is_annual(fact: Fact) -> bool:
    days = duration_days(fact)
    return days is not None and ANNUAL_MIN_DAYS <= days <= ANNUAL_MAX_DAYS


def filing_fiscal_year(companyfacts: dict[str, Any], accession: str) -> int | None:
    """Fiscal year a filing reports on: the most common `fy` among its 10-K facts."""
    years = Counter(
        f.fy
        for f in iter_facts(companyfacts)
        if f.accession == accession and f.form == "10-K" and f.fy is not None
    )
    return years.most_common(1)[0][0] if years else None


def match_fact(
    companyfacts: dict[str, Any],
    concepts: list[str],
    accession: str,
    period_end: str,
    flow: bool,
    unit: str = "USD",
) -> Fact | None:
    """Value for the filing's own fiscal period, trying concepts in order (fallbacks)."""
    for concept in concepts:
        for f in iter_facts(companyfacts):
            if f.concept != concept or f.unit != unit:
                continue
            if f.accession != accession or f.form != "10-K" or f.end != period_end:
                continue
            if flow and not is_annual(f):
                continue
            if not flow and f.start is not None:
                continue
            return f
    return None
