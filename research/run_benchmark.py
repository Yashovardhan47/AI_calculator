from __future__ import annotations

import json
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.calcgraph import ClarificationNeeded, compile_query, execute_graph, verify_graph  # noqa: E402


def run_case(case: dict) -> tuple[bool, str]:
    expected = case["expected"]
    outcome = expected.get("outcome", "success")
    try:
        graph = compile_query(case["query"], case.get("calculator"))
    except ClarificationNeeded as exc:
        return outcome == "clarification" and bool(exc.questions), f"clarification: {'; '.join(exc.questions)}"

    report = verify_graph(graph)
    if outcome == "invalid_graph":
        return not report.valid, report.errors[0] if report.errors else "graph was accepted"
    if not report.valid:
        return False, report.errors[0]

    try:
        execution = execute_graph(graph)
    except (SyntaxError, TypeError, ValueError, ZeroDivisionError, OverflowError) as exc:
        return outcome == "execution_error", f"execution error: {exc}"

    if outcome != "success":
        return False, f"expected {outcome}, but execution succeeded"
    result = execution["calculation"]
    if graph.calculator != expected["calculator"]:
        return False, f"calculator {graph.calculator} != {expected['calculator']}"
    tolerance = expected.get("tolerance", 1e-9)
    correct = math.isclose(float(result["value"]), float(expected["value"]), abs_tol=tolerance, rel_tol=tolerance)
    return correct, f"value={result['value']} hash={execution['receipt']['reproducibility_hash'][:12]}"


def main() -> int:
    cases = json.loads((ROOT / "research" / "benchmark" / "sample_cases.json").read_text())
    passed = 0
    for case in cases:
        success, detail = run_case(case)
        passed += success
        print(f"{'PASS' if success else 'FAIL'}  {case['id']}: {detail}")
    print(f"\n{passed}/{len(cases)} benchmark cases passed")
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
