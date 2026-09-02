import httpx

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .calculator import CALCULATORS
from .calcgraph import (
    CalcGraph,
    ClarificationNeeded,
    GraphVerificationError,
    compile_query,
    execute_graph,
    verify_graph,
)
from .calcgraph.service import calculate_with_graph
from .config import settings
from .schemas import CalcGraphPayload, CalculationRequest, CalculationResult, CalculatorInfo
from .services.ai_router import route_with_openai


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Natural-language routing backed by deterministic, verifiable calculation tools.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok", "version": settings.app_version, "ai_router_enabled": bool(settings.openai_api_key)}


@app.get("/api/v1/calculators", response_model=list[CalculatorInfo])
def list_calculators() -> list[dict]:
    return CALCULATORS


def _calculation_error(exc: Exception, calculator: str | None = None) -> HTTPException:
    detail: dict = {"message": str(exc), "calculator": calculator}
    if isinstance(exc, ClarificationNeeded):
        detail["calculator"] = exc.calculator
        detail["questions"] = exc.questions
    if isinstance(exc, GraphVerificationError):
        detail["verification"] = exc.report.to_dict()
    return HTTPException(status_code=422, detail=detail)


@app.post("/api/v1/calculate", response_model=CalculationResult)
async def run_calculation(payload: CalculationRequest) -> dict:
    query = payload.query
    hint = payload.calculator
    routing_source = "client_hint" if hint else "local"

    if not hint and settings.openai_api_key:
        try:
            route = await route_with_openai(query, settings.openai_api_key, settings.openai_model)
            query = route["normalized_query"]
            hint = route["calculator"]
            routing_source = "openai"
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            routing_source = "local_fallback"

    try:
        result = calculate_with_graph(query, hint)
    except (ClarificationNeeded, GraphVerificationError, SyntaxError, TypeError, ValueError, ZeroDivisionError, OverflowError) as exc:
        raise _calculation_error(exc, hint) from exc

    result["metadata"]["routing_source"] = routing_source
    return result


@app.post("/api/v1/calcgraph/compile")
def compile_calcgraph(payload: CalculationRequest) -> dict:
    try:
        graph = compile_query(payload.query, payload.calculator)
    except (ClarificationNeeded, SyntaxError, TypeError, ValueError) as exc:
        raise _calculation_error(exc, payload.calculator) from exc
    return {"calcgraph": graph.to_dict(), "graph_fingerprint": graph.fingerprint()}


@app.post("/api/v1/calcgraph/verify")
def verify_calcgraph(payload: CalcGraphPayload) -> dict:
    try:
        graph = CalcGraph.from_dict(payload.graph)
        return verify_graph(graph).to_dict()
    except (TypeError, KeyError, ValueError) as exc:
        raise _calculation_error(exc) from exc


@app.post("/api/v1/calcgraph/execute")
def execute_calcgraph(payload: CalcGraphPayload) -> dict:
    try:
        graph = CalcGraph.from_dict(payload.graph)
        return execute_graph(graph)
    except (GraphVerificationError, SyntaxError, TypeError, KeyError, ValueError, ZeroDivisionError, OverflowError) as exc:
        raise _calculation_error(exc, getattr(graph, "calculator", None) if "graph" in locals() else None) from exc
