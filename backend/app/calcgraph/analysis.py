from __future__ import annotations

import hashlib
import itertools
import json
import math
from typing import Any

from .executor import execute_graph
from .models import CalcGraph


MAX_UNCERTAIN_INPUTS = 8
MAX_SCENARIOS = 20
ANALYSIS_VERSION = "1.0.0"


def _digest(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _clone_with_overrides(graph: CalcGraph, overrides: dict[str, float | int]) -> CalcGraph:
    clone = CalcGraph.from_dict(graph.to_dict())
    clone.status = "compiled"
    nodes = {node.id: node for node in clone.nodes}
    for node_id, value in overrides.items():
        node = nodes.get(node_id)
        if node is None or node.kind != "input":
            raise ValueError(f"Override '{node_id}' must reference an existing input node.")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError(f"Override '{node_id}' must be a finite number.")
        if isinstance(node.value, int) and not isinstance(node.value, bool):
            if not float(value).is_integer():
                raise ValueError(f"Override '{node_id}' must remain an integer.")
            node.value = int(value)
        elif isinstance(node.value, float):
            node.value = float(value)
        else:
            raise ValueError(f"Input '{node_id}' is not a scalar numeric input.")
    return clone


def _scalar_outputs(graph: CalcGraph, overrides: dict[str, float | int] | None = None) -> tuple[dict[str, float], dict]:
    execution = execute_graph(_clone_with_overrides(graph, overrides or {}))
    outputs: dict[str, float] = {}
    for node_id in graph.output_node_ids:
        value = execution["node_results"][node_id].get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError(
                f"Analysis requires scalar numeric outputs; output '{node_id}' is not supported."
            )
        outputs[node_id] = float(value)
    return outputs, execution


def _uncertainty_bounds(graph: CalcGraph, specifications: dict[str, dict[str, float]]) -> dict[str, tuple[float, float]]:
    nodes = {node.id: node for node in graph.nodes}
    if len(specifications) > MAX_UNCERTAIN_INPUTS:
        raise ValueError(f"At most {MAX_UNCERTAIN_INPUTS} uncertain inputs are allowed.")
    bounds: dict[str, tuple[float, float]] = {}
    for node_id, specification in specifications.items():
        node = nodes.get(node_id)
        if node is None or node.kind != "input" or isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise ValueError(f"Uncertainty '{node_id}' must reference a scalar numeric input.")
        allowed = {"absolute", "relative_percent"}
        if set(specification) - allowed or len(specification) != 1:
            raise ValueError(
                f"Uncertainty '{node_id}' must contain exactly one of: absolute, relative_percent."
            )
        amount = float(next(iter(specification.values())))
        if not math.isfinite(amount) or amount < 0:
            raise ValueError(f"Uncertainty '{node_id}' must be a finite non-negative number.")
        radius = amount if "absolute" in specification else abs(float(node.value)) * amount / 100
        low, high = float(node.value) - radius, float(node.value) + radius
        if isinstance(node.value, int):
            low, high = math.floor(low), math.ceil(high)
        bounds[node_id] = (low, high)
    return bounds


def analyze_graph(
    graph: CalcGraph,
    uncertainties: dict[str, dict[str, float]] | None = None,
    scenarios: list[dict[str, Any]] | None = None,
    sensitivity_fraction: float = 0.01,
) -> dict[str, Any]:
    """Run bounded uncertainty, local sensitivity, and counterfactual analysis.

    Uncertainty uses deterministic corner enumeration. It is exact for monotonic
    functions over the declared box, but is otherwise a sampled outer-corner
    estimate and is labelled accordingly.
    """
    if not 0 < sensitivity_fraction <= 0.25:
        raise ValueError("sensitivity_fraction must be greater than 0 and at most 0.25.")
    scenarios = scenarios or []
    if len(scenarios) > MAX_SCENARIOS:
        raise ValueError(f"At most {MAX_SCENARIOS} counterfactual scenarios are allowed.")

    baseline, baseline_execution = _scalar_outputs(graph)
    input_nodes = [
        node for node in graph.nodes
        if node.kind == "input"
        and not isinstance(node.value, bool)
        and isinstance(node.value, (int, float))
    ]

    sensitivity: dict[str, dict[str, Any]] = {}
    for node in input_nodes:
        step: float | int = 1 if isinstance(node.value, int) else max(abs(float(node.value)) * sensitivity_fraction, sensitivity_fraction)
        low_value = node.value - step
        high_value = node.value + step
        if isinstance(node.value, int):
            low_value, high_value = int(low_value), int(high_value)
        low_outputs, _ = _scalar_outputs(graph, {node.id: low_value})
        high_outputs, _ = _scalar_outputs(graph, {node.id: high_value})
        derivatives = {
            output_id: (high_outputs[output_id] - low_outputs[output_id]) / (float(high_value) - float(low_value))
            for output_id in baseline
        }
        elasticity = {
            output_id: (
                derivatives[output_id] * float(node.value) / baseline[output_id]
                if baseline[output_id] != 0 else None
            )
            for output_id in baseline
        }
        sensitivity[node.id] = {
            "input_value": node.value,
            "step": step,
            "partial_derivative": derivatives,
            "normalized_elasticity": elasticity,
        }

    bounds = _uncertainty_bounds(graph, uncertainties or {})
    interval_samples: list[dict[str, float]] = []
    if bounds:
        node_ids = list(bounds)
        for corner in itertools.product((0, 1), repeat=len(node_ids)):
            override = {
                node_id: bounds[node_id][choice]
                for node_id, choice in zip(node_ids, corner)
            }
            outputs, _ = _scalar_outputs(graph, override)
            interval_samples.append(outputs)
    else:
        interval_samples.append(baseline)
    intervals = {
        output_id: {
            "lower": min(sample[output_id] for sample in interval_samples),
            "baseline": value,
            "upper": max(sample[output_id] for sample in interval_samples),
        }
        for output_id, value in baseline.items()
    }

    counterfactuals = []
    for index, scenario in enumerate(scenarios):
        name = str(scenario.get("name") or f"scenario-{index + 1}")
        overrides = scenario.get("overrides")
        if not isinstance(overrides, dict) or not overrides:
            raise ValueError(f"Counterfactual '{name}' requires a non-empty overrides object.")
        outputs, _ = _scalar_outputs(graph, overrides)
        counterfactuals.append({
            "name": name,
            "overrides": overrides,
            "outputs": outputs,
            "delta_from_baseline": {
                output_id: outputs[output_id] - baseline[output_id]
                for output_id in baseline
            },
        })

    evidence_payload = {
        "analysis_version": ANALYSIS_VERSION,
        "graph_fingerprint": baseline_execution["receipt"]["graph_fingerprint"],
        "baseline": baseline,
        "uncertainty_intervals": intervals,
        "sensitivity": sensitivity,
        "counterfactuals": counterfactuals,
    }
    return {
        **evidence_payload,
        "method": {
            "uncertainty": "deterministic corner enumeration",
            "sensitivity": "central finite difference",
            "counterfactuals": "verified graph re-execution",
            "corner_samples": len(interval_samples),
        },
        "limitations": [
            "Corner enumeration is not a formal global bound for non-monotonic functions.",
            "Inputs are varied independently; correlations require an external probabilistic model.",
            "Local sensitivity depends on the selected finite-difference step.",
            "Only scalar numeric graph inputs and outputs are analyzed in this version.",
        ],
        "analysis_digest": _digest(evidence_payload),
        "baseline_receipt": baseline_execution["receipt"],
    }
