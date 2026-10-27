"""Factual text questions drafted by Claude from 10-K passages, then checked.

1. Draft: the generator model writes one question per passage, with a short reference answer.
2. Code check: the question must name the company and the fiscal year.
3. Model check: a second model sees the question and the passage, answers independently, and
   judges whether the question is self-contained and the reference answer correct.
4. Grounding (added after review round 1): the generator extracts verbatim quotes covering every
   part of the answer and every premise of the question; code verifies each quote is verbatim;
   then the checker sees ONLY the question, answer and quotes - not the passage - and must
   confirm the quotes alone support everything. Step 3 alone was not enough: the checker saw
   the whole passage, so it could approve answers the stored evidence did not support.
5. Near-duplicates (same question, different fiscal year) are dropped, and reviewer wording
   fixes from evals/data/manual_fixes.yaml are applied.
Candidates failing any check are dropped. Survivors are reviewed by hand.

The draft and check prompts are unchanged since the first build: the LLM cache keys on prompt
text, so editing them would regenerate (and pay for) every question.
"""

from __future__ import annotations

import hashlib
import random
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import yaml
from pydantic import BaseModel, Field

from rag_eval.schema import EvalItem, Gold
from rag_eval.text import contains, normalize
from rescue_rag import llm
from rescue_rag.config import project_path
from rescue_rag.corpus import CorpusFiling, filing_sections

ITEM_NAMES = {"1": "Item 1 (Business)", "1A": "Item 1A (Risk Factors)", "7": "Item 7 (MD&A)"}
PAGE_FOOTER_RE = re.compile(r"\|\s*\d{4} Form 10-K\s*\|\s*\d+\s*$", re.I)
PASSAGE_CHARS = 6000
MIN_SECTION_CHARS = 8000


@dataclass(frozen=True)
class Passage:
    filing: CorpusFiling
    item: str
    start: int
    text: str


class DraftQA(BaseModel):
    question: str = Field(description="Self-contained question naming the company and fiscal year")
    answer: str = Field(description="Short, complete reference answer (one or two sentences)")
    evidence_quote: str = Field(description="Exact sentence(s) copied verbatim from the passage")


class CheckQA(BaseModel):
    independent_answer: str
    self_contained: bool = Field(description="Names the company and fiscal year; one clear answer")
    answerable_from_passage: bool
    reference_answer_correct: bool = Field(description="Reference answer is correct and complete")
    issues: str = Field(description="Problems found, or empty")


DRAFT_PROMPT = """You are building an evaluation set for a question-answering system over
SEC 10-K filings.

Below is a passage from {company}'s Form 10-K for fiscal year {fy}, {item_name}.

Write ONE factual question that:
- names the company ("{company}") and the fiscal year ("fiscal year {fy}") explicitly;
- can be answered fully and unambiguously from this passage alone;
- asks for a specific fact (a policy, product, segment, count, named risk, date, business detail),
  not an opinion, summary or "list everything" question;
- would make sense to an analyst who has not seen the passage;
- is not about a headline financial-statement figure (revenue, net income, total assets, EPS,
  cash) - those are covered elsewhere.

Give a short reference answer and copy the supporting sentence(s) from the passage exactly,
character for character, as the evidence quote (at most 400 characters).

<passage>
{passage}
</passage>"""

CHECK_PROMPT = """You are checking one item of an evaluation set built from SEC 10-K filings.

Question: {question}
Proposed reference answer: {answer}

Passage (from {company}'s Form 10-K for fiscal year {fy}):
<passage>
{passage}
</passage>

Answer the question yourself using only the passage. Then judge:
- self_contained: the question names the company and fiscal year and has one clear answer;
- answerable_from_passage: the passage fully answers it;
- reference_answer_correct: the proposed answer is correct and complete per the passage.
List any problems in `issues`."""


CURLY_QUOTES = str.maketrans(
    {chr(0x2019): "'", chr(0x2018): "'", chr(0x201C): '"', chr(0x201D): '"'}
)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.translate(CURLY_QUOTES)).strip().lower()


def sample_passages(filings: list[CorpusFiling], n: int, rng: random.Random) -> list[Passage]:
    """n passages spread over companies and Items 1 / 1A / 7, from paragraph boundaries."""
    pools: dict[str, list[Passage]] = defaultdict(list)
    for f in filings:
        for sec in filing_sections(f):
            if sec.item not in ITEM_NAMES or len(sec.text) < MIN_SECTION_CHARS:
                continue
            # skip the heading region; start at a line break
            lo, hi = 500, len(sec.text) - PASSAGE_CHARS
            for _ in range(2):
                start = rng.randint(lo, hi)
                start = sec.text.find("\n", start) + 1 or start
                pools[f.ticker].append(
                    Passage(f, sec.item, sec.start + start, sec.text[start : start + PASSAGE_CHARS])
                )
    ordered = [rng.sample(p, len(p)) for _, p in sorted(pools.items())]
    out: list[Passage] = []
    used: set[tuple[str, str]] = set()
    while len(out) < n and any(ordered):
        for pool in ordered:
            while pool and len(out) < n:
                p = pool.pop()
                key = (p.filing.key, p.item)  # at most one passage per filing and Item
                if key in used:
                    continue
                used.add(key)
                out.append(p)
                break
    return out


