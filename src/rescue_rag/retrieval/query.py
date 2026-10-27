"""Query understanding and metadata filters (rescue step S4).

A small-model call extracts which corpus companies and fiscal years a question is about.
Retrieval then runs once per company, restricted to the filings that can hold the answer:
- the filing for each requested fiscal year, plus the next one (10-Ks repeat the prior year
  as comparatives, so FY2024 figures also appear in the FY2025 10-K);
- a requested year that no corpus filing covers (e.g. FY2029, FY2014) leaves that company
  with no chunks at all, so the answer step sees no misleading context;
- a question only about companies outside the corpus retrieves nothing.
The first two fix the main v0 failure modes: comparisons that retrieve only one company, and
answers taken from the wrong year's filing.
"""

from __future__ import annotations

from collections import defaultdict
from functools import cache

from pydantic import BaseModel, Field

from rescue_rag import llm
from rescue_rag.config import get_corpus
from rescue_rag.corpus import load_manifest


class QueryPlan(BaseModel):
    companies: list[str] = Field(description="Tickers of corpus companies the question is about")
    fiscal_years: list[int] = Field(
        description="Fiscal years the question asks about, as written (e.g. 2025 for "
        "'fiscal year 2025'); empty if none is stated"
    )
    mentions_other_companies: bool = Field(
        description="True if it asks about a company that is not in the list"
    )


PROMPT = """Extract retrieval filters from a question about companies' 10-K annual reports.

Companies available (ticker: name):
{companies}

Question: {question}

Return the tickers of the listed companies the question is about, the fiscal years it asks
about (as stated; include every year in a range or comparison), and whether it asks about any
company that is not in the list."""


@cache
def _company_list() -> str:
    return "\n".join(f"{c.ticker}: {c.name}" for c in get_corpus().companies)


@cache
def available_years() -> dict[str, set[int]]:
    years: dict[str, set[int]] = defaultdict(set)
    for f in load_manifest():
        years[f.ticker].add(f.fy)
    return dict(years)


def understand(
    question: str, model: str, api_key: str | None = None
) -> tuple[QueryPlan, llm.CallInfo]:
    plan, call = llm.parse_full(
        model,
        PROMPT.format(companies=_company_list(), question=question),
        QueryPlan,
        effort="low",
        max_tokens=1000,
        api_key=api_key,
    )
    known = {c.ticker for c in get_corpus().companies}
    plan.companies = [t for t in dict.fromkeys(plan.companies) if t in known]
    return plan, call


def allowed_years(ticker: str, requested: list[int]) -> set[int] | None:
    """Fiscal years of this company's filings to search. None = no year filter;
    an empty set = no filing can answer (the company gets no chunks)."""
    if not requested:
        return None
    have = available_years().get(ticker, set())
    # each requested year's own filing, and the next one (it repeats that year as comparatives)
    return {y for r in requested for y in (r, r + 1) if y in have}
