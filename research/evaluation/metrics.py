from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import fmean
from typing import Any


@dataclass
class CaseEvaluation:
    case_id: str
    expected_outcome: str
    passed: bool
    detail: str
    calculator_correct: bool | None = None
    reproducible: bool | None = None
    graph_depth: int | None = None
    operation_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _rate(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def summarize(records: list[CaseEvaluation]) -> dict[str, Any]:
    outcomes = {
        name: [record for record in records if record.expected_outcome == name]
        for name in {"success", "clarification", "invalid_graph", "execution_error"}
    }
    executed = [record for record in outcomes["success"] if record.reproducible is not None]
    depths = [record.graph_depth for record in executed if record.graph_depth is not None]
    multi_step = [record for record in executed if (record.operation_count or 0) > 1]
    calculator_records = [record for record in executed if record.calculator_correct is not None]
    return {
        "total_cases": len(records),
        "passed_cases": sum(record.passed for record in records),
        "overall_pass_rate": _rate(sum(record.passed for record in records), len(records)),
        "execution_accuracy": _rate(sum(record.passed for record in outcomes["success"]), len(outcomes["success"])),
        "clarification_accuracy": _rate(
            sum(record.passed for record in outcomes["clarification"]), len(outcomes["clarification"])
        ),
        "invalid_graph_rejection_rate": _rate(
            sum(record.passed for record in outcomes["invalid_graph"]), len(outcomes["invalid_graph"])
        ),
        "unsafe_execution_rejection_rate": _rate(
            sum(record.passed for record in outcomes["execution_error"]), len(outcomes["execution_error"])
        ),
        "calculator_accuracy": _rate(
            sum(record.calculator_correct is True for record in calculator_records), len(calculator_records)
        ),
        "reproducibility_rate": _rate(sum(record.reproducible is True for record in executed), len(executed)),
        "mean_graph_depth": round(fmean(depths), 4) if depths else None,
        "maximum_graph_depth": max(depths) if depths else None,
        "multi_step_case_count": len(multi_step),
    }
