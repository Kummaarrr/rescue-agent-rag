"""Questions whose ground truth comes from XBRL facts: lookups, computed figures, comparisons.

Every candidate goes through three checks before it can become a question:
1. fact matching (see rescue_rag.sec.xbrl): the filing's own fiscal-year value;
2. plausibility rules (e.g. R&D between 0.2% and 50% of revenue), which catch concept traps
   such as J&J reporting its main R&D figure under a non-standard concept;
3. evidence check: the figure, as printed in the statements (e.g. "416,161" in millions),
   must appear in the filing text, so the question is answerable from the document itself.
"""

from __future__ import annotations

import hashlib
import random
import re
from collections import defaultdict
from dataclasses import dataclass
from functools import cache

from rag_eval.schema import EvalItem, Gold
from rescue_rag.corpus import CorpusFiling, company_facts, filing_text
from rescue_rag.sec.xbrl import match_fact

REVENUE = [
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "SalesRevenueNet",
]


@dataclass(frozen=True)
class Metric:
    key: str
    phrase: str
    concepts: tuple[str, ...]
    flow: bool  # income/cash-flow item (annual duration) vs balance-sheet item (point in time)
    unit: str = "USD"


METRICS = {
    m.key: m
    for m in [
        Metric("revenue", "total revenue", tuple(REVENUE), flow=True),
        Metric("net_income", "net income", ("NetIncomeLoss",), flow=True),
        Metric("operating_income", "operating income", ("OperatingIncomeLoss",), flow=True),
        Metric(
            "operating_cash_flow",
            "net cash provided by operating activities",
            ("NetCashProvidedByUsedInOperatingActivities",),
            flow=True,
        ),
        Metric("rnd", "research and development expense", ("ResearchAndDevelopmentExpense",), True),
        Metric(
            "eps_diluted",
            "diluted earnings per share",
            ("EarningsPerShareDiluted",),
            flow=True,
            unit="USD/shares",
        ),
        Metric("total_assets", "total assets", ("Assets",), flow=False),
        Metric("total_liabilities", "total liabilities", ("Liabilities",), flow=False),
        Metric("equity", "total shareholders' equity", ("StockholdersEquity",), flow=False),
        Metric(
            "cash",
            "cash and cash equivalents",
            ("CashAndCashEquivalentsAtCarryingValue",),
            flow=False,
        ),
    ]
}

# Company-specific concept preferences, found while validating the corpus.
CONCEPT_OVERRIDES: dict[tuple[str, str], tuple[str, ...]] = {
    # J&J's ResearchAndDevelopmentExpense holds only a small component (~$0.1-1.8B);
    # the reported R&D line (~$15B) uses this concept.
    ("JNJ", "rnd"): ("ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",),
}

# Wording where a company's reported measure differs from the generic phrase (reviewer round 1).
PHRASE_OVERRIDES: dict[tuple[str, str], str] = {
    ("XOM", "revenue"): "total revenues and other income",
    ("JPM", "revenue"): "total net revenue",
}


@cache
def material_nci(ticker: str) -> bool:
    """Does the company report any noncontrolling interest in net income?

    True if, in any corpus filing, net income including noncontrolling interests (ProfitLoss)
    differs from net income attributable to the parent (NetIncomeLoss) at all (>= $1M).
    Only then is "attributable to X" said; it is said consistently for such companies
    (reviewer rounds 2-3: a 0.5% threshold left Coca-Cola's ~$10-30M NCI ambiguous).
    """
    from rescue_rag.corpus import load_manifest

    facts = company_facts(ticker)
    for f in load_manifest():
        if f.ticker != ticker:
            continue
        ni = match_fact(facts, ["NetIncomeLoss"], f.accession, f.report_date, True)
        pl = match_fact(facts, ["ProfitLoss"], f.accession, f.report_date, True)
        if ni and pl and abs(pl.value - ni.value) >= 1e6:
            return True
    return False


