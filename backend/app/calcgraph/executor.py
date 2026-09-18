from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any, Callable
from uuid import uuid4

from app.calculator.modules import age, arithmetic, finance, statistics, units

from .models import CalcGraph, CalcNode
from .verifier import verify_graph


CALCGRAPH_ENGINE_VERSION = "0.2.0"


OperationOutcome = tuple[dict[str, Any], Any]


def _arithmetic(values: dict[str, Any], _: CalcNode) -> OperationOutcome:
    result = arithmetic.calculate(str(values["expression"]))
    return result, result["value"]


def _age(values: dict[str, Any], _: CalcNode) -> OperationOutcome:
    result = age.calculate(f"Calculate the difference from {values['start_date']} to {values['end_date']}")
    return result, result["value"]


def _emi(values: dict[str, Any], _: CalcNode) -> OperationOutcome:
    result = finance.calculate(
        f"EMI for INR {values['principal']} at {values['annual_rate']}% for {int(values['tenure'])} months"
    )
    principal = float(values["principal"])
    annual_rate = float(values["annual_rate"])
    tenure = int(values["tenure"])
    monthly_rate = annual_rate / 12 / 100
    if monthly_rate == 0:
        machine_value = principal / tenure
    else:
        factor = math.pow(1 + monthly_rate, tenure)
        machine_value = principal * monthly_rate * factor / (factor - 1)
    return result, machine_value


def _total_payment(values: dict[str, Any], _: CalcNode) -> OperationOutcome:
    total = float(values["monthly_payment"]) * int(values["tenure"])
    rounded = round(total, 2)
    result = {
        "title": "Total loan payment",
        "answer": f"₹{rounded:,.2f}",
        "value": rounded,
        "unit": "INR",
        "formula": "total payment = monthly payment × number of monthly payments",
        "steps": [
            f"Use the verified monthly payment ₹{values['monthly_payment']:,.6f}.",
            f"Multiply by {int(values['tenure'])} monthly payments: ₹{rounded:,.2f}.",
        ],
        "assumptions": ["Every scheduled monthly payment is made without fees or prepayments."],
        "confidence": 1.0,
    }
    return result, total


def _total_interest(values: dict[str, Any], _: CalcNode) -> OperationOutcome:
    interest = float(values["total_payment"]) - float(values["principal"])
    rounded = round(interest, 2)
    result = {
        "title": "Total loan interest",
        "answer": f"₹{rounded:,.2f}",
        "value": rounded,
        "unit": "INR",
        "formula": "total interest = total payment − principal",
        "steps": [
            f"Total payment = ₹{values['total_payment']:,.2f}.",
            f"Subtract principal ₹{values['principal']:,.2f}: ₹{rounded:,.2f}.",
        ],
        "assumptions": ["The principal excludes processing fees and insurance charges."],
        "confidence": 1.0,
    }
    return result, interest


def _interest_share(values: dict[str, Any], _: CalcNode) -> OperationOutcome:
    total_payment = float(values["total_payment"])
    share = float(values["total_interest"]) / total_payment * 100 if total_payment else 0.0
    rounded = round(share, 4)
    result = {
        "title": "Interest share",
        "answer": f"{rounded:.4f}% of total repayment",
        "value": rounded,
        "unit": "percent",
        "formula": "interest share = total interest ÷ total payment × 100",
        "steps": [
            f"Divide total interest ₹{values['total_interest']:,.2f} by total payment ₹{total_payment:,.2f}.",
            f"Multiply by 100: {rounded:.4f}%.",
        ],
        "assumptions": ["The percentage is measured against total scheduled repayment."],
        "confidence": 1.0,
    }
    return result, share


def _statistics(values: dict[str, Any], _: CalcNode) -> OperationOutcome:
    data = ", ".join(str(value) for value in values["values"])
    result = statistics.calculate(f"Find mean, median and standard deviation of {data}")
    return result, result["metadata"]


def _units(values: dict[str, Any], node: CalcNode) -> OperationOutcome:
    result = units.calculate(f"Convert {values['quantity']} {values['_quantity_unit']} to {node.unit}")
    return result, result["value"]


EXECUTORS: dict[str, Callable[[dict[str, Any], CalcNode], OperationOutcome]] = {
    "arithmetic.evaluate": _arithmetic,
    "age.difference": _age,
    "finance.emi": _emi,
    "finance.total_payment": _total_payment,
    "finance.total_interest": _total_interest,
    "finance.interest_share": _interest_share,
    "statistics.summary": _statistics,
    "units.convert": _units,
}


def _aggregate_outputs(graph: CalcGraph, operation_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    outputs = [operation_results[node_id] for node_id in graph.output_node_ids]
    if len(outputs) == 1:
        return outputs[0]

    assumptions: list[str] = []
    steps: list[str] = []
    for output in outputs:
        for assumption in output.get("assumptions", []):
            if assumption not in assumptions:
                assumptions.append(assumption)
        steps.extend(f"{output['title']}: {step}" for step in output.get("steps", []))
    return {
        "title": "Verified multi-step loan analysis",
        "answer": "; ".join(f"{output['title']}: {output['answer']}" for output in outputs),
        "value": [output["value"] for output in outputs],
        "unit": None,
        "formula": " → ".join(output["formula"] for output in outputs),
        "steps": steps,
        "assumptions": assumptions,
        "confidence": min(float(output.get("confidence", 1.0)) for output in outputs),
        "metadata": {
            "output_node_ids": graph.output_node_ids,
            "outputs": {node_id: operation_results[node_id] for node_id in graph.output_node_ids},
        },
    }


def _graph_depth(graph: CalcGraph, topological_order: list[str]) -> int:
    nodes = {node.id: node for node in graph.nodes}
    depths: dict[str, int] = {}
    for node_id in topological_order:
        node = nodes[node_id]
        if node.kind == "input":
            depths[node_id] = 0
        else:
            depths[node_id] = 1 + max((depths[dependency] for dependency in node.inputs.values()), default=0)
    return max(depths.values(), default=0)


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
        result, machine_value = EXECUTORS[node.operation](inputs, node)
        operation_results[node.id] = result
        values[node.id] = machine_value

    calculation = _aggregate_outputs(graph, operation_results)
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
        "graph_metrics": {
            "node_count": len(graph.nodes),
            "operation_count": sum(node.kind == "operation" for node in graph.nodes),
            "graph_depth": _graph_depth(graph, report.topological_order),
            "output_count": len(graph.output_node_ids),
        },
    }
    return {
        "calculation": calculation,
        "calcgraph": graph.to_dict(),
        "verification": report.to_dict(),
        "receipt": receipt,
        "node_results": operation_results,
    }
