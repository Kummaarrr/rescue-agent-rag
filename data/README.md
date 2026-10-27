# data/

Everything here except this file and `manifest.csv` is git-ignored and recreated by `scripts/download_corpus.py`.

- `raw/` - 10-K HTML documents from SEC EDGAR
- `xbrl/` - companyfacts JSON
- `processed/` - chunks and indexes
- `manifest.csv` - frozen list of corpus filings (ticker, fy, accession, filing date, URL, bytes, sha256)
