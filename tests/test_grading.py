from rag_eval.adapters import Context, Response
from rag_eval.grading import Reading, _within, retrieval_hits, to_base_units
from rag_eval.schema import EvalItem, Gold


def _num(answer, tol=0.005, kind="relative", **gold):
    return EvalItem(
        id="n", type="numeric_lookup", question="q", answer=answer, tolerance=tol,
        tolerance_kind=kind, gold=Gold(**gold), source="s",
    )  # fmt: skip


def test_scale_conversion_done_in_code():
    r = Reading(behavior="answered", number_as_written=110543, scale="million", chosen_option=None)
    assert to_base_units(r) == 110_543_000_000
    r = Reading(behavior="answered", number_as_written=416.2, scale="billion", chosen_option=None)
    assert _within(to_base_units(r), _num(416_161_000_000))  # rounding within 0.5%


def test_tolerances():
    assert not _within(420e9, _num(416_161_000_000))
    pct = _num(14.858, tol=0.15, kind="absolute")
    assert _within(14.9, pct) and not _within(15.1, pct)


def test_retrieval_hits_need_gold_filing_and_figure():
    item = _num(1.0, accessions=["A1"], evidence=["416,161"])
    hit = Response("x", contexts=[Context("c1", "Total net sales 416,161", "A1")])
    wrong_doc = Response("x", contexts=[Context("c2", "Total net sales 416,161", "B9")])
    no_fig = Response("x", contexts=[Context("c3", "Total net sales 1,416,161", "A1")])
    assert retrieval_hits(item, hit) == (True, True)
    assert retrieval_hits(item, wrong_doc) == (False, False)
    assert retrieval_hits(item, no_fig) == (True, False)


def test_number_in_text_catches_misreads():
    from rag_eval.grading import number_in_text

    text = "diluted EPS were **$11.93**, up 586% from $1.74; net income $29,760 million"
    assert number_in_text(11.93, text) and number_in_text(29760, text)
    assert not number_in_text(1.19, text)
