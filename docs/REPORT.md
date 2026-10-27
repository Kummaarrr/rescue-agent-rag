# Rescue Agent - RAG: results report

27 October 2026. All numbers are measured; nothing below is a projection.

## 1. Summary

A naive RAG prototype over 30 SEC 10-K filings was rebuilt into a grounded, cited pipeline and
measured at every step. On a held-out test split (50 questions, 3 runs per system):

| | v0: naive, Claude Opus 5.5 | v1: rescued, Claude Haiku 5.5 |
|---|---|---|
| Overall accuracy | 95.3% | **98.7%** |
| Numeric accuracy (vs SEC XBRL data) | 95.5% | **100%** |
| Hallucination on unanswerable questions | 0% | **0%** |
| Faithfulness (own judge / RAGAS) | 93.7% / 0.91 | **100% / 0.95** |
| Cost per 1,000 queries | $37.73 | **$0.88** |
| Latency p50 | 4.1 s | 3.6 s |

**The rescue was a cost rescue.** The naive prototype was not inaccurate - on a frontier model
it was already ~95% right. It was expensive. Restructuring what the model is fed and forcing
grounded, cited answers let a model ~40x cheaper beat it, at 1/43 of the cost per query.

## 2. Setup

**Corpus.** The 3 latest 10-K filings of 10 companies across sectors (AAPL, MSFT, NVDA, AMZN,
JPM, UNH, JNJ, XOM, WMT, KO): 30 filings, ~3M tokens, frozen in `data/manifest.csv`.

**Evaluation set (150 questions; dev 100 / test 50, frozen).**

| Type | n | Ground truth |
|---|---|---|
| Numeric lookup | 45 | SEC XBRL facts; the figure must also appear in the filing text |
| Numeric compute (growth, margins) | 20 | Computed from XBRL facts |
| Cross-company comparison | 15 | XBRL facts, fiscal year-ends at most 95 days apart |
| Factual text | 40 | Drafted by Claude Opus, verbatim evidence checked in code, then checked by Claude Sonnet seeing only question + answer + evidence |
| Unanswerable | 30 | Future / pre-corpus years, companies outside the corpus, false premises, fabricated events; must abstain or reject the premise |

The set went through **three rounds of human review** (`evals/data/review_round*/`); every
finding and its resolution is recorded there.

**Scoring.** Numbers are read from the answer by a small model and compared **in code**
(±0.5% relative; ±0.15 percentage points for percentages). Text answers are judged by Claude
Opus 5.5 against the reference answer and evidence (pass at 4/5). Retrieval and citations are
scored in code (does a retrieved / cited chunk from a gold filing contain the gold figure or
quote?). Faithfulness: share of claims supported by the retrieved context (Opus judge).

## 3. The rescue ladder (dev split, Claude Haiku 5.5)

Each step was built, measured on the dev split, and kept only if it helped.

| Step | Change | Overall | Hallucination | Evidence retrieved | $/1k | Kept? |
|---|---|---|---|---|---|---|
| v0 (Opus) | naive reference | 95% | 0% | 81% | 37.63 | - |
| v0-small | same pipeline on Haiku | 89% | 10% | 81% | 0.92 | - |
| S1 | structure-aware chunks with context headers | 95% | 5% | 91% | 0.73 | yes |
| S2 | tables as labelled rows | 94% | 5% | 91% | 0.69 | yes (for citations) |
| S3 | hybrid BM25 + dense | 92% | 10% | 86% | 0.72 | **no** |
| S4 | company / fiscal-year filters | 92% | **30%** | 96% | 0.75 | yes |
| S8 | grounded answers, citations, numeric check | 98% | 0% | 99% | 0.81 | yes |
| S5 | reranking (Voyage rerank-2.5-lite) | 98% | 0% | 99% | 1.00 | **no** |
| S7 | calculator tool | 99% | 0% | 99% | 0.86 | yes |
| v1 | S2 + S4 + S7 + S8 as a LangGraph agent | 99% | 0% | 99% | 0.86 | final |

What the ladder shows:
1. **Chunking is the highest-leverage fix.** Fixed-size chunks cut tables and sentences in
   half; chunks that follow the document's own structure lifted the cheap model from 89% to 95%.
2. **Popular techniques are not free wins.** Hybrid search lowered evidence recall on this
   data (91% -> 86%); reranking added 24% to cost with no gain. Both stayed out.
3. **Better retrieval can make a cheap model less safe.** Filters (S4) fixed comparisons and
   wrong-year answers, but questions about years or companies outside the corpus now got empty
   contexts - and Haiku answered 30% of them from memory. Opus never did.
4. **Guardrails fixed it.** "No context, no answer", citations restricted to retrieved
   excerpts, and grounded-only instructions brought hallucination to 0%. The numeric grounding
   check (code) never had to fire on dev; it stays as a safety net.

## 4. Final results (held-out test split)

Mean of 3 runs; range in brackets. Full table: `evals/results/FINAL_test.md`.

| Metric | v0 (Opus) | v0-small (Haiku) | v1 (Haiku) |
|---|---|---|---|
| Overall accuracy | 95.3% (94-96) | 94.0% (92-96) | **98.7% (98-100)** |
| Numeric accuracy | 95.5% | 97.0% (95.5-100) | **100%** |
| Comparisons | 93.3% (80-100) | 93.3% (80-100) | **100%** |
| Text answers passing judge | 92.3% | 87.2% (84.6-92.3) | **94.9% (92.3-100)** |
| Hallucination (unanswerable) | 0% | 3.3% (0-10) | **0%** |
| False "not found" (answerable) | 5.8% | 3.3% | **1.7%** |
| Gold evidence retrieved | 80.0% | 80.0% | **97.5%** |
| Citations contain the evidence | - | - | 97.5% |
| Faithfulness (Opus judge, run 1) | 93.7% | - | **100%** |
| Latency p50 / p95 | 4.1 s / 8.2 s | 1.9 s / 4.6 s | 3.6 s / 9.4 s |
| Cost per 1,000 queries | $37.73 | $0.90 | **$0.88** |

