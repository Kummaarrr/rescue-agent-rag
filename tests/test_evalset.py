import pytest
from pydantic import ValidationError

from rag_eval.schema import EvalItem
from rescue_rag.evalset.xbrl_questions import METRICS, Value, appears_in, evidence_string, plausible


def test_evidence_string_formats():
    assert evidence_string(416_161_000_000, "USD")[0] == "416,161"
    assert evidence_string(-42_012_000_000, "USD")[0] == "42,012"  # negatives print in parens
    assert evidence_string(6.08, "USD/shares") == ["6.08"]


def test_appears_in_respects_number_boundaries():
    assert appears_in("Total net sales $ 416,161 $ 391,035", "416,161")
    assert not appears_in("Total 1,416,161", "416,161")
    assert not appears_in("EPS 16.08", "6.08")
    assert not appears_in("value 6.085", "6.08")


def _value(key, x):
    return Value(filing=None, metric=METRICS[key], value=x, concept="c", period_end="2025-12-31")  # type: ignore[arg-type]


def test_plausibility_catches_mistagged_rnd():
    revenue = 94_200_000_000
    assert not plausible(_value("rnd", 110_000_000), revenue)  # J&J's component-only concept
    assert plausible(_value("rnd", 14_660_000_000), revenue)
    assert plausible(_value("rnd", 1_200_000_000), 332_200_000_000)  # ExxonMobil, genuinely low


def test_schema_rules():
    with pytest.raises(ValidationError):
        EvalItem(id="x", type="numeric_lookup", question="q", answer="text", source="s")
    with pytest.raises(ValidationError):
        EvalItem(id="x", type="unanswerable", question="q", answer="something", source="s")
    ok = EvalItem(
        id="x", type="numeric_lookup", question="q", answer=1.0,
        tolerance=0.005, tolerance_kind="relative", source="s",
    )  # fmt: skip
    assert ok.answer == 1.0
