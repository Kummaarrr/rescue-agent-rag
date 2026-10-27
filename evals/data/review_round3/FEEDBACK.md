# Review round 3 (26 Oct 2026) - reviewer feedback and resolution

Checked against the evidence shown, not the filings.

| Finding | Resolution |
|---|---|
| comp-3c3552: JPM operating cash flow is negative (-42,012) but the evidence showed 42,012 and the question says "net cash provided by" | Comparisons now require positive figures on both sides; the pair was swapped for comp-c01a9a (WMT FY2026 vs JNJ FY2025 net income, year-ends 34 days apart) using a separate random stream, so no other comparison changed. Also fixed the same issue in a lookup: num-0044 now asks for "net cash provided by (used in) operating activities" |
| Coca-Cola net income: plain "net income" in num-0045 / calc-0005 / calc-0012 vs "(excluding noncontrolling interests)" in comparisons; KO has a small NCI | "Attributable to X" now applies whenever any NCI exists in the XBRL data (KO: -$11M / $18M / $30M); consistent across lookups, computes and comparisons. Applies to KO, UNH, WMT, XOM |

Also: the grader's reader now records outflows and losses ("used $42.0 billion", "(42,012)") as negative numbers.

Reviewer verdicts "OK" for all other round-3 items: comp-a35732, 6a0693, 4ea460, 20ef0e, 6f405e, 52ad07, 6c6094, 131953, b6fb88, feb2ad, 450265, e88544, 844340, 19dc9f; text-ce3dc7, 436c04, c21c2e, 89ac3b, 79530b, d9c222, f42d67; template rewordings.