def phrase(metric: Metric, ticker: str, name: str) -> str:
    """Precise wording for one company. NetIncomeLoss is net income attributable to the parent."""
    if (ticker, metric.key) in PHRASE_OVERRIDES:
        return PHRASE_OVERRIDES[(ticker, metric.key)]
    if metric.key == "net_income" and material_nci(ticker):
        return f"net income attributable to {name}"
    return metric.phrase


def subject(metric: Metric, ticker: str, name: str) -> str:
    """Noun phrase for a company's measure: "Apple's net income",
    "net income attributable to Walmart" (no doubled company name)."""
    if metric.key == "net_income" and material_nci(ticker):
        return phrase(metric, ticker, name)
    return f"{name}'s {phrase(metric, ticker, name)}"


def _verb(noun_phrase: str) -> str:
    return "were" if "revenues" in noun_phrase or "earnings per share" in noun_phrase else "was"


def period_label(report_date: str) -> str:
    """'2024-01-31' -> 'January 31, 2024'."""
    from datetime import date

    d = date.fromisoformat(report_date)
    return f"{d:%B} {d.day}, {d.year}"


NUMERIC_TOLERANCE = 0.005  # ±0.5% relative
PERCENT_TOLERANCE = 0.15  # ±0.15 percentage points for computed percentages


@dataclass(frozen=True)
class Value:
    filing: CorpusFiling
    metric: Metric
    value: float
    concept: str
    period_end: str


def evidence_string(value: float, unit: str) -> list[str]:
    """How a figure is printed in 10-K tables: millions with separators; EPS in dollars."""
    if unit == "USD/shares":
        return [f"{abs(value):.2f}"]
    return [f"{round(abs(value) / 1e6):,}", f"{round(abs(value) / 1e3):,}"]


def appears_in(text: str, needle: str) -> bool:
    return re.search(rf"(?<![\d,.]){re.escape(needle)}(?![\d,]|\.\d)", text) is not None


def lookup(filing: CorpusFiling, metric: Metric, period_end: str | None = None) -> Value | None:
    concepts = list(CONCEPT_OVERRIDES.get((filing.ticker, metric.key), metric.concepts))
    end = period_end or filing.report_date
    fact = match_fact(
        company_facts(filing.ticker), concepts, filing.accession, end, metric.flow, metric.unit
    )
    if fact is None:
        return None
    return Value(filing, metric, float(fact.value), fact.concept, end)


def plausible(v: Value, revenue: float | None) -> bool:
    key, x = v.metric.key, v.value
    if key in ("revenue", "total_assets", "cash", "total_liabilities") and x <= 0:
        return False
    if key == "eps_diluted" and not 0 < abs(x) < 1000:
        return False
    if revenue:
        # R&D floor 0.2%: ExxonMobil is genuinely ~0.3%; J&J's mis-tagged concept is ~0.1%.
        if key == "rnd" and not 0.002 * revenue <= x <= 0.5 * revenue:
            return False
        if key in ("net_income", "operating_income") and abs(x) > revenue:
            return False
    return True


def validated_values(filings: list[CorpusFiling]) -> tuple[list[Value], list[str]]:
    """All (filing, metric) values that pass plausibility and evidence checks, plus a log."""
    values, log = [], []
    for f in filings:
        text = filing_text(f)
        rev = lookup(f, METRICS["revenue"])
        for metric in METRICS.values():
            v = lookup(f, metric)
            if v is None:
                log.append(f"{f.key} {metric.key}: no matching fact")
                continue
            if not plausible(v, rev.value if rev else None):
                log.append(f"{f.key} {metric.key}: implausible value {v.value:,.0f} ({v.concept})")
                continue
            ev = [s for s in evidence_string(v.value, metric.unit) if appears_in(text, s)]
            if not ev:
                log.append(f"{f.key} {metric.key}: figure not found in filing text")
                continue
            values.append(v)
    return values, log


def other_sources(v: Value, filings: list[CorpusFiling]) -> list[str]:
    """Later filings that report the same figure (prior-year comparatives), unchanged."""
    accns = [v.filing.accession]
    for f in filings:
        if f.ticker != v.filing.ticker or f.accession == v.filing.accession:
            continue
        other = lookup(f, v.metric, period_end=v.period_end)
        if other and abs(other.value - v.value) <= NUMERIC_TOLERANCE * abs(v.value):
            accns.append(f.accession)
    return accns


