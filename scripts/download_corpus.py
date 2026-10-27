"""Download the 10-K corpus and XBRL companyfacts, and freeze data/manifest.csv.

First run: selects the latest N 10-Ks per company and writes the manifest.
Later runs: re-download exactly what the manifest lists (reproducible), unless --refresh.

Usage:
    uv run python scripts/download_corpus.py [--refresh] [--tickers AAPL MSFT]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

from rescue_rag.config import get_corpus, get_env, get_settings, project_path
from rescue_rag.sec.client import SecClient
from rescue_rag.sec.filings import TICKER_MAP_URL, Filing, fetch_latest_filings, resolve_ciks
from rescue_rag.sec.xbrl import COMPANYFACTS_URL, filing_fiscal_year

MANIFEST_FIELDS = [
    "ticker",
    "cik",
    "fy",
    "form",
    "accession",
    "filing_date",
    "report_date",
    "url",
    "path",
    "bytes",
    "sha256",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_manifest(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh", action="store_true", help="re-select filings, rewrite manifest"
    )
    parser.add_argument("--tickers", nargs="*", help="limit to these tickers")
    args = parser.parse_args()

    settings = get_settings()
    corpus = get_corpus()
    raw_dir = project_path(settings["paths"]["raw"])
    xbrl_dir = project_path(settings["paths"]["xbrl"])
    manifest_path = project_path(settings["paths"]["manifest"])
    tickers = args.tickers or [c.ticker for c in corpus.companies]

    with SecClient(
        get_env().sec_user_agent,
        max_per_second=settings["sec"]["max_requests_per_second"],
        timeout=settings["sec"]["timeout_seconds"],
    ) as client:
        overrides = {c.ticker: c.cik for c in corpus.companies if c.cik is not None}
        lookup = [t for t in tickers if t not in overrides]
        ciks = resolve_ciks(client.get_json(TICKER_MAP_URL), lookup) if lookup else {}
        ciks.update({t: overrides[t] for t in tickers if t in overrides})

        if manifest_path.exists() and not args.refresh:
            frozen = [r for r in read_manifest(manifest_path) if r["ticker"] in tickers]
            print(f"Using frozen manifest ({len(frozen)} filings). Pass --refresh to re-select.")
            plan = [
                Filing(
                    r["ticker"],
                    int(r["cik"]),
                    r["form"],
                    r["accession"],
                    r["filing_date"],
                    r["report_date"],
                    Path(r["url"]).name,
                )
                for r in frozen
            ]
        else:
            plan = []
            for t in tickers:
                plan += fetch_latest_filings(
                    client, t, ciks[t], corpus.form, corpus.filings_per_company
                )

        expected_sha = (
            {r["accession"]: r["sha256"] for r in read_manifest(manifest_path)}
            if manifest_path.exists() and not args.refresh
            else {}
        )
        rows: list[dict[str, object]] = []
        facts_cache: dict[str, dict] = {}
        for f in plan:
            facts_path = client.download(
                COMPANYFACTS_URL.format(cik=f.cik), xbrl_dir / f"{f.ticker}.json"
            )
            if f.ticker not in facts_cache:
                facts_cache[f.ticker] = json.loads(facts_path.read_bytes())
            fy = filing_fiscal_year(facts_cache[f.ticker], f.accession)
            if fy is None:
                fy = int(f.report_date[:4])
                print(f"  ! {f.ticker} {f.accession}: no XBRL fy, using report year {fy}")
            suffix = Path(f.primary_document).suffix or ".htm"
            dest = raw_dir / f.ticker / f"{f.ticker}_FY{fy}_{f.accession}{suffix}"
            client.download(f.url, dest)
            rows.append(
                {
                    "ticker": f.ticker,
                    "cik": f.cik,
                    "fy": fy,
                    "form": f.form,
                    "accession": f.accession,
                    "filing_date": f.filing_date,
                    "report_date": f.report_date,
                    "url": f.url,
                    "path": dest.relative_to(project_path(".")).as_posix(),
                    "bytes": dest.stat().st_size,
                    "sha256": sha256(dest),
                }
            )
            if f.accession in expected_sha and expected_sha[f.accession] != rows[-1]["sha256"]:
                print(f"  ! {f.ticker} {f.accession}: sha256 differs from the frozen manifest")
            print(
                f"  {f.ticker} FY{fy} {f.accession} filed {f.filing_date} ({rows[-1]['bytes']:,} B)"
            )

    if args.tickers and manifest_path.exists() and not args.refresh:
        print("Subset run on a frozen manifest: manifest left unchanged.")
    else:
        if args.tickers and manifest_path.exists():
            keep = [r for r in read_manifest(manifest_path) if r["ticker"] not in tickers]
            rows = keep + rows
        rows.sort(key=lambda r: (str(r["ticker"]), int(r["fy"])))  # type: ignore[call-overload]
        write_manifest(manifest_path, rows)
        print(f"Wrote {manifest_path} ({len(rows)} filings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
