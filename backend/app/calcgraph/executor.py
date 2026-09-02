from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from app.calculator.modules import age, arithmetic, finance, statistics, units

from .models import CalcGraph, CalcNode
from .verifier import verify_graph


CALCGRAPH_ENGINE_VERSION = "0.1.0"


def _arithmetic(values: dict[str, Any], _: CalcNode) -> dict:
    return arithmetic.calculate(str(values["expression"]))


def _age(values: dict[str, Any], _: CalcNode) -> dict:
    return age.calculate(f"Calculate the difference from {values['start_date']} to {values['end_date']}")


def _emi(values: dict[str, Any], _: CalcNode) -> dict:
    return finance.calculate(
        f"EMI for INR {values['principal']} at {values['annual_rate']}% for {int(values['tenure'])} months"
    )


def _statistics(values: dict[str, Any], _: CalcNode) -> dict:
    data = ", ".join(str(value) for value in values["values"])
    return statistics.calculate(f"Find mean, median and standard deviation of {data}")


def _units(values: dict[str, Any], node: CalcNode) -> dict:
    return units.calculate(f"Convert {values['quantity']} {values['_quantity_unit']} to {node.unit}")


EXECUTORS: dict[str, Callable[[dict[str, Any], CalcNode], dict]] = {
    "arithmetic.evaluate": _arithmetic,
    "age.difference": _age,
    "finance.emi": _emi,
    "statistics.summary": _statistics,
    "units.convert": _units,
}


def _digest(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def execute_graph(graph: CalcGraph) -> dict[str, Any]:
    report = verify_graph(graph, raise_on_error=True)
    node_map = {node.id: node for node in graph.nodes}
    values: dict[str, Any] = {}
    operation_results: dict[str, dict] = {}

    for node_id in report.topological_order:
        node = node_map[node_id]
        if node.kind == "input":
            values[node.id] = node.value
            continue

        inputs = {name: values[dependency_id] for name, dependency_id in node.inputs.items()}
        if node.operation == "units.convert":
            inputs["_quantity_unit"] = node_map[node.inputs["quantity"]].unit
        result = EXECUTORS[node.operation](inputs, node)
        operation_results[node.id] = result
        values[node.id] = result.get("value", result)

    output_id = graph.output_node_ids[-1]
    calculation = operation_results[output_id]
    graph.status = "executed"
    graph_fingerprint = graph.fingerprint()
    result_digest = _digest(calculation)
    reproducibility_hash = _digest({"graph_fingerprint": graph_fingerprint, "result_digest": result_digest})
    receipt = {
        "receipt_id": str(uuid4()),
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "engine": "CalcGraph reference executor",
        "engine_version": CALCGRAPH_ENGINE_VERSION,
        "graph_fingerprint": graph_fingerprint,
        "result_digest": result_digest,
        "reproducibility_hash": reproducibility_hash,
        "formula_provenance": graph.provenance,
        "verification_summary": {
            "valid": report.valid,
            "checks_passed": sum(check.status == "pass" for check in report.checks),
            "checks_failed": sum(check.status == "fail" for check in report.checks),
        },
    }
    return {
        "calculation": calculation,
        "calcgraph": graph.to_dict(),
        "verification": report.to_dict(),
        "receipt": receipt,
    }
