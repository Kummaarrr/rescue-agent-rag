import pytest

from rescue_rag.sec.filings import Filing, filings_from_table, resolve_ciks, select_latest


def _table(rows):
    keys = ["form", "accessionNumber", "filingDate", "reportDate", "primaryDocument"]
    return {k: [r[i] for r in rows] for i, k in enumerate(keys)}


TABLE = _table(
    [
        ("8-K", "a-8k", "2025-11-05", "2025-11-05", "x.htm"),
        ("10-K", "a-2025", "2025-10-31", "2025-09-27", "aapl-2025.htm"),
        ("10-K/A", "a-2024a", "2025-01-10", "2024-09-28", "amend.htm"),
        ("10-K", "a-2024", "2024-11-01", "2024-09-28", "aapl-2024.htm"),
        ("10-Q", "a-q3", "2024-08-02", "2024-06-29", "q.htm"),
        ("10-K", "a-2023", "2023-11-03", "2023-09-30", "aapl-2023.htm"),
        ("10-K", "a-2022", "2022-10-28", "2022-09-24", "aapl-2022.htm"),
    ]
)


def test_select_latest_excludes_amendments_and_other_forms():
    filings = filings_from_table("AAPL", 320193, TABLE)
    chosen = select_latest(filings, "10-K", 3)
    assert [f.accession for f in chosen] == ["a-2025", "a-2024", "a-2023"]


def test_select_latest_one_filing_per_period():
    rows = _table(
        [
            ("10-K", "late-refile", "2025-12-01", "2025-09-27", "b.htm"),
            ("10-K", "original", "2025-10-31", "2025-09-27", "a.htm"),
            ("10-K", "prior", "2024-11-01", "2024-09-28", "c.htm"),
        ]
    )
    chosen = select_latest(filings_from_table("X", 1, rows), "10-K", 3)
    assert [f.accession for f in chosen] == ["late-refile", "prior"]


def test_filing_url():
    f = Filing("AAPL", 320193, "10-K", "0000320193-25-000079", "2025-10-31", "2025-09-27", "a.htm")
    assert f.url == "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/a.htm"


def test_resolve_ciks():
    ticker_map = {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}}
    assert resolve_ciks(ticker_map, ["aapl"]) == {"aapl": 320193}
    with pytest.raises(KeyError):
        resolve_ciks(ticker_map, ["MSFT"])