def _when(metric: Metric, fy: int) -> str:
    return f"as of the end of fiscal year {fy}" if not metric.flow else f"for fiscal year {fy}"


def lookup_questions(
    values: list[Value],
    filings: list[CorpusFiling],
    names: dict[str, str],
    n: int,
    rng: random.Random,
) -> list[EvalItem]:
    """n lookups, spread evenly over companies, then metrics and years."""
    by_company: dict[str, list[Value]] = defaultdict(list)
    for v in values:
        by_company[v.filing.ticker].append(v)
    pools = {t: rng.sample(vs, len(vs)) for t, vs in sorted(by_company.items())}
    chosen: list[Value] = []
    seen_metric: dict[str, set[str]] = defaultdict(set)
    while len(chosen) < n and any(pools.values()):
        for t, pool in pools.items():
            if len(chosen) == n or not pool:
                continue
            # prefer a metric not yet used for this company
            idx = next((i for i, v in enumerate(pool) if v.metric.key not in seen_metric[t]), 0)
            v = pool.pop(idx)
            seen_metric[t].add(v.metric.key)
            chosen.append(v)

    items = []
    for i, v in enumerate(chosen, start=1):
        name, fy, m = names[v.filing.ticker], v.filing.fy, v.metric
        if m.key == "eps_diluted":
            q = f"What were {name}'s diluted earnings per share for fiscal year {fy}?"
        else:
            subj = subject(m, v.filing.ticker, name)
            if m.key == "operating_cash_flow" and v.value < 0:
                # "provided by" doesn't fit an outflow (reviewer round 3); use the filer's label
                subj = subj.replace("provided by", "provided by (used in)")
            q = f"What {_verb(subj)} {subj} {_when(m, fy)}?"
        items.append(
            EvalItem(
                id=f"num-{i:04d}",
                type="numeric_lookup",
                question=q,
                answer=v.value,
                unit=m.unit,
                tolerance=NUMERIC_TOLERANCE,
                tolerance_kind="relative",
                gold=Gold(
                    tickers=[v.filing.ticker],
                    fiscal_years=[fy],
                    accessions=other_sources(v, filings),
                    evidence=[
                        s
                        for s in evidence_string(v.value, m.unit)
                        if appears_in(filing_text(v.filing), s)
                    ],
                ),
                source=f"xbrl:{v.concept}",
            )
        )
    return items