def draft_and_check(
    p: Passage, name: str, generator: str, checker: str
) -> tuple[DraftQA, CheckQA] | str:
    """Returns (draft, check) or a rejection reason."""
    f = p.filing
    try:
        draft = llm.parse(
            generator,
            DRAFT_PROMPT.format(
                company=name, fy=f.fy, item_name=ITEM_NAMES[p.item], passage=p.text
            ),
            DraftQA,
            effort="medium",
        )
    except llm.LLMRefusal as e:
        return f"generator refused: {e}"
    if _norm(draft.evidence_quote) not in _norm(p.text):
        return "evidence quote not verbatim in passage"
    if str(f.fy) not in draft.question or name.split()[0].lower() not in draft.question.lower():
        return "question does not name company and fiscal year"
    try:
        check = llm.parse(
            checker,
            CHECK_PROMPT.format(
                question=draft.question, answer=draft.answer, company=name, fy=f.fy, passage=p.text
            ),
            CheckQA,
            effort="medium",
        )
    except llm.LLMRefusal as e:
        return f"checker refused: {e}"
    if not (check.self_contained and check.answerable_from_passage):
        return f"checker: not self-contained/answerable ({check.issues})"
    if not check.reference_answer_correct:
        return f"checker: reference answer wrong ({check.issues})"
    return draft, check


class EvidenceQuotes(BaseModel):
    quotes: list[str] = Field(
        description="Verbatim excerpts from the passage (sentences or table rows), in order"
    )


class EvidenceCheck(BaseModel):
    supported: bool = Field(description="The quotes alone support the whole answer and premise")
    unsupported_parts: str = Field(description="Answer or premise parts not in the quotes")
    material_wording_issue: bool = Field(
        description="True only if the question is ambiguous, has several correct answers, or "
        "its wording contradicts the evidence (e.g. asks for reasons, evidence gives one)"
    )
    wording_notes: str = Field(description="Wording observations, minor or material; or empty")


EVIDENCE_PROMPT = """Below are a question, its reference answer, and the 10-K passage it came from.

Copy, verbatim from the passage, the excerpts that together support EVERY part of the reference
answer and EVERY premise stated in the question. Include table rows when the answer comes from
a table (copy the row labels and values as they appear). Copy characters exactly; do not
paraphrase, merge or shorten excerpts. Use as few excerpts as needed, but leave nothing out.

Question: {question}
Reference answer: {answer}

<passage>
{passage}
</passage>"""

GROUNDING_CHECK_PROMPT = """You are auditing one item of an evaluation set. You see ONLY the
question, the reference answer and the evidence excerpts - not the rest of the source document.

Provenance (established, do not question it): the excerpts are from {company}'s Form 10-K for
fiscal year {fy}, {item_name}. "We", "our" and "the Company" in them refer to {company}.

Question: {question}
Reference answer: {answer}

Evidence excerpts:
{quotes}

Taking the provenance as given, decide whether the excerpts ALONE support every factual claim
in the reference answer and every factual premise in the question (for example, that a figure
belongs to a particular segment, or that a cause applies to a particular product). Content not
stated in the excerpts counts as unsupported, even if it is probably true.

Separately, set material_wording_issue only if the question is ambiguous, could have more than
one correct answer, or its wording contradicts the evidence (e.g. it asks for several reasons
and the evidence gives one). Minor style points go in wording_notes only."""


def ground(p: Passage, draft: DraftQA, name: str, generator: str, checker: str) -> list[str] | str:
    """Verbatim evidence that alone supports the answer, or a rejection reason."""
    try:
        ev = llm.parse(
            generator,
            EVIDENCE_PROMPT.format(question=draft.question, answer=draft.answer, passage=p.text),
            EvidenceQuotes,
            effort="medium",
        )
    except llm.LLMRefusal as e:
        return f"evidence extraction refused: {e}"
    # Page footers ("Apple Inc. | 2023 Form 10-K | 13") repeat on every page, so they would
    # make any retrieved chunk look like a hit; they never support an answer anyway.
    quotes = [normalize(q) for q in ev.quotes if q.strip() and not PAGE_FOOTER_RE.search(q)]
    if not quotes:
        return "no evidence quotes"
    if any(not contains(p.text, q) for q in quotes):
        return "evidence quote not verbatim in passage"
    try:
        check = llm.parse(
            checker,
            GROUNDING_CHECK_PROMPT.format(
                company=name,
                fy=p.filing.fy,
                item_name=ITEM_NAMES[p.item],
                question=draft.question,
                answer=draft.answer,
                quotes="\n".join(f"- {q}" for q in quotes),
            ),
            EvidenceCheck,
            effort="medium",
        )
    except llm.LLMRefusal as e:
        return f"grounding check refused: {e}"
    if not check.supported:
        return f"evidence does not support answer ({check.unsupported_parts})"
    if check.material_wording_issue:
        return f"wording issue ({check.wording_notes})"
    return quotes


