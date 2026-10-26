from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.calcgraph import ClarificationNeeded, compile_query, execute_graph, verify_graph  # noqa: E402
from evaluation.metrics import CaseEvaluation, summarize  # noqa: E402


def _close(actual: float, expected: float, tolerance: float) -> bool:
    return math.isclose(float(actual), float(expected), abs_tol=tolerance, rel_tol=tolerance)


def run_case(case: dict) -> CaseEvaluation:
    expected = case["expected"]
    outcome = expected.get("outcome", "success")
    try:
        graph = compile_query(case["query"], case.get("calculator"))
    except ClarificationNeeded as exc:
        passed = outcome == "clarification" and bool(exc.questions)
        return CaseEvaluation(case["id"], outcome, passed, f"clarification: {'; '.join(exc.questions)}")

    report = verify_graph(graph)
    if outcome == "invalid_graph":
        return CaseEvaluation(
            case["id"], outcome, not report.valid, report.errors[0] if report.errors else "graph was accepted"
        )
    if not report.valid:
        return CaseEvaluation(case["id"], outcome, False, report.errors[0])

    try:
        execution = execute_graph(graph)
        repeated = execute_graph(compile_query(case["query"], case.get("calculator")))
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError, OverflowError) as exc:
        return CaseEvaluation(case["id"], outcome, outcome == "execution_error", f"execution error: {exc}")

    metrics = execution["receipt"]["graph_metrics"]
    reproducible = execution["receipt"]["reproducibility_hash"] == repeated["receipt"]["reproducibility_hash"]
    calculator_correct = graph.calculator == expected.get("calculator", graph.calculator)
    checks = [calculator_correct, reproducible]
    tolerance = expected.get("tolerance", 1e-9)

    if "value" in expected:
        checks.append(_close(execution["calculation"]["value"], expected["value"], tolerance))
    if "output_values" in expected:
        for node_id, expected_value in expected["output_values"].items():
            actual = execution["node_results"].get(node_id, {}).get("value")
            checks.append(actual is not None and _close(actual, expected_value, tolerance))
    if "operation_count" in expected:
        checks.append(metrics["operation_count"] == expected["operation_count"])
    if "graph_depth" in expected:
        checks.append(metrics["graph_depth"] == expected["graph_depth"])
    if outcome != "success":
        checks.append(False)

    passed = all(checks)
    detail = (
        f"operations={metrics['operation_count']} depth={metrics['graph_depth']} "
        f"hash={execution['receipt']['reproducibility_hash'][:12]}"
    )
    return CaseEvaluation(
        case["id"],
        outcome,
        passed,
        detail,
        calculator_correct=calculator_correct,
        reproducible=reproducible,
        graph_depth=metrics["graph_depth"],
        operation_count=metrics["operation_count"],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CalcGraphBench and report research metrics.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=ROOT / "research" / "benchmark" / "sample_cases.json",
    )
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    cases = json.loads(args.dataset.read_text(encoding="utf-8"))
    records = [run_case(case) for case in cases]
    for record in records:
        print(f"{'PASS' if record.passed else 'FAIL'}  {record.case_id}: {record.detail}")

    metrics = summarize(records)
    print("\nCalcGraphBench metrics")
    for name, value in metrics.items():
        print(f"  {name}: {value}")

    if args.json_output:
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dataset": str(args.dataset),
            "metrics": metrics,
            "cases": [record.to_dict() for record in records],
        }
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Saved JSON report to {args.json_output}")

    return 0 if metrics["passed_cases"] == metrics["total_cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