**Dev vs test.** The cheap naive baseline did better on test (94.0%) than on dev (89.0%), so the
measured gap between v0-small and v1 is smaller on test (4.7 points) than on dev (10 points).
With 50 questions, one question is 2 points; we report the test numbers as the result.

## 5. RAGAS cross-check

RAGAS 0.4.3 with Claude Opus 5.5 as the judge, on a deterministic stratified sample of 20
answerable test questions (run 1). Independent of the project's own metrics.

| RAGAS metric | v0 (Opus) | v1 (Haiku) |
|---|---|---|
| Faithfulness | 0.91 | **0.95** |
| Context recall | 0.90 | **1.00** |
| Context precision | **0.86** | 0.75 |

- Faithfulness and context recall agree with the project's metrics. RAGAS splits answers into
  finer-grained statements, so its faithfulness for v1 (0.95) is stricter than the project's
  judge (100%).
- **Context precision is lower for v1 by design.** v1 retrieves 10 chunks per company
  (20 for comparisons) so the evidence is reliably present (recall 1.00); more of what it
  retrieves is therefore not needed. v0 retrieves 5 larger chunks: more "precise", but it
  misses evidence more often. Retrieving fewer chunks for single-company lookups is an obvious
  next optimisation (also lowers cost and latency).

## 6. Judge calibration

30 text answers from dev runs were labelled PASS/FAIL by a human reviewer, blind to the judge's
verdicts (`evals/calibration/`: labels, key, `result.json`).

| | |
|---|---|
| Agreement | **90% (27/30)** - above the 85% threshold set in the plan |
| Cohen's kappa | 0.35 - low because the sample is lopsided (28 human PASS, 2 FAIL), which makes chance agreement high |
| Judge FAIL, human PASS | 2 (cal-14, cal-21) |
| Judge PASS, human FAIL | 1 (cal-30) |

The disagreements show two systematic biases:
- **Too strict on extra detail.** The judge sees only the gold evidence, so it marks down correct
  answers that add true details it cannot verify (cal-14: other years' turnover rates; cal-21:
  "without merit", "defending vigorously"). The rubric says extra detail is fine unless wrong.
- **Too lenient on grounding.** It passed (4/5) a response that said the context did not name the
  business and then supplied the right name "from outside knowledge" (cal-30).

**Effect on the results: none on v1 or v0.** On the test split every failed text answer from
v1 and v0 was an abstention, which is scored in code, not by the judge. The judge failed two
v0-small answers (the same question, 3/5); if those were the strictness bias, v0-small is
understated by at most ~1 point overall.

The rubric was **not** revised: it passes the threshold, and tuning it on the same 30 labels
used to measure it would overstate its accuracy. Next step: add "unverifiable extra detail is
not an error" and "answers that disclaim the sources and rely on outside knowledge score <= 2",
then validate on freshly labelled answers.

## 7. Failure analysis (v1, test split)

- **One recurring miss in all three runs** (text-ae5eea, Coca-Cola 4-MEI): the key sentence is
  split across two chunks ("...formed during the manufacturing of" | "certain types of caramel
  coloring"). The grounding instructions make the model refuse because the excerpt is cut off.
  The guardrail's trade-off in one example: occasionally too cautious, never inventive. Fix:
  never split a sentence that continues across HTML blocks.
- **Retrieval miss on dev** (J&J total revenue in a comparison): the J&J revenue line was not
  among the chunks retrieved for J&J; v1 answered "not found" instead of guessing.
- **Latency.** Two sequential model calls (query understanding, then the answer) keep v1's
  p50 near v0's. In one run, slow API responses pushed three questions to 17-18 s.

## 8. Limitations

- **Small test split.** 50 questions; one question moves overall accuracy by 2 points.
- **Explicit questions.** Every question names the company and fiscal year. Real users write
  "What was Apple's latest revenue?"; that is not tested here.
- **One domain, one corpus size.** 30 filings of 10 large US companies.
- **Same-family judge.** Systems and judge are all Claude models. Mitigations: 110 of 150
  questions are scored in code; RAGAS cross-check; human calibration of the judge (90%
  agreement, two known biases - section 6).
- **No sampling control.** The API no longer accepts `temperature`; results are means of 3 runs.
- **List prices.** Costs use list prices at the time of the runs (Anthropic, Voyage); Voyage
  embeddings and reranking were within the free tier.
- **Not faster.** v1 is cheaper and more accurate, not lower-latency.

## 9. Reproduce

```
uv sync --group dev --extra agent --extra ragas
uv run python scripts/download_corpus.py            # frozen manifest -> same 30 filings
uv run python scripts/build_index.py --variant v0
uv run python scripts/build_index.py --variant s2
uv run python scripts/run_eval.py --pipeline v1 --split dev
uv run python scripts/run_eval.py --pipeline v1 --split test --i-mean-it --repeats 3
uv run python scripts/final_table.py --split test
```
Needs `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY` and `SEC_USER_AGENT` in `.env`.
