from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .typesystem import TYPE_SYSTEM_VERSION


CALCGRAPH_VERSION = "0.2.0"


@dataclass
class CalcNode:
    id: str
    label: str
    kind: str
    semantic_type: str
    unit: str | None = None
    value: Any = None
    operation: str | None = None
    inputs: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CalcNode":
        return cls(**payload)


@dataclass
class CalcConstraint:
    expression: str
    description: str
    severity: str = "error"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CalcGraph:
    goal: str
    calculator: str
    nodes: list[CalcNode]
    output_node_ids: list[str]
    assumptions: list[str] = field(default_factory=list)
    constraints: list[CalcConstraint] = field(default_factory=list)
    provenance: list[dict[str, Any]] = field(default_factory=list)
    graph_id: str = field(default_factory=lambda: str(uuid4()))
    version: str = CALCGRAPH_VERSION
    type_system_version: str = TYPE_SYSTEM_VERSION
    status: str = "compiled"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "version": self.version,
            "type_system_version": self.type_system_version,
            "goal": self.goal,
            "calculator": self.calculator,
            "status": self.status,
            "created_at": self.created_at,
            "nodes": [node.to_dict() for node in self.nodes],
            "output_node_ids": self.output_node_ids,
            "assumptions": self.assumptions,
            "constraints": [constraint.to_dict() for constraint in self.constraints],
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CalcGraph":
        return cls(
            graph_id=payload.get("graph_id", str(uuid4())),
            version=payload.get("version", CALCGRAPH_VERSION),
            type_system_version=payload.get("type_system_version", TYPE_SYSTEM_VERSION),
            goal=payload["goal"],
            calculator=payload["calculator"],
            status=payload.get("status", "compiled"),
            created_at=payload.get("created_at", datetime.now(timezone.utc).isoformat()),
            nodes=[CalcNode.from_dict(node) for node in payload.get("nodes", [])],
            output_node_ids=list(payload.get("output_node_ids", [])),
            assumptions=list(payload.get("assumptions", [])),
            constraints=[CalcConstraint(**item) for item in payload.get("constraints", [])],
            provenance=list(payload.get("provenance", [])),
        )

    def reproducible_payload(self) -> dict[str, Any]:
        """Return only semantic graph data; omit random IDs and timestamps."""
        nodes = []
        for node in self.nodes:
            item = node.to_dict()
            nodes.append(item)
        return {
            "version": self.version,
            "type_system_version": self.type_system_version,
            "goal": self.goal,
            "calculator": self.calculator,
            "nodes": nodes,
            "output_node_ids": self.output_node_ids,
            "assumptions": self.assumptions,
            "constraints": [constraint.to_dict() for constraint in self.constraints],
            "provenance": self.provenance,
        }

    def fingerprint(self) -> str:
        canonical = json.dumps(self.reproducible_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
