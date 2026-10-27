"""Calculator tool (rescue step S7): arithmetic is done in Python, never by the model.

The model writes a formula over figures copied from the excerpts; this module evaluates it
with a whitelist of AST nodes (numbers, + - * /, parentheses, unary minus) - no names, calls
or attribute access, so nothing in a model output can execute code.
"""

from __future__ import annotations

import ast
import operator
import re

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}
_NUM_IN_EXPR = re.compile(r"\d[\d,]*(?:\.\d+)?")


class CalculatorError(ValueError):
    pass


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))  # type: ignore[operator]
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))  # type: ignore[operator]
    raise CalculatorError(f"unsupported expression element: {type(node).__name__}")


def calculate(expression: str) -> float:
    """Evaluate an arithmetic expression. Thousands separators in numbers are allowed."""
    unicode_minus = chr(0x2212)
    cleaned = re.sub(r"(?<=\d),(?=\d{3})", "", expression.replace(unicode_minus, "-"))
    if len(cleaned) > 200:
        raise CalculatorError("expression too long")
    try:
        tree = ast.parse(cleaned, mode="eval")
        return _eval(tree)
    except (SyntaxError, ZeroDivisionError) as e:
        raise CalculatorError(str(e)) from e


def input_numbers(expression: str) -> list[float]:
    """The literal figures used in a formula (to check they appear in the cited excerpts)."""
    return [float(n.replace(",", "")) for n in _NUM_IN_EXPR.findall(expression)]
