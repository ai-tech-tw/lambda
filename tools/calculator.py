"""Safe arithmetic evaluation tool."""

import ast
import operator
from collections.abc import Callable


BinaryOperator = Callable[[float, float], float]
UnaryOperator = Callable[[float], float]


_ALLOWED_BIN_OPS: dict[type[ast.operator], BinaryOperator] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_ALLOWED_UNARY_OPS: dict[type[ast.unaryop], UnaryOperator] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_ast(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        value = node.value
        if isinstance(value, bool):
            raise ValueError("Booleans are not supported")
        if isinstance(value, (int, float)):
            return float(value)
        raise ValueError(f"Unsupported constant type: {type(value).__name__}")

    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BIN_OPS:
        left = _eval_ast(node.left)
        right = _eval_ast(node.right)
        return _ALLOWED_BIN_OPS[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY_OPS:
        value = _eval_ast(node.operand)
        return _ALLOWED_UNARY_OPS[type(node.op)](value)

    raise ValueError(f"Unsupported expression node: {type(node).__name__}")


def evaluate_expression(expression: str) -> str:
    """Evaluate a math expression safely, e.g. '(4*4*(33/22)+12-20)'."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_ast(tree.body)
    except Exception as exc:
        return f"Error: {exc}"

    formatted = f"{result:.10f}".rstrip("0").rstrip(".")
    return formatted or "0"
