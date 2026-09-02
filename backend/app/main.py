import httpx

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .calculator import CALCULATORS, CalculationError, calculate
from .config import settings
from .schemas import CalculationRequest, CalculationResult, CalculatorInfo
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
        result = calculate(query, hint)
    except CalculationError as exc:
        raise HTTPException(
            status_code=422,
            detail={"message": str(exc), "calculator": exc.calculator},
        ) from exc

    result["metadata"]["routing_source"] = routing_source
    return result