def _dedupe_key(ticker: str, question: str) -> str:
    """Same company + same question apart from the years -> same key."""
    return ticker + "|" + re.sub(r"\b(19|20)\d{2}\b", "Y", normalize(question).lower())


def load_manual_fixes() -> dict[str, dict]:
    """Reviewer fixes (reword or drop), keyed by the normalised generated question text."""
    path = project_path("evals/data/manual_fixes.yaml")
    if not path.exists():
        return {}
    rows = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return {normalize(r["question"]): r for r in rows}


def stable_id(p: Passage, generated_question: str) -> str:
    """Content-derived id: survives drops and re-ordering (reviewer round 2)."""
    digest = hashlib.sha1(
        f"{p.filing.accession}|{p.item}|{normalize(generated_question)}".encode()
    ).hexdigest()
    return f"text-{digest[:6]}"


def text_questions(
    filings: list[CorpusFiling],
    names: dict[str, str],
    n: int,
    n_candidates: int,
    generator: str,
    checker: str,
    rng: random.Random,
    workers: int = 4,
) -> tuple[list[EvalItem], list[str]]:
    passages = sample_passages(filings, n_candidates, rng)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(
            pool.map(
                lambda p: draft_and_check(p, names[p.filing.ticker], generator, checker), passages
            )
        )
    items: list[EvalItem] = []
    log: list[str] = []
    per_company: dict[str, int] = defaultdict(int)
    seen: set[str] = set()
    cap = -(-n // len(names)) + 1  # keep the mix balanced across companies
    fixes = load_manual_fixes()
    used_fixes: set[str] = set()

    pending = []
    for p, r in zip(passages, results, strict=True):
        if isinstance(r, str):
            log.append(f"{p.filing.key} Item {p.item}: rejected - {r}")
        else:
            pending.append((p, r))

    # Grounding runs lazily in small parallel batches: we only pay for as many as needed.
    batch_size = 8
    for start in range(0, len(pending), batch_size):
        if len(items) == n:
            for p, _ in pending[start:]:
                log.append(f"{p.filing.key} Item {p.item}: valid draft, not needed")
            break
        batch: list[tuple[Passage, tuple[DraftQA, CheckQA], str]] = []
        for p, r in pending[start : start + batch_size]:
            label = f"{p.filing.key} Item {p.item}"
            key = _dedupe_key(p.filing.ticker, r[0].question)
            fix = fixes.get(normalize(r[0].question), {})
            if fix.get("drop"):
                used_fixes.add(normalize(r[0].question))
                log.append(f"{label}: dropped by reviewer - {fix.get('reason', '')}")
            elif key in seen or any(key == b[2] for b in batch):
                log.append(f"{label}: dropped - near-duplicate of an earlier question")
            elif per_company[p.filing.ticker] >= cap:
                log.append(f"{label}: valid draft, company cap reached")
            else:
                batch.append((p, r, key))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            grounded = list(
                pool.map(
                    lambda b: ground(b[0], b[1][0], names[b[0].filing.ticker], generator, checker),
                    batch,
                )
            )
        for (p, (draft, check), key), quotes in zip(batch, grounded, strict=True):
            label = f"{p.filing.key} Item {p.item}"
            if isinstance(quotes, str):
                log.append(f"{label}: rejected - {quotes}")
                continue
            if len(items) == n or per_company[p.filing.ticker] >= cap:
                log.append(f"{label}: grounded, not needed")
                continue
            question = draft.question
            if "new_question" in fixes.get(normalize(question), {}):
                used_fixes.add(normalize(question))
                question = fixes[normalize(question)]["new_question"]
            seen.add(key)
            per_company[p.filing.ticker] += 1
            items.append(
                EvalItem(
                    id=stable_id(p, draft.question),
                    type="factual_text",
                    question=question,
                    answer=draft.answer,
                    gold=Gold(
                        tickers=[p.filing.ticker],
                        fiscal_years=[p.filing.fy],
                        accessions=[p.filing.accession],
                        items=[p.item],
                        evidence=quotes,
                    ),
                    source=f"llm:{generator}+check:{checker}+grounded",
                    notes=f"checker answer: {check.independent_answer}",
                )
            )
    for q in sorted(set(fixes) - used_fixes):
        log.append(f"manual fix not applied (question not selected): {q[:80]}")
    return items, log
