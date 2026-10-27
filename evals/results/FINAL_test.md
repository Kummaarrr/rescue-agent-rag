# Final results - held-out test split

50 questions never used during development. Each system was run 3 times with fresh model calls; cells show the mean and, in brackets, the range across runs. One question is 2 points of overall accuracy.

| Metric | v0: naive RAG, Claude Opus 5.5 | v0-small: naive RAG, Claude Haiku 5.5 | v1: rescued, Claude Haiku 5.5 |
|---|---|---|---|
| Overall accuracy | 95.3% (94.0-96.0) | 94.0% (92.0-96.0) | 98.7% (98.0-100.0) |
| Numeric accuracy (lookup + compute) | 95.5% | 97.0% (95.5-100.0) | 100.0% |
| Cross-company comparisons | 93.3% (80.0-100.0) | 93.3% (80.0-100.0) | 100.0% |
| Text answers passing judge | 92.3% | 87.2% (84.6-92.3) | 94.9% (92.3-100.0) |
| Unanswerable handled correctly | 100.0% | 96.7% (90.0-100.0) | 100.0% |
| Hallucination rate (unanswerable) | 0.0% | 3.3% (0.0-10.0) | 0.0% |
| False abstain rate (answerable) | 5.8% (5.0-7.5) | 3.3% (2.5-5.0) | 1.7% (0.0-2.5) |
| Gold evidence retrieved | 80.0% | 80.0% | 97.5% |
| Citations contain the evidence | n/a | n/a | 97.5% (97.4-97.5) |
| Faithfulness (Opus judge, run 1) | 93.7% | n/a | 100.0% |
| Latency p50 (s) | 4.07 (4.02-4.11) | 1.93 (1.88-2.01) | 3.62 (3.31-4.19) |
| Latency p95 (s) | 8.17 (7.24-9.94) | 4.59 (3.51-5.53) | 9.44 (5.08-17.79) |
| Cost per 1,000 queries (USD) | $37.73 (37.60-37.83) | $0.90 (0.90-0.90) | $0.88 (0.88-0.89) |

Runs: `v0_test_20261027-001212_rep1`, `v0_test_20261027-001443_rep2`, `v0_test_20261027-001618_rep3`, `v0-small_test_20261027-000916_rep1`, `v0-small_test_20261027-001017_rep2`, `v0-small_test_20261027-001111_rep3`, `v1_test_20261027-000433_rep1`, `v1_test_20261027-000642_rep2`, `v1_test_20261027-000755_rep3`
