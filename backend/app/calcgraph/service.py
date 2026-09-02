from __future__ import annotations

from .compiler import compile_query
from .executor import execute_graph


def calculate_with_graph(query: str, calculator_hint: str | None = None) -> dict:
    graph = compile_query(query, calculator_hint)
    execution = execute_graph(graph)
    calculation = execution.pop("calculation")
    metadata = calculation.setdefault("metadata", {})
    metadata.update(
        {
            "calcgraph_version": graph.version,
            "graph_id": graph.graph_id,
            "graph_fingerprint": execution["receipt"]["graph_fingerprint"],
        }
    )
    return {
        "request_id": execution["receipt"]["receipt_id"],
        "query": query,
        "calculator": graph.calculator,
        **calculation,
        **execution,
    }
