"""Grounded answers with citations and an abstain path (rescue step S8).

Guardrails, in order:
1. No context, no answer: if retrieval found nothing (e.g. a fiscal year or company outside
   the corpus), reply "not found" without calling the model. S4 made this case common, and the
   small model answered it from memory 30% of the time.
2. Structured output: status (answered / not_found / premise_false), the answer, and the
   excerpt ids it relies on. Citations must refer to excerpts that were actually retrieved.
3. Numeric grounding (code, not an LLM): an answer that states dollar figures must have at
   least one of them present in a cited excerpt (precision-aware, any of ones / thousands /
   millions / billions). Answers whose figures appear nowhere in the evidence - the signature
   of an answer from memory - become "not found". Computed figures (differences, growth
   rates) are allowed as long as the answer is anchored in at least one cited figure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from rescue_rag import llm
from rescue_rag.agent.tools import CalculatorError, calculate, input_numbers
from rescue_rag.ingest.chunk import Chunk

Status = Literal["answered", "not_found", "premise_false"]

SYSTEM = """You answer questions about companies' SEC 10-K annual reports using ONLY the numbered
excerpts provided with each question.

Rules:
- Use only facts stated in the excerpts. Never use outside or general knowledge, even when you
  are confident; if a fact is not in the excerpts, it is not available.
- Cite the excerpts that support each claim inline, like [C3], and list their ids.
- If the excerpts do not contain the answer, set status to "not_found" and say briefly what is
  missing.
- If the excerpts contradict the question's premise (for example it assumes a decline that did
  not happen, or an event that never occurred), set status to "premise_false" and explain,
  citing the excerpts.
- For calculations, state the input figures (with citations) and the result.
- Be concise."""

USER = """Excerpts:

{excerpts}

Question: {question}"""

NOT_FOUND_EMPTY = "Not found in the filings: no relevant filing in the corpus covers this question."


class GroundedAnswer(BaseModel):
    status: Status
    answer: str = Field(description="The answer with inline citations like [C2]")
    citations: list[str] = Field(description="Ids of the excerpts relied on, e.g. ['C2', 'C5']")


class Calculation(BaseModel):
    expression: str = Field(
        description="Formula over figures copied exactly from the excerpts, using only numbers, "
        "+ - * / and parentheses, e.g. '(130497 - 60922) / 60922 * 100'"
    )
    result_label: str = Field(description="What the result is, e.g. 'percent change'")
    is_percent: bool


class GroundedAnswerCalc(GroundedAnswer):
    calculation: Calculation | None = Field(
        description="Set when the question needs arithmetic; the system computes the result"
    )


CALC_RULE = """
- Do not do arithmetic yourself. If the question needs a calculation (growth rate, margin,
  difference, ratio), put the formula in `calculation.expression` using the input figures
  exactly as they appear in the excerpts (no units, no rounding) and say in the answer which
  figures you used, with citations. The system computes the result and adds it to your answer;
  do not state the result yourself."""


@dataclass
class Grounded:
    text: str
    status: Status
    citations: list[str]  # chunk ids
    guardrail: str  # which guardrail decided the outcome, "" if the model's answer stood
    call: llm.CallInfo | None


_MONEY_RE = re.compile(r"\$\s?(\d[\d,]*(?:\.\d+)?)\s*(thousand|million|billion|trillion)?", re.I)
_NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
_SCALES = {None: 1.0, "thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12}
_CITE_RE = re.compile(r"\[C(\d+)\]")


def money_figures(text: str) -> list[tuple[float, float]]:
    """(value in dollars, tolerance in dollars) for each $-figure; tolerance = half a unit of the
    last stated digit, so '$19.4 billion' tolerates +/- $0.05 billion."""
    out = []
    for num, scale_word in _MONEY_RE.findall(text):
        scale = _SCALES[scale_word.lower() if scale_word else None]
        decimals = len(num.split(".")[1]) if "." in num else 0
        value = float(num.replace(",", "")) * scale
        out.append((value, 0.5 * 10**-decimals * scale + 1e-6 * value))
    return out


def figure_in(chunks: list[Chunk], value: float, tol: float) -> bool:
    for c in chunks:
        for raw in _NUMBER_RE.findall(c.text):
            n = float(raw.replace(",", ""))
            if any(abs(n * s - value) <= tol for s in (1.0, 1e3, 1e6, 1e9)):
                return True
    return False


def answer(
    question: str,
    hits: list[Chunk],
    model: str,
    calculator: bool = False,
    api_key: str | None = None,
) -> Grounded:
    if not hits:
        return Grounded(NOT_FOUND_EMPTY, "not_found", [], "empty_context", None)

    labels = {f"C{i}": c for i, c in enumerate(hits, start=1)}
    excerpts = "\n\n".join(f"[{label}] {c.text}" for label, c in labels.items())
    schema: type[GroundedAnswer] = GroundedAnswerCalc if calculator else GroundedAnswer
    system = SYSTEM + CALC_RULE if calculator else SYSTEM
    out, call = llm.parse_full(
        model,
        USER.format(excerpts=excerpts, question=question),
        schema,
        system=system,
        api_key=api_key,
    )
    cited_labels = dict.fromkeys([*out.citations, *(f"C{n}" for n in _CITE_RE.findall(out.answer))])
    cited = [labels[label] for label in cited_labels if label in labels]

    if out.status == "not_found":
        return Grounded(f"Not found in the filings: {out.answer}", "not_found", [], "", call)
    if out.status == "premise_false":
        text = f"The filings do not support the question's premise: {out.answer}"
        return Grounded(text, "premise_false", [c.chunk_id for c in cited], "", call)

    if not cited:
        return Grounded(
            "Not found in the filings: the answer could not be tied to any excerpt.",
            "not_found", [], "no_citation", call,
        )  # fmt: skip
    figures = money_figures(out.answer)
    if figures and not any(figure_in(cited, v, tol) for v, tol in figures):
        return Grounded(
            "Not found in the filings: the figures in the draft answer do not appear in the "
            "cited excerpts.",
            "not_found", [], "numeric_grounding", call,
        )  # fmt: skip
    text = out.answer
    calc = getattr(out, "calculation", None)
    if calc is not None:
        # S7: every input figure must come from a cited excerpt; the result is computed in code
        missing = [n for n in input_numbers(calc.expression) if not figure_in(cited, n, 1e-9)]
        if missing and not all(n in (100, 1000, 1e6) for n in missing):  # allow unit constants
            return Grounded(
                "Not found in the filings: the calculation uses figures that are not in the "
                "cited excerpts.",
                "not_found", [], "calculator_inputs", call,
            )  # fmt: skip
        try:
            result = calculate(calc.expression)
        except CalculatorError:
            pass  # keep the model's answer; the numeric check above still applied
        else:
            shown = f"{result:,.2f}%" if calc.is_percent else f"{result:,.4g}"
            line = f"Calculation ({calc.result_label}): {calc.expression} = {shown}"
            text = "\n\n".join([text, line])
    return Grounded(text, "answered", [c.chunk_id for c in cited], "", call)
