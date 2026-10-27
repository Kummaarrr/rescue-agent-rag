"""Scoring one response against one eval item.

- Reader (small model, one call per response): classifies behaviour (answered / abstained /
  rejected the premise) and extracts the final number or the chosen company. Code then applies
  the tolerance check, so numeric correctness never depends on an LLM's judgement of "close".
- Judge (judge model, factual_text only): 1-5 rubric against the reference answer and evidence;
  pass at >= 4.
- Retrieval (code only): did the retrieved contexts include the gold filing (doc hit) and the
  gold evidence itself (evidence hit)?
- Faithfulness (judge model, optional): share of the response's claims supported by the
  retrieved contexts.

The harness currently calls Claude through rescue_rag.llm; that is the only coupling to the
project, and it is what a client engagement would swap for its own LLM access.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Literal

from pydantic import BaseModel, Field

from rag_eval.adapters import Response
from rag_eval.schema import EvalItem
from rag_eval.text import contains, contains_number, normalize
from rescue_rag import llm

BehaviorSeen = Literal["answered", "abstained", "rejected_premise"]
PASS_SCORE = 4
MIN_QUOTE_CHARS = 40  # shorter quotes (headings) are too generic to prove retrieval


class Reading(BaseModel):
    behavior: BehaviorSeen = Field(
        description="answered: gives a substantive answer to the question asked; abstained: "
        "says the requested information is not available / cannot answer (even if it then "
        "offers other, related figures, e.g. a different year). If it still supplies the "
        "requested answer from general knowledge or memory, that counts as answered. "
        "rejected_premise: says the "
        "question's premise is false or not supported by the documents"
    )
    # The number exactly as written plus its scale word; code does the conversion (an LLM
    # asked to convert "$110,543 million" to dollars sometimes returns 110543).
    number_as_written: float | None = Field(
        description="The final numeric answer exactly as written, without its scale word: "
        "'$110,543 million' -> 110543; '$416.2 billion' -> 416.2; '14.9%' -> 14.9; "
        "'$6.08 per share' -> 6.08. Null if no numeric answer is given."
    )
    scale: Literal["none", "thousand", "million", "billion", "trillion"] = Field(
        description="Scale word attached to that number ('million', 'billion', ...), or 'none'"
    )
    chosen_option: Literal["A", "B"] | None = Field(
        description="For two-option questions: which option the response picks; else null"
    )


class Judgement(BaseModel):
    score: int = Field(ge=1, le=5)
    reason: str


READER_PROMPT = """Read a question-answering system's response and record what it says.
Do not judge whether it is correct. If the response states its final figure at more than one
precision (e.g. "about 114%" and later "114.2%"), record the most precise one. For a change
described as a decrease ("fell 2.4%", "decreased by 0.77%"), or an amount described as an
outflow or loss ("used $42.0 billion in operating activities", "(42,012)", "a net loss of"),
record it as a negative number.

Question: {question}
{options}
Response:
<response>
{response}
</response>"""

JUDGE_PROMPT = """Grade a response to a question about a company's 10-K filing.

Question: {question}
Reference answer: {reference}
Supporting evidence from the filing:
{evidence}

Response to grade:
<response>
{response}
</response>

Score 1-5:
5 = fully correct and complete; 4 = correct, minor omissions or extra detail that is not wrong;
3 = partly correct or missing an important part; 2 = mostly incorrect, or correct content mixed
with a contradicting claim; 1 = wrong, or no answer. Judge facts, not style or length."""

FAITHFULNESS_PROMPT = """Check whether a response is supported by the context it was given.

Context:
<context>
{context}
</context>

Response:
<response>
{response}
</response>

