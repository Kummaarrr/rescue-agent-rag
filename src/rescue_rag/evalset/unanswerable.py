"""Unanswerable questions: the right behaviour is to say the filings don't contain the answer.

Five kinds, each probing a different way RAG systems hallucinate:
- future_year:    a fiscal year after the corpus (no filing can contain it);
- old_year:       a fiscal year long before the corpus (recent 10-Ks only carry 2-3 years of data);
- other_company:  a company outside the corpus;
- false_premise:  presupposes something the filings contradict (e.g. a revenue collapse);
- fabricated:     asks about an event that never happened (a merger between corpus companies).
"""

from __future__ import annotations

import random

from rag_eval.schema import Behavior, EvalItem, Gold
from rescue_rag.corpus import CorpusFiling
from rescue_rag.evalset.xbrl_questions import METRICS, lookup

OUTSIDE_COMPANIES = ["Tesla", "Netflix", "Pfizer", "Bank of America", "Costco", "PepsiCo", "Intel"]
PHRASES = [
    "total revenue",
    "net income",
    "total assets",
    "net cash provided by operating activities",
]
FUTURE_YEARS = [2028, 2029, 2030]
OLD_YEARS = [2012, 2013, 2014, 2015]

# The ideal response to these rejects the premise (e.g. "revenue did not fall"), not just abstains.
REJECT_KINDS = {"false_premise", "fabricated"}
REJECT: Behavior = "reject_premise"
ABSTAIN: Behavior = "abstain"

COUNTS = {"future_year": 8, "old_year": 6, "other_company": 6, "false_premise": 5, "fabricated": 5}


def unanswerable_questions(
    filings: list[CorpusFiling], names: dict[str, str], rng: random.Random
) -> list[EvalItem]:
    tickers = sorted(names)
    raw: list[tuple[str, str, Gold]] = []

    # Sample without replacement so no question repeats.
    for kind, years in (("future_year", FUTURE_YEARS), ("old_year", OLD_YEARS)):
        combos = [(t, y, p) for t in tickers for y in years for p in PHRASES]
        for t, y, p in rng.sample(combos, COUNTS[kind]):
            q = f"What was {names[t]}'s {p} for fiscal year {y}?"
            raw.append((kind, q, Gold(tickers=[t])))
    for company in rng.sample(OUTSIDE_COMPANIES, COUNTS["other_company"]):
        y, p = rng.choice([2023, 2024, 2025]), rng.choice(PHRASES)
        raw.append(("other_company", f"What was {company}'s {p} for fiscal year {y}?", Gold()))

    # False premise: claim a >50% revenue drop in a year where revenue actually changed < 25%.
    candidates = []
    by_ticker: dict[str, list[CorpusFiling]] = {}
    for f in filings:
        by_ticker.setdefault(f.ticker, []).append(f)
    for fs in by_ticker.values():
        fs.sort(key=lambda f: f.fy)
        for cur_f, prev_f in zip(fs[1:], fs[:-1], strict=True):
            cur = lookup(cur_f, METRICS["revenue"])
            prev = lookup(cur_f, METRICS["revenue"], period_end=prev_f.report_date)
            if cur and prev and abs(cur.value / prev.value - 1) < 0.25:
                candidates.append(cur_f)
    for f in rng.sample(candidates, COUNTS["false_premise"]):
        raw.append(
            (
                "false_premise",
                f"Why did {names[f.ticker]}'s total revenue fall by more than half in "
                f"fiscal year {f.fy}?",
                Gold(tickers=[f.ticker], fiscal_years=[f.fy], accessions=[f.accession]),
            )
        )

    pairs = [(a, b) for a in tickers for b in tickers if a != b]
    for a, b in rng.sample(pairs, COUNTS["fabricated"]):
        y = rng.choice([2024, 2025])
        raw.append(
            (
                "fabricated",
                f"According to {names[a]}'s fiscal year {y} annual report, what price did "
                f"{names[a]} pay to acquire {names[b]}?",
                Gold(tickers=[a, b]),
            )
        )

    return [
        EvalItem(
            id=f"unans-{i:04d}",
            type="unanswerable",
            question=q,
            answer=None,
            gold=gold,
            expected_behavior=REJECT if kind in REJECT_KINDS else ABSTAIN,
            source=f"template:{kind}",
            notes=kind,
        )
        for i, (kind, q, gold) in enumerate(raw, start=1)
    ]
