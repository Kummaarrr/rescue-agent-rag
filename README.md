# Rescue Agent - RAG

A RAG system over 30 SEC 10-K filings, taken from a naive prototype to a production-grade
pipeline - with every change measured on a 150-question evaluation set whose numeric answers
are checked against the SEC's own XBRL data.

## The story

1. **v0 - the tutorial prototype.** Fixed 1,000-token chunks, vector top-5, one generic prompt.
   On a frontier model (Claude Opus 5.5) it is already ~95% accurate - but costs $37.73 per
   1,000 questions. On a model ~40x cheaper (Claude Haiku 5.5) it loses accuracy and sometimes
   answers "from general knowledge" when the filings don't contain the answer.
2. **The rescue: fix what the model is fed, then make it prove its answers.**
   - structure-aware chunks (whole paragraphs inside a 10-K Item, tables as labelled rows,
     a context header naming company / year / section),
   - query understanding with company and fiscal-year filters (retrieval per company),
   - grounded answers: mandatory citations, a numeric grounding check in code, a "not found"
     path, and a calculator tool so arithmetic is never done by the model,
   - orchestrated as a LangGraph agent.
3. **Measured, including what didn't work.** Hybrid keyword search made retrieval worse and
   reranking added cost without gains - both were measured and left out. Better retrieval alone
   made the cheap model *less* safe (empty contexts led to answers from memory) until the
   grounding guardrails went in.
4. **Verified on held-out data.** Final numbers come from a test split never used during
   development, run three times per system.

## Results

**Held-out test split** - 50 questions never used during development. Each system was run 3
times with fresh model calls: mean, with the range across runs in brackets.

| Metric | v0: naive RAG, Claude Opus 5.5 | v0-small: naive RAG, Claude Haiku 5.5 | **v1: rescued, Claude Haiku 5.5** |
|---|---|---|---|
| Overall accuracy | 95.3% (94-96) | 94.0% (92-96) | **98.7% (98-100)** |
| Numeric accuracy (±0.5% of SEC XBRL data) | 95.5% | 97.0% (95.5-100) | **100%** |
| Cross-company comparisons | 93.3% (80-100) | 93.3% (80-100) | **100%** |
| Hallucination rate (unanswerable questions) | 0% | 3.3% (0-10) | **0%** |
| Faithfulness (claims supported by retrieved text) | 93.7% | - | **100%** |
| RAGAS faithfulness / context recall / precision (20-question sample) | 0.91 / 0.90 / 0.86 | - | **0.95 / 1.00** / 0.75 |
| Gold evidence retrieved | 80.0% | 80.0% | **97.5%** |
| Citations contain the evidence | - | - | 97.5% |
| Cost per 1,000 queries | $37.73 | $0.90 | **$0.88** |
| Latency p50 / p95 | 4.1 s / 8.2 s | 1.9 s / 4.6 s | 3.6 s / 9.4 s * |

\* v1 makes two sequential model calls (query understanding, grounded answer). One of the three
runs hit slow API responses (17-18 s on three questions); the other two had p95 of about 5 s.

**In one line:** the rescued pipeline on a model ~40x cheaper beats the naive pipeline on the
frontier model - 98.7% vs 95.3% accuracy, no hallucinations, every claim grounded - at
**$0.88 instead of $37.73 per 1,000 questions** (43x cheaper). It is not faster.

How we got there - every step measured on the dev split, including the two popular techniques
that did not help (hybrid keyword search, reranking):
[evals/results/ABLATION_dev.md](evals/results/ABLATION_dev.md). Full test table with all runs:
[evals/results/FINAL_test.md](evals/results/FINAL_test.md). Write-up with failure analysis and
limitations: [docs/REPORT.md](docs/REPORT.md). Architecture:
[docs/architecture.md](docs/architecture.md).

## Live demo

**[Demo link - added after deployment]** - compare v0 and v1 on highlighted examples, browse all
150 evaluation questions with every system's answer (misses included), or ask v1 your own
question with your own Anthropic API key (the demo holds no key of its own; your key is used
only for that request and never stored).

## Evaluation set

150 questions (dev 100 / test 50, frozen in `evals/data/splits.json`): 45 numeric lookups,
20 calculations, 15 cross-company comparisons, 40 text facts and 30 unanswerable questions.
Numeric answers come from the SEC's XBRL data and must appear in the filing text; text
questions have verbatim evidence checked in code and by a second model. Three rounds of human
review are recorded in `evals/data/review_round*/`. Judge calibration against human labels:
90% agreement (`evals/calibration/`).

## Stack

Python 3.12 · Claude Haiku 5.5 / Opus 5.5 (Anthropic SDK, structured outputs) · Voyage AI
embeddings · Qdrant · LangGraph · BeautifulSoup/lxml · SEC EDGAR + XBRL APIs · RAGAS ·
Streamlit · pytest, ruff, mypy · GitHub Actions. Measured and left out: BM25 hybrid search,
reranking.

## Repository layout

```
src/rescue_rag/   the RAG system: SEC client, parsing, chunking, retrieval, LangGraph agent
src/rag_eval/     evaluation harness - works against any RAG system via an adapter (HTTP too)
evals/            dataset, review rounds, judge calibration, results of every run
scripts/          download, index, evaluate, ablation and final tables, RAGAS, demo build
app/              Streamlit demo (pre-computed answers + live questions on your own key)
config/           companies, models, prices, pipeline settings
docs/             REPORT.md (results write-up), architecture.md (diagrams)
tests/            unit tests
```

## Reproduce

```
uv sync --group dev --extra agent --extra app
cp .env.example .env   # ANTHROPIC_API_KEY, VOYAGE_API_KEY, SEC_USER_AGENT
uv run python scripts/download_corpus.py      # the frozen 30 filings (data/manifest.csv)
uv run python scripts/build_index.py --variant v0
uv run python scripts/build_index.py --variant s2
uv run python scripts/run_eval.py --pipeline v1 --split dev
uv run python scripts/run_eval.py --pipeline v1 --split test --i-mean-it --repeats 3
uv run python scripts/final_table.py --split test
uv run streamlit run app/streamlit_app.py
```

Raw filings are not committed; the download script recreates them from SEC EDGAR. A full
dev run costs about $0.25 on v1 and $3.60 on v0 (Opus) at list prices.

## License

MIT
