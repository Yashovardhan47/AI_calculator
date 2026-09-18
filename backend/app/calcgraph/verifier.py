from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any

from app.calculator.modules import units

from .formulas import FORMULA_REGISTRY, formula_provenance
from .models import CALCGRAPH_VERSION, CalcGraph, CalcNode
from .typesystem import TYPE_SYSTEM_VERSION, is_assignable, is_registered, value_matches


CALCULATOR_OPERATIONS = {
    "arithmetic": {"arithmetic.evaluate"},
    "age": {"age.difference"},
    "emi": {
        "finance.emi",
        "finance.total_payment",
        "finance.total_interest",
        "finance.interest_share",
    },
    "statistics": {"statistics.summary"},
    "units": {"units.convert"},
}


@dataclass
class ValidationCheck:
    id: str
    status: str
    message: str
    node_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationReport:
    valid: bool
    checks: list[ValidationCheck] = field(default_factory=list)
    topological_order: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "checks": [check.to_dict() for check in self.checks],
            "topological_order": self.topological_order,
            "errors": self.errors,
        }


class GraphVerificationError(ValueError):
    def __init__(self, report: VerificationReport):
        super().__init__(report.errors[0] if report.errors else "CalcGraph verification failed.")
        self.report = report


def _contains_non_finite(value: Any) -> bool:
    if isinstance(value, float):
        return not math.isfinite(value)
    if isinstance(value, list):
        return any(_contains_non_finite(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_non_finite(item) for item in value.values())
    return False


def _unit_dimension(unit: str | None) -> str | None:
    if unit in units.TEMPERATURES:
        return "temperature"
    if unit in units.UNITS:
        return units.UNITS[unit][0]
    return None


def _topological_order(nodes: dict[str, CalcNode]) -> tuple[list[str], list[str]]:
    order: list[str] = []
    errors: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> None:
        if node_id in visited:
            return
        if node_id in visiting:
            errors.append(f"Cycle detected at node '{node_id}'.")
            return
        visiting.add(node_id)
        node = nodes[node_id]
        for dependency in node.inputs.values():
            if dependency in nodes:
                visit(dependency)
        visiting.remove(node_id)
        visited.add(node_id)
        order.append(node_id)

    for node_id in nodes:
        visit(node_id)
    return order, errors


def verify_graph(graph: CalcGraph, raise_on_error: bool = False) -> VerificationReport:
    checks: list[ValidationCheck] = []
    errors: list[str] = []

    def record(check_id: str, valid: bool, message: str, node_id: str | None = None) -> None:
        checks.append(ValidationCheck(check_id, "pass" if valid else "fail", message, node_id))
        if not valid:
            errors.append(message)

    record(
        "graph.version",
        graph.version == CALCGRAPH_VERSION,
        f"Graph IR version must be {CALCGRAPH_VERSION}; received {graph.version}.",
    )
    record(
        "graph.type_system_version",
        graph.type_system_version == TYPE_SYSTEM_VERSION,
        f"Semantic type-system version must be {TYPE_SYSTEM_VERSION}; received {graph.type_system_version}.",
    )

    node_ids = [node.id for node in graph.nodes]
    unique_ids = len(node_ids) == len(set(node_ids))
    record("graph.unique_nodes", unique_ids, "Every CalcGraph node must have a unique identifier.")
    nodes = {node.id: node for node in graph.nodes}

    for node in graph.nodes:
        kind_valid = node.kind in {"input", "operation"}
        record(
            "node.kind",
            kind_valid,
            f"Node '{node.id}' has a supported kind." if kind_valid else f"Node '{node.id}' has unsupported kind '{node.kind}'.",
            node.id,
        )
        finite = not _contains_non_finite(node.value)
        record(
            "node.finite",
            finite,
            f"Node '{node.id}' contains only finite numeric values."
            if finite
            else f"Node '{node.id}' contains a non-finite numeric value.",
            node.id,
        )
        semantic_type_valid = is_registered(node.semantic_type)
        record(
            "node.semantic_type_registered",
            semantic_type_valid,
            f"Node '{node.id}' uses registered semantic type '{node.semantic_type}'."
            if semantic_type_valid
            else f"Node '{node.id}' uses unknown semantic type '{node.semantic_type}'.",
            node.id,
        )

        if node.kind == "input":
            record(
                "input.no_operation",
                not node.operation and not node.inputs,
                f"Input node '{node.id}' cannot declare an operation or dependencies.",
                node.id,
            )
            value_type_valid = semantic_type_valid and value_matches(node.semantic_type, node.value)
            record(
                "input.value_type",
                value_type_valid,
                f"Input node '{node.id}' value conforms to semantic type '{node.semantic_type}'."
                if value_type_valid
                else f"Input node '{node.id}' value does not conform to semantic type '{node.semantic_type}'.",
                node.id,
            )
            continue

        operation_valid = node.operation in FORMULA_REGISTRY
        record(
            "operation.allowlist",
            operation_valid,
            f"Node '{node.id}' operation '{node.operation}' is registered in the formula allowlist."
            if operation_valid
            else f"Node '{node.id}' operation '{node.operation}' is not in the formula allowlist.",
            node.id,
        )
        if not operation_valid:
            continue

        signature = FORMULA_REGISTRY[node.operation]
        domain_valid = node.operation in CALCULATOR_OPERATIONS.get(graph.calculator, set())
        record(
            "operation.domain",
            domain_valid,
            f"Operation '{node.operation}' belongs to calculator domain '{graph.calculator}'."
            if domain_valid
            else f"Operation '{node.operation}' is not registered for calculator domain '{graph.calculator}'.",
            node.id,
        )
        formula_metadata_valid = (
            node.metadata.get("formula_id") == signature["formula_id"]
            and node.metadata.get("formula_version") == signature["version"]
        )
        record(
            "operation.formula_version",
            formula_metadata_valid,
            f"Node '{node.id}' identifies formula '{signature['formula_id']}' version '{signature['version']}'."
            if formula_metadata_valid
            else f"Node '{node.id}' formula identity does not match the executable registry.",
            node.id,
        )
        expected_provenance = formula_provenance(node.operation)
        provenance_valid = expected_provenance in graph.provenance
        record(
            "operation.provenance",
            provenance_valid,
            f"Node '{node.id}' has complete formula provenance."
            if provenance_valid
            else f"Node '{node.id}' is missing matching formula provenance.",
            node.id,
        )
        expected_inputs = signature["inputs"]
        names_valid = set(node.inputs) == set(expected_inputs)
        record(
            "operation.signature",
            names_valid,
            f"Node '{node.id}' input names match formula '{node.operation}'."
            if names_valid
            else f"Node '{node.id}' input names do not match formula '{node.operation}'.",
            node.id,
        )
        output_valid = node.semantic_type == signature["output"]
        record(
            "operation.output_type",
            output_valid,
            f"Node '{node.id}' output type is '{signature['output']}'.",
            node.id,
        )

        for input_name, dependency_id in node.inputs.items():
            dependency = nodes.get(dependency_id)
            exists = dependency is not None
            record(
                "edge.reference",
                exists,
                f"Input '{input_name}' of node '{node.id}' references an existing node."
                if exists
                else f"Input '{input_name}' of node '{node.id}' references missing node '{dependency_id}'.",
                node.id,
            )
            if exists and input_name in expected_inputs:
                expected_type = expected_inputs[input_name]
                type_valid = is_assignable(dependency.semantic_type, expected_type)
                record(
                    "edge.semantic_type",
                    type_valid,
                    f"Edge '{dependency_id} → {node.id}' carries semantic type '{expected_type}'."
                    if type_valid
                    else f"Edge '{dependency_id} → {node.id}' must carry semantic type '{expected_type}', not '{dependency.semantic_type}'.",
                    node.id,
                )

        if node.operation == "units.convert" and "quantity" in node.inputs:
            source = nodes.get(node.inputs["quantity"])
            source_dimension = _unit_dimension(source.unit) if source else None
            target_dimension = _unit_dimension(node.unit)
            compatible = source_dimension is not None and source_dimension == target_dimension
            record(
                "units.dimension",
                compatible,
                f"Unit conversion dimensions are compatible ({source_dimension} → {target_dimension})."
                if compatible
                else f"Unit conversion dimensions are incompatible ({source_dimension} → {target_dimension}).",
                node.id,
            )

    operation_count_valid = any(node.kind == "operation" for node in graph.nodes)
    record(
        "graph.operation_count",
        operation_count_valid,
        "The graph contains at least one executable operation."
        if operation_count_valid
        else "The graph does not contain an executable operation.",
    )

    for index, constraint in enumerate(graph.constraints):
        constraint_valid = bool(constraint.expression.strip()) and bool(constraint.description.strip())
        severity_valid = constraint.severity in {"error", "warning"}
        record(
            "constraint.structure",
            constraint_valid and severity_valid,
            f"Constraint {index} has an expression, description, and supported severity."
            if constraint_valid and severity_valid
            else f"Constraint {index} is malformed.",
        )
    outputs_valid = bool(graph.output_node_ids) and all(node_id in nodes for node_id in graph.output_node_ids)
    record(
        "graph.outputs",
        outputs_valid,
        "All declared graph outputs reference existing nodes."
        if outputs_valid
        else "The graph must declare at least one existing output node.",
    )
    output_kinds_valid = outputs_valid and all(nodes[node_id].kind == "operation" for node_id in graph.output_node_ids)
    record(
        "graph.output_kinds",
        output_kinds_valid,
        "Every declared graph output is an operation node."
        if output_kinds_valid
        else "Every declared graph output must be an operation node.",
    )

    order, cycle_errors = _topological_order(nodes)
    acyclic = not cycle_errors
    checks.append(ValidationCheck("graph.acyclic", "pass" if acyclic else "fail", "The calculation graph is acyclic." if acyclic else cycle_errors[0]))
    errors.extend(cycle_errors)

    report = VerificationReport(valid=not errors, checks=checks, topological_order=order if acyclic else [], errors=errors)
    if raise_on_error and not report.valid:
        raise GraphVerificationError(report)
    return report
