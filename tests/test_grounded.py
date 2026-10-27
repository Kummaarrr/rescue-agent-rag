from rescue_rag.agent.grounded import figure_in, money_figures
from rescue_rag.ingest.chunk import Chunk


def _chunk(text):
    return Chunk("c", text, "X", 2025, "A1")


def test_money_figures_tolerance_follows_stated_precision():
    ((v, tol),) = money_figures("revenue was $19.4 billion")
    assert v == 19.4e9 and abs(tol - 0.05e9) < 1e6


def test_figure_in_matches_across_scales():
    table = _chunk("| Net income attributable to Walmart | 19,436 | 15,511 |")
    v, tol = money_figures("$19.4 billion")[0]
    assert figure_in([table], v, tol)  # 19,436 (millions) ~ $19.4 billion
    v, tol = money_figures("$19,436 million")[0]
    assert figure_in([table], v, tol)
    v, tol = money_figures("about $63.6 billion")[0]  # a figure from memory
    assert not figure_in([table], v, tol)


def test_per_share_figures_match_raw():
    v, tol = money_figures("diluted EPS of $11.93")[0]
    assert figure_in([_chunk("Diluted | $11.93 | $1.74")], v, tol)


def test_calculator_is_exact_and_safe():
    import pytest

    from rescue_rag.agent.tools import CalculatorError, calculate, input_numbers

    assert round(calculate("(130,497 - 60,922) / 60,922 * 100"), 4) == 114.2034
    assert input_numbers("(130497 - 60922) / 60922 * 100") == [130497, 60922, 60922, 100]
    for bad in ["__import__('os').system('x')", "2 ** 1000000", "a + 1", "1 / 0"]:
        with pytest.raises(CalculatorError):
            calculate(bad)
