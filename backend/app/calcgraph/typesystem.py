from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any


TYPE_SYSTEM_VERSION = "0.2.0"


@dataclass(frozen=True)
class SemanticTypeDefinition:
    name: str
    parent: str | None
    description: str
    value_kind: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


TYPE_REGISTRY = {
    definition.name: definition
    for definition in [
        SemanticTypeDefinition("Any", None, "Root semantic value type.", "any"),
        SemanticTypeDefinition("Text", "Any", "Natural-language or symbolic text.", "string"),
        SemanticTypeDefinition("Number", "Any", "Finite real-valued scalar.", "number"),
        SemanticTypeDefinition("Integer", "Number", "Whole-number scalar.", "integer"),
        SemanticTypeDefinition("Percentage", "Number", "Dimensionless value expressed as a percentage.", "number"),
        SemanticTypeDefinition("Probability", "Number", "Dimensionless value in the closed interval [0, 1].", "number"),
        SemanticTypeDefinition("Money", "Number", "Monetary amount with an explicit currency unit.", "number"),
        SemanticTypeDefinition("MoneyPerMonth", "Number", "Monthly monetary rate.", "number"),
        SemanticTypeDefinition("Rate", "Number", "Rate measured over an explicit period.", "number"),
        SemanticTypeDefinition("Duration", "Number", "Elapsed or calendar duration with an explicit unit.", "number"),
        SemanticTypeDefinition("Quantity", "Number", "Dimensioned physical quantity.", "number"),
        SemanticTypeDefinition("Date", "Any", "ISO-8601 calendar date.", "date"),
        SemanticTypeDefinition("Boolean", "Any", "Logical true or false value.", "boolean"),
        SemanticTypeDefinition("NumberSeries", "Any", "Ordered finite series of numbers.", "number_series"),
        SemanticTypeDefinition("Vector", "Any", "One-dimensional numeric vector.", "number_series"),
        SemanticTypeDefinition("Matrix", "Any", "Two-dimensional numeric matrix.", "matrix"),
        SemanticTypeDefinition("StatisticsSummary", "Any", "Structured descriptive-statistics result.", "object"),
        SemanticTypeDefinition("Comparison", "Any", "Structured comparison between alternatives.", "object"),
        SemanticTypeDefinition("Interval", "Any", "Closed numeric interval.", "object"),
        SemanticTypeDefinition("UncertainQuantity", "Any", "Value paired with uncertainty information.", "object"),
        SemanticTypeDefinition("Constraint", "Any", "Machine-verifiable restriction on graph values.", "object"),
    ]
}


def is_registered(type_name: str) -> bool:
    return type_name in TYPE_REGISTRY


def is_assignable(actual: str, expected: str) -> bool:
    """Return whether an actual semantic type may flow into an expected type."""
    if actual == expected or expected == "Any":
        return True
    current = TYPE_REGISTRY.get(actual)
    seen: set[str] = set()
    while current and current.parent and current.name not in seen:
        seen.add(current.name)
        if current.parent == expected:
            return True
        current = TYPE_REGISTRY.get(current.parent)
    return False


def value_matches(type_name: str, value: Any) -> bool:
    definition = TYPE_REGISTRY.get(type_name)
    if definition is None:
        return False
    kind = definition.value_kind
    if kind == "any":
        return True
    if kind == "string":
        return isinstance(value, str)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "date":
        if not isinstance(value, str):
            return False
        try:
            date.fromisoformat(value)
        except ValueError:
            return False
        return True
    if kind == "number_series":
        return isinstance(value, list) and bool(value) and all(
            isinstance(item, (int, float)) and not isinstance(item, bool) for item in value
        )
    if kind == "matrix":
        return isinstance(value, list) and bool(value) and all(
            isinstance(row, list)
            and bool(row)
            and all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in row)
            for row in value
        )
    if kind == "object":
        return isinstance(value, dict)
    return False


def registry_payload() -> dict[str, Any]:
    return {
        "version": TYPE_SYSTEM_VERSION,
        "types": [definition.to_dict() for definition in TYPE_REGISTRY.values()],
    }
