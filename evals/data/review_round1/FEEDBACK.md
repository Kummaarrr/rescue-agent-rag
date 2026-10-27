# Review round 1 (26 Oct 2026) - reviewer feedback

## Evidence doesn't support the answer (fix or drop)
- text-0004: question asks for the IHC's name and what the Parent Company must contribute; evidence covers only the name.
- text-0019: evidence is only the lead-in sentence ("ratings were as follows:"); the table with Moody's Aa2 / P-1 is missing.
- text-0029: answer's "37 basis point" figure isn't in the evidence; the checker cites text not in the evidence, so stored evidence is a trimmed version of what the checker saw.
- text-0030: evidence is cut off before it mentions Pioneer.
- text-0005: evidence truncated mid-sentence; supports the compound name but not "certain types of caramel coloring used in cola".
- General: the checker agreeing doesn't clear these - it saw more text than the stored evidence. Re-extract spans for all 40 items.

## Minor question or answer issues
- text-0039: asks for "reasons" (plural) but evidence gives one for food; premise "fail quality expectations" not in evidence.
- text-0010 / text-0020: same question and answer, differing only in fiscal year; keep one or make them distinguishable.
- text-0016: evidence has line-break artifacts; normalise.
- text-0009 / text-0003: awkward wording ("Walmart's Walmart U.S. segment"; "before what date does the company not anticipate").
- General: nearly every question is answered by a near-verbatim span; fine for a baseline, but mostly tests retrieval rather than reasoning.

## Numeric and other types
- calc-0011: Exxon "net income" (incl. or attributable to ExxonMobil?) and "Revenues" (sales vs total revenues and other income) are ambiguous; specify tags and wording.
- comp-0015 / comp-0007: fiscal year ends differ (WMT January vs XOM December; MSFT June vs WMT January); state the fiscal period alignment.
- unans-0013 / unans-0011: UNH 2012 and JPM 2014 data exist in public filings; only unanswerable relative to the corpus.
- unans-0023: expected answer "None" is too vague; the ideal answer rejects the false premise and the grader should check for that.

## Looked fine
text-0001, 0002, 0006-0009, 0011-0015, 0017, 0018, 0020-0028, 0031-0038, 0040, and the remaining numeric items (calc-0018, calc-0006, calc-0003, calc-0009, num-0031, num-0033, unans-0001/0003/0006). Calc arithmetic checks out.
