import json

import httpx


ALLOWED_TOOLS = ["arithmetic", "age", "emi", "statistics", "units"]


async def route_with_openai(query: str, api_key: str, model: str) -> dict:
    """Use AI only to select a verified calculator; never trust it for arithmetic."""
    schema = {
        "type": "object",
        "properties": {
            "calculator": {"type": "string", "enum": ALLOWED_TOOLS},
            "normalized_query": {"type": "string"},
        },
        "required": ["calculator", "normalized_query"],
        "additionalProperties": False,
    }
    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": "Route the request to one verified calculator. Preserve every number, unit, date, and assumption. Do not calculate the answer.",
            },
            {"role": "user", "content": query},
        ],
        "text": {"format": {"type": "json_schema", "name": "calculation_route", "strict": True, "schema": schema}},
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/responses",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    text = data["output"][0]["content"][0]["text"]
    routed = json.loads(text)
    if routed.get("calculator") not in ALLOWED_TOOLS:
        raise ValueError("AI returned an unsupported calculator route.")
    return routed

