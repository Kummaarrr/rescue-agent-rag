# Review round 2 (26 Oct 2026) - reviewer feedback and resolution

Checked against the evidence shown, not the filings.

| Finding | Resolution |
|---|---|
| text-0003: round-1 rewording ("earliest date ... anticipates ... could launch") overstates the evidence, which gives a floor | Reworded: "before what date does the company say it does not anticipate a U.S. launch ..." (manual_fixes.yaml) |
| text-0040: "which countries'" but "certain territories in India" is not a country | Reworded to "where" |
| IDs renumbered (round-1 text-0011 is now text-0010; text-0013 seemed gone); make sure verdicts carried over by content | Verdicts were matched by content (filing + Item + answer); round-1 text-0013 (J&J sales returns) was renumbered, not dropped. Text and comparison items now have stable content-derived ids |
| Comparisons with ~11-month period gaps (comp-0006/0008/0010/0012/0015), 6-8 months for comp-0009/0003 | Comparisons re-paired by nearest fiscal year-end, max 100 days apart (actual: 0-95). All 15 comparisons are new and listed in REVIEW_ROUND3.md with their values |
| Footers in text-0001 / text-0019 evidence; "corresponding.z ECCNs" spacing glitch in text-0025 | Footers filtered from evidence; normalisation only removes a space before punctuation that ends a token |
| "attributable to each company" clunky; "attributable to" redundant where there is no material noncontrolling interest | "Attributable to X" only when NCI > 0.5% of net income in the XBRL data (UNH, WMT, XOM; Coca-Cola's NCI is below 0.5%). Comparisons say "net income (excluding noncontrolling interests)" only when one side has material NCI |
| text-0030: "In fiscal year 2025" frames a July 2023 lawsuit | Reworded to "According to Johnson & Johnson's fiscal year 2025 10-K, ..." |

Also found while running v0 and fixed:
- text-0015 (Microsoft acquisitions) dropped: the filing cites two acquisitions, so "which acquisition" is ambiguous.
- The dev/test split is now frozen in splits.json; replacing one item had reshuffled 12 text items between dev and test (no test runs had happened).
- Grader: extracted numbers are checked against the response text and re-read with the judge model on a mismatch (the small reader had read "$11.93" as 1.19).

Reviewer verdicts "OK" for: text-0037, 0038, 0039 (new); text-0001, 0004, 0005, 0006, 0010, 0011, 0013, 0015, 0016, 0018, 0019, 0020, 0023, 0025, 0026, 0027, 0030, 0031, 0032, 0033 (re-extracted evidence); template rewording for XOM/JPM labels.
