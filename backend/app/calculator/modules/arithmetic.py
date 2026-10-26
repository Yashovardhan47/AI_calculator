import ast
import math
import operator
import re


OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _evaluate(node: ast.AST) -> float | int:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_evaluate(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("The exponent is too large for an interactive calculation.")
        return OPERATORS[type(node.op)](left, right)
    raise ValueError("Only numbers and standard arithmetic operators are allowed.")


def calculate(query: str) -> dict:
    expression = query.strip().replace("^", "**").replace("×", "*").replace("÷", "/")
    expression = re.sub(
        r"^(please\s+)?(calculate|compute|evaluate|solve|what\s+is)\s*[:=]?\s*",
        "",
        expression,
        flags=re.IGNORECASE,
    ).strip().rstrip("?")
    if not expression:
        raise ValueError("Enter an arithmetic expression, such as (18 + 6) * 4 / 3.")

    parsed = ast.parse(expression, mode="eval")
    value = _evaluate(parsed)
    if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError("The expression did not produce a finite number.")

    rounded = round(value, 12) if isinstance(value, float) else value
    return {
        "title": "Arithmetic result",
        "answer": f"{rounded:,}",
        "value": rounded,
        "unit": None,
        "formula": expression,
        "steps": [f"Normalize the expression: {expression}", f"Evaluate using standard operator precedence: {rounded}"],
        "assumptions": ["The ^ symbol is interpreted as exponentiation."],
        "confidence": 1.0,
    }