def compute_questions(
    filings: list[CorpusFiling], names: dict[str, str], n_growth: int, n_margin: int,
    rng: random.Random,
) -> list[EvalItem]:  # fmt: skip
    by_ticker: dict[str, list[CorpusFiling]] = defaultdict(list)
    for f in filings:
        by_ticker[f.ticker].append(f)
    growth, margins = [], []
    for fs in by_ticker.values():
        fs = sorted(fs, key=lambda f: f.fy)
        # Growth: latest filing reports both years (current + prior-year comparative).
        for cur_f, prev_f in zip(fs[1:], fs[:-1], strict=True):
            for key in ("revenue", "net_income", "operating_cash_flow"):
                cur = lookup(cur_f, METRICS[key])
                prev = lookup(cur_f, METRICS[key], period_end=prev_f.report_date)
                if cur and prev and prev.value > 0 and cur.value > 0:
                    growth.append((cur, prev))
        for f in fs:
            rev = lookup(f, METRICS["revenue"])
            for key in ("net_income", "operating_income"):
                num = lookup(f, METRICS[key])
                if rev and num and plausible(num, rev.value):
                    margins.append((num, rev))

    def evidence(*vals: Value) -> list[str]:
        text = filing_text(vals[0].filing)
        return [
            s
            for v in vals
            for s in evidence_string(v.value, v.metric.unit)[:1]
            if appears_in(text, s)
        ]

    items = []
    for cur, prev in _spread(growth, n_growth, rng):
        name, m = names[cur.filing.ticker], cur.metric
        pct = (cur.value / prev.value - 1) * 100
        items.append(
            EvalItem(
                id="",
                type="numeric_compute",
                question=(
                    f"By what percentage did {subject(m, cur.filing.ticker, name)} "
                    f"change from fiscal year "
                    f"{cur.filing.fy - 1} to fiscal year {cur.filing.fy}?"
                ),
                answer=round(pct, 4),
                unit="percent",
                tolerance=PERCENT_TOLERANCE,
                tolerance_kind="absolute",
                gold=Gold(
                    tickers=[cur.filing.ticker],
                    fiscal_years=[cur.filing.fy],
                    accessions=[cur.filing.accession],
                    evidence=evidence(cur, prev),
                ),
                source=f"xbrl:growth:{cur.concept}",
                notes=f"current={cur.value:.0f} prior={prev.value:.0f}",
            )
        )
    for num, rev in _spread(margins, n_margin, rng):
        name, fy = names[num.filing.ticker], num.filing.fy
        label = "net profit margin" if num.metric.key == "net_income" else "operating margin"
        items.append(
            EvalItem(
                id="",
                type="numeric_compute",
                question=(
                    f"What was {name}'s {label} "
                    f"({phrase(num.metric, num.filing.ticker, name)} as a percentage of "
                    f"{phrase(rev.metric, rev.filing.ticker, name)}) for fiscal year {fy}?"
                ),
                answer=round(num.value / rev.value * 100, 4),
                unit="percent",
                tolerance=PERCENT_TOLERANCE,
                tolerance_kind="absolute",
                gold=Gold(
                    tickers=[num.filing.ticker],
                    fiscal_years=[fy],
                    accessions=[num.filing.accession],
                    evidence=evidence(num, rev),
                ),
                source=f"xbrl:margin:{num.concept}/{rev.concept}",
                notes=f"numerator={num.value:.0f} revenue={rev.value:.0f}",
            )
        )
    for i, item in enumerate(items, start=1):
        item.id = f"calc-{i:04d}"
    return items


COMPARISON_KEYS = ("revenue", "net_income", "rnd", "total_assets", "operating_cash_flow")
# Pair each company's fiscal year with the other company's fiscal year that ends closest to it,
# and only if the two year-ends are within this many days (reviewer round 2: pairing by the
# fiscal-year label put e.g. Walmart's Jan-2024 year against Exxon's Dec-2024 year).
MAX_YEAR_END_GAP_DAYS = 100


def legacy_comparison_draws(values: list[Value], n: int, rng: random.Random) -> None:
    """Consume the shared random stream exactly as the round-1 comparison generator did.

    Later generators (unanswerable, text passages) draw from the same stream; keeping the draws
    identical keeps their already-reviewed output identical. The new comparison generator uses
    its own seeded stream instead. Remove this when the dataset is next regenerated from scratch.
    """
    index = {(v.filing.ticker, v.filing.fy, v.metric.key): v for v in values}
    pairs = []
    tickers = sorted({v.filing.ticker for v in values})
    for key in COMPARISON_KEYS:
        for i, a in enumerate(tickers):
            for b in tickers[i + 1 :]:
                for fy in sorted({v.filing.fy for v in values}):
                    va, vb = index.get((a, fy, key)), index.get((b, fy, key))
                    if va and vb and abs(va.value - vb.value) > 0.02 * max(va.value, vb.value):
                        pairs.append((va, vb))
    for _ in _spread(pairs, n, rng):
        rng.random()


def _days_apart(a: str, b: str) -> int:
    from datetime import date

    return abs((date.fromisoformat(a) - date.fromisoformat(b)).days)