List each factual claim in the response and whether the context supports it."""


class Claim(BaseModel):
    claim: str
    supported: bool


class ClaimCheck(BaseModel):
    claims: list[Claim]


@dataclass
class Score:
    id: str
    type: str
    split: str | None
    behavior: str
    correct: bool
    numeric_value: float | None = None
    judge_score: int | None = None
    judge_reason: str = ""
    doc_hit: bool | None = None
    evidence_hit: bool | None = None
    citation_hit: bool | None = None  # cited contexts contain the gold evidence
    faithfulness: float | None = None
    cost_usd: float | None = None
    latency_s: float | None = None
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


SCALE = {"none": 1.0, "thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12}


def to_base_units(reading: Reading) -> float | None:
    if reading.number_as_written is None:
        return None
    return reading.number_as_written * SCALE[reading.scale]


def _within(value: float, item: EvalItem) -> bool:
    assert isinstance(item.answer, int | float) and item.tolerance is not None
    gold = float(item.answer)
    if item.tolerance_kind == "absolute":
        return abs(value - gold) <= item.tolerance
    return abs(value - gold) <= item.tolerance * abs(gold)


def _comparison_options(item: EvalItem) -> tuple[str, str]:
    """Option A/B tickers, in the order the question names them."""
    a, b = item.gold.tickers
    return a, b


def retrieval_hits(item: EvalItem, r: Response) -> tuple[bool | None, bool | None]:
    if item.type == "unanswerable" or not r.contexts:
        return None, None
    if not any(c.accession for c in r.contexts):
        return None, None  # system doesn't expose sources (e.g. an external endpoint)
    gold = set(item.gold.accessions)
    from_gold = [c for c in r.contexts if c.accession in gold]

    if item.type == "comparison" and item.gold.accessions_by_ticker:
        # each company: a context from any of its filings that report the figure
        sides = list(item.gold.accessions_by_ticker.items())
        doc_hit = all(any(c.accession in accs for c in r.contexts) for _, accs in sides)
        ev_hit = all(
            any(c.accession in accs and contains_number(c.text, num) for c in r.contexts)
            for (_, accs), num in zip(sides, item.gold.evidence, strict=False)
        )
        return doc_hit, ev_hit
    if item.type == "comparison":
        # both companies' filings, each with its own figure
        doc_hit = {c.accession for c in from_gold} >= gold
        ev_hit = all(
            any(c.accession == acc and contains_number(c.text, num) for c in r.contexts)
            for acc, num in zip(item.gold.accessions, item.gold.evidence, strict=False)
        )
        return doc_hit, ev_hit

    doc_hit = bool(from_gold)
    if item.type in ("numeric_lookup", "numeric_compute"):
        if item.type == "numeric_compute":  # needs every input figure
            ev_hit = all(
                any(contains_number(c.text, n) for c in from_gold) for n in item.gold.evidence
            )
        else:
            ev_hit = any(contains_number(c.text, n) for c in from_gold for n in item.gold.evidence)
        return doc_hit, ev_hit

    quotes = [q for q in item.gold.evidence if len(q) >= MIN_QUOTE_CHARS] or item.gold.evidence
    # a quote split across two naive chunks still counts if its start or end is retrieved
    probes = [p for q in quotes for p in {q, q[:100], q[-100:]}]
    ev_hit = any(contains(c.text, p) for c in from_gold for p in probes)
    return doc_hit, ev_hit


def read(item: EvalItem, r: Response, model: str) -> Reading:
    options = ""
    if item.type == "comparison":
        a, b = _comparison_options(item)
        options = f"Options: A = {a}, B = {b} (as named in the question)\n"
    return llm.parse(
        model,
        READER_PROMPT.format(question=item.question, options=options, response=r.answer),
        Reading,
        effort="low",
    )


_NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def number_in_text(number: float, text: str) -> bool:
    """Is `number` literally present in the response (ignoring thousands separators)?"""
    found = {float(m.replace(",", "")) for m in _NUMBER_RE.findall(text)}
    return any(abs(f - number) <= 1e-9 * max(1.0, abs(number)) for f in found)


def read_checked(item: EvalItem, r: Response, model: str, fallback_model: str) -> Reading:
    """Reader output, re-read with a stronger model if the extracted number isn't actually in
    the response (round-1 v0 run: the small model read "$11.93" as 1.19)."""
    reading = read(item, r, model)
    n = reading.number_as_written
    if n is not None and not number_in_text(abs(n), r.answer):
        reading = read(item, r, fallback_model)
    return reading


def judge(item: EvalItem, r: Response, model: str) -> Judgement:
    return llm.parse(
        model,
        JUDGE_PROMPT.format(
            question=item.question,
            reference=item.answer,
            evidence="\n".join(f"- {e}" for e in item.gold.evidence),
            response=r.answer,
        ),
        Judgement,
        effort="medium",
    )


def faithfulness(r: Response, model: str) -> float | None:
    if not r.contexts or not r.answer.strip():
        return None
    check = llm.parse(
        model,
        FAITHFULNESS_PROMPT.format(
            context="\n\n".join(normalize(c.text) for c in r.contexts), response=r.answer
        ),
        ClaimCheck,
        effort="medium",
    )
    if not check.claims:
        return None
    return sum(c.supported for c in check.claims) / len(check.claims)


def grade(
    item: EvalItem,
    r: Response,
    *,
    reader_model: str,
    judge_model: str,
    with_faithfulness: bool = False,
) -> Score:
    reading = read_checked(item, r, reader_model, judge_model)
    value = to_base_units(reading)
    doc_hit, ev_hit = retrieval_hits(item, r)
    cite_hit = None
    if r.citations and item.type != "unanswerable":
        cited = [c for c in r.contexts if c.chunk_id in set(r.citations)]
        cite_hit = retrieval_hits(item, Response(r.answer, contexts=cited))[1]
    s = Score(
        id=item.id,
        type=item.type,
        split=item.split,
        behavior=reading.behavior,
        correct=False,
        numeric_value=value,
        doc_hit=doc_hit,
        evidence_hit=ev_hit,
        citation_hit=cite_hit,
        cost_usd=r.cost_usd,
        latency_s=r.latency_s,
    )
    if item.type == "unanswerable":
        if item.expected_behavior == "reject_premise":
            s.correct = reading.behavior == "rejected_premise"
        else:
            s.correct = reading.behavior in ("abstained", "rejected_premise")
    elif reading.behavior != "answered":
        s.correct = False
    elif item.type in ("numeric_lookup", "numeric_compute"):
        s.correct = value is not None and _within(value, item)
    elif item.type == "comparison":
        a, b = _comparison_options(item)
        chosen = {"A": a, "B": b}.get(reading.chosen_option or "")
        s.correct = chosen == item.answer
    else:
        j = judge(item, r, judge_model)
        s.judge_score, s.judge_reason = j.score, j.reason
        s.correct = j.score >= PASS_SCORE
    if with_faithfulness and reading.behavior == "answered":
        s.faithfulness = faithfulness(r, judge_model)
    return s
