# Ablation - dev split

| Configuration | Overall | Numeric | Comparisons | Text | Halluc. | False abstain | Evidence retrieved | Citations OK | p50 s | $/1k queries | Run |
|---|---|---|---|---|---|---|---|---|---|---|---|
| v0: naive RAG, Opus 5.5 | 95% | 93% | 90% | 96% | 0% | 4% | 81% | n/a | 4.12 | 37.63 | `v0_dev_20261026-225136` |
| v0-small: naive RAG, Haiku 5.5 | 89% | 91% | 70% | 93% | 10% | 10% | 81% | n/a | 2.04 | 0.92 | `v0-small_dev_20261026-225227` |
| + S1 structure-aware chunks (Haiku) | 95% | 100% | 80% | 93% | 5% | 2% | 91% | n/a | 1.82 | 0.73 | `s1_dev_20261026-231449` |
| + S2 table-aware chunks | 94% | 98% | 70% | 96% | 5% | 2% | 91% | n/a | 1.76 | 0.69 | `s2_dev_20261026-231655` |
| + S3 hybrid retrieval (BM25 + dense) | 92% | 93% | 80% | 96% | 10% | 5% | 86% | n/a | 1.94 | 0.72 | `s3_dev_20261026-232445` |
| + S4 company/year filters (on S3) | 92% | 95% | 100% | 100% | 30% | 0% | 91% | n/a | 3.35 | 1.83 | `s4_dev_20261026-232638` |
| S2 + S4 filters, without S3 (v1 path) | 92% | 95% | 100% | 100% | 30% | 0% | 96% | n/a | 2.05 | 0.75 | `s4-dense_dev_20261026-232951` |
| + S8 grounded answers (citations, numeric check) | 98% | 98% | 90% | 100% | 0% | 1% | 99% | 100% | 3.09 | 0.81 | `s8_dev_20261026-234709` |
| S8 + S5 reranking (Voyage rerank-2.5-lite) | 98% | 95% | 100% | 100% | 0% | 0% | 99% | 99% | 3.77 | 1.00 | `s5_dev_20261026-234805` |
| S8 + S7 calculator tool | 99% | 100% | 90% | 100% | 0% | 1% | 99% | 99% | 2.31 | 0.86 | `s7_dev_20261026-235218` |
| v1 = S2 + S4 + S7 + S8 as a LangGraph agent (S6) | 99% | 100% | 90% | 100% | 0% | 1% | 99% | 99% | 2.92 | 0.86 | `v1_dev_20261026-235534` |

Each step adds to the one above. Differences of 1-2 points are within run-to-run noise (one comparison question = 10 points of that column).