def comparison_questions(
    values: list[Value],
    names: dict[str, str],
    n: int,
    rng: random.Random,
    filings: list[CorpusFiling] | None = None,
) -> list[EvalItem]:
    by_company_metric: dict[tuple[str, str], list[Value]] = defaultdict(list)
    for v in values:
        if v.metric.key in COMPARISON_KEYS:
            by_company_metric[(v.filing.ticker, v.metric.key)].append(v)
    tickers = sorted({v.filing.ticker for v in values})
    pairs = []
    for key in COMPARISON_KEYS:
        for i, a in enumerate(tickers):
            for b in tickers[i + 1 :]:
                for va in by_company_metric.get((a, key), []):
                    candidates = by_company_metric.get((b, key), [])
                    if not candidates:
                        continue
                    vb = min(candidates, key=lambda v: _days_apart(v.period_end, va.period_end))
                    if _days_apart(vb.period_end, va.period_end) > MAX_YEAR_END_GAP_DAYS:
                        continue
                    # skip near-ties so the right answer is unambiguous
                    if abs(va.value - vb.value) > 0.02 * max(va.value, vb.value):
                        pairs.append((va, vb))
    # Comparisons need positive figures: "higher net cash provided by" is unclear against an
    # outflow (reviewer round 3, JPM). Selected pairs with a non-positive side are swapped for a
    # valid unselected pair drawn from a separate stream, so the other selections don't move.
    selected = _spread(pairs, n, rng)
    spares = [p for p in pairs if p not in selected and p[0].value > 0 and p[1].value > 0]
    replace_rng = random.Random("comparison-replacements")
    selected = [
        p if p[0].value > 0 and p[1].value > 0 else spares.pop(replace_rng.randrange(len(spares)))
        for p in selected
    ]
    items = []
    for va, vb in selected:
        if rng.random() < 0.5:
            va, vb = vb, va
        winner = va if va.value > vb.value else vb
        m = va.metric
        digest = hashlib.sha1(f"{va.filing.accession}|{vb.filing.accession}|{m.key}".encode())
        items.append(
            EvalItem(
                id=f"comp-{digest.hexdigest()[:6]}",
                type="comparison",
                question=comparison_wording(va, vb, names),
                answer=winner.filing.ticker,
                gold=Gold(
                    tickers=[va.filing.ticker, vb.filing.ticker],
                    fiscal_years=[va.filing.fy, vb.filing.fy],
                    accessions=[va.filing.accession, vb.filing.accession],
                    accessions_by_ticker=(
                        {v.filing.ticker: other_sources(v, filings) for v in (va, vb)}
                        if filings
                        else {}
                    ),
                    evidence=[
                        evidence_string(va.value, m.unit)[0],
                        evidence_string(vb.value, m.unit)[0],
                    ],
                ),
                source=f"xbrl:comparison:{m.key}",
                notes=(
                    f"{va.filing.ticker}={va.value:.0f} {vb.filing.ticker}={vb.value:.0f}; "
                    f"year-ends {_days_apart(va.period_end, vb.period_end)} days apart"
                ),
            )
        )
    return items


def comparison_wording(va: Value, vb: Value, names: dict[str, str]) -> str:
    """Names each company's own fiscal year and year-end, since they need not match."""
    m = va.metric
    if m.key == "net_income":
        nci = material_nci(va.filing.ticker) or material_nci(vb.filing.ticker)
        what = "net income (excluding noncontrolling interests)" if nci else "net income"
    else:
        what = m.phrase
    notes = [
        f"for {names[v.filing.ticker]}, {PHRASE_OVERRIDES[(v.filing.ticker, m.key)]}"
        for v in (va, vb)
        if (v.filing.ticker, m.key) in PHRASE_OVERRIDES
    ]
    if notes:
        what += f" ({'; '.join(notes)})"

    def side(v: Value) -> str:
        return (
            f"{names[v.filing.ticker]} for its fiscal year {v.filing.fy} "
            f"(ended {period_label(v.period_end)})"
        )

    return f"Which company reported higher {what}: {side(va)} or {side(vb)}?"


def _spread(candidates: list, n: int, rng: random.Random) -> list:
    """Sample n candidates, cycling over companies so no single company dominates."""
    by_company: dict[str, list] = defaultdict(list)
    for c in candidates:
        first = c[0] if isinstance(c, tuple) else c
        by_company[first.filing.ticker].append(c)
    pools = [rng.sample(v, len(v)) for _, v in sorted(by_company.items())]
    rng.shuffle(pools)
    out: list = []
    while len(out) < n and any(pools):
        for pool in pools:
            if pool and len(out) < n:
                out.append(pool.pop())
    return out
