from typing import Any

from pydantic import BaseModel, Field


class CalculationRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2_000)
    calculator: str | None = Field(
        default=None,
        description="Optional verified calculator hint supplied by a trusted client.",
    )


class CalculationResult(BaseModel):
    request_id: str
    query: str
    calculator: str
    title: str
    answer: str
    value: float | int | list[float] | None = None
    unit: str | None = None
    formula: str
    steps: list[str]
    assumptions: list[str]
    confidence: float = Field(ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    calcgraph: dict[str, Any]
    verification: dict[str, Any]
    receipt: dict[str, Any]
    node_results: dict[str, Any] = Field(default_factory=dict)


class CalcGraphPayload(BaseModel):
    graph: dict[str, Any]


class CalculatorInfo(BaseModel):
    id: str
    name: str
    description: str
    examples: list[str]
