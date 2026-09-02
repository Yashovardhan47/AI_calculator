from uuid import uuid4

from .modules import age, arithmetic, finance, statistics, units
from .parser import detect_calculator


class CalculationError(ValueError):
    def __init__(self, message: str, calculator: str | None = None):
        super().__init__(message)
        self.calculator = calculator


HANDLERS = {
    "arithmetic": arithmetic.calculate,
    "age": age.calculate,
    "emi": finance.calculate,
    "statistics": statistics.calculate,
    "units": units.calculate,
}


def calculate(query: str, calculator_hint: str | None = None) -> dict:
    normalized_query = query.strip()
    calculator = detect_calculator(normalized_query, calculator_hint)
    handler = HANDLERS.get(calculator)
    if not handler:
        raise CalculationError("That calculator is not available in this release.", calculator)

    try:
        result = handler(normalized_query)
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError, OverflowError) as exc:
        raise CalculationError(str(exc), calculator) from exc

    return {
        "request_id": str(uuid4()),
        "query": normalized_query,
        "calculator": calculator,
        **result,
        "metadata": result.get("metadata", {}),
    }

