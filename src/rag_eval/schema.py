"""Evaluation dataset records (one JSON object per line in dataset.jsonl)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

QuestionType = Literal[
    "numeric_lookup", "numeric_compute", "comparison", "factual_text", "unanswerable"
]
Split = Literal["dev", "test"]
# What a correct response does. "Unanswerable" means not answerable from the corpus filings
# (the data may well exist elsewhere, e.g. in older 10-Ks that are not in the corpus).
Behavior = Literal["answer", "abstain", "reject_premise"]


class Gold(BaseModel):
    """Where the answer lives. Any listed filing counts as a correct source."""

    tickers: list[str] = Field(default_factory=list)
    fiscal_years: list[int] = Field(default_factory=list)
    accessions: list[str] = Field(default_factory=list)
    items: list[str] = Field(default_factory=list)  # 10-K Items, when known
    # Strings that appear verbatim in the evidence, e.g. "416,161" or a quoted sentence.
    # Retrieval counts as a hit when a retrieved chunk from a gold filing contains one of them.
    evidence: list[str] = Field(default_factory=list)
    # Comparisons: every filing of each company that reports the same figure (a later 10-K
    # repeats the prior year as a comparative). Used for retrieval/citation scoring.
    accessions_by_ticker: dict[str, list[str]] = Field(default_factory=dict)


class EvalItem(BaseModel):
    id: str
    split: Split | None = None
    type: QuestionType
    question: str
    # numeric types: a number; comparison: the winning ticker; factual_text: reference answer;
    # unanswerable: None (the system is expected to abstain).
    answer: float | str | None
    expected_behavior: Behavior = "answer"
    unit: str | None = None  # "USD", "USD/share", "percent"
    tolerance: float | None = None
    tolerance_kind: Literal["relative", "absolute"] | None = None
    gold: Gold = Field(default_factory=Gold)
    source: str  # how the item was made, e.g. "xbrl:NetIncomeLoss" or "llm:claude-opus-5-5"
    notes: str = ""

    @model_validator(mode="after")
    def _check(self) -> EvalItem:
        numeric = self.type in ("numeric_lookup", "numeric_compute")
        if numeric and not isinstance(self.answer, int | float):
            raise ValueError(f"{self.id}: numeric item needs a numeric answer")
        if numeric and (self.tolerance is None or self.tolerance_kind is None):
            raise ValueError(f"{self.id}: numeric item needs a tolerance")
        if self.type == "unanswerable" and self.answer is not None:
            raise ValueError(f"{self.id}: unanswerable item must have answer=None")
        if (self.type == "unanswerable") != (self.expected_behavior != "answer"):
            raise ValueError(f"{self.id}: only unanswerable items abstain or reject a premise")
        if self.type in ("comparison", "factual_text") and not isinstance(self.answer, str):
            raise ValueError(f"{self.id}: {self.type} item needs a string answer")
        return self


def write_jsonl(path: Path, items: list[EvalItem]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for item in items:
            f.write(item.model_dump_json(exclude_none=False) + "\n")


def read_jsonl(path: Path) -> list[EvalItem]:
    with path.open(encoding="utf-8") as f:
        return [EvalItem.model_validate(json.loads(line)) for line in f if line.strip()]
