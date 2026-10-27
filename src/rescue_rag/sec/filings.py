"""Find the latest 10-K filings for a company via the SEC submissions API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rescue_rag.sec.client import SecClient

TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
SUBMISSIONS_PAGE_URL = "https://data.sec.gov/submissions/{name}"
ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accn_nodash}/{document}"


@dataclass(frozen=True)
class Filing:
    ticker: str
    cik: int
    form: str
    accession: str
    filing_date: str  # YYYY-MM-DD
    report_date: str  # period end, YYYY-MM-DD
    primary_document: str

    @property
    def url(self) -> str:
        return ARCHIVE_URL.format(
            cik=self.cik,
            accn_nodash=self.accession.replace("-", ""),
            document=self.primary_document,
        )


def resolve_ciks(ticker_map: dict[str, Any], tickers: list[str]) -> dict[str, int]:
    """Map tickers to CIKs using the SEC company_tickers.json payload."""
    by_ticker = {row["ticker"].upper(): int(row["cik_str"]) for row in ticker_map.values()}
    missing = [t for t in tickers if t.upper() not in by_ticker]
    if missing:
        raise KeyError(f"Tickers not in SEC ticker map: {missing}")
    return {t: by_ticker[t.upper()] for t in tickers}


def filings_from_table(ticker: str, cik: int, table: dict[str, list[Any]]) -> list[Filing]:
    """Turn a column-oriented submissions table ('recent' or a history page) into Filing rows."""
    rows = zip(
        table["form"],
        table["accessionNumber"],
        table["filingDate"],
        table["reportDate"],
        table["primaryDocument"],
        strict=True,
    )
    return [
        Filing(ticker, cik, form, accn, fdate, rdate, doc) for form, accn, fdate, rdate, doc in rows
    ]


def select_latest(filings: list[Filing], form: str, n: int) -> list[Filing]:
    """Latest n filings of exactly `form` (amendments like 10-K/A excluded), one per period end."""
    candidates = sorted(
        (f for f in filings if f.form == form and f.report_date),
        key=lambda f: f.filing_date,
        reverse=True,
    )
    chosen: list[Filing] = []
    seen_periods: set[str] = set()
    for f in candidates:
        if f.report_date in seen_periods:
            continue
        seen_periods.add(f.report_date)
        chosen.append(f)
        if len(chosen) == n:
            break
    return chosen


def fetch_latest_filings(
    client: SecClient, ticker: str, cik: int, form: str, n: int
) -> list[Filing]:
    """Latest n filings, paging into older submission history if 'recent' is not enough
    (frequent filers such as banks can push older 10-Ks out of the recent window)."""
    payload = client.get_json(SUBMISSIONS_URL.format(cik=cik))
    filings = filings_from_table(ticker, cik, payload["filings"]["recent"])
    chosen = select_latest(filings, form, n)
    for page in payload["filings"].get("files", []):
        if len(chosen) == n:
            break
        older = client.get_json(SUBMISSIONS_PAGE_URL.format(name=page["name"]))
        filings.extend(filings_from_table(ticker, cik, older))
        chosen = select_latest(filings, form, n)
    if len(chosen) < n:
        raise RuntimeError(f"{ticker}: found only {len(chosen)} {form} filings, need {n}")
    return chosen
