# API

Base path: `/api/v1`

## Health

`GET /health`

Returns service version and whether optional AI routing is enabled. It never reveals the key.

## Calculator registry

`GET /calculators`

Returns calculator IDs, descriptions, and examples for client discovery.

## Calculate

`POST /calculate`

Request:

```json
{
  "query": "EMI for ₹10 lakh at 8.5% for 5 years",
  "calculator": null
}
```

Successful response:

```json
{
  "request_id": "generated-uuid",
  "query": "EMI for ₹10 lakh at 8.5% for 5 years",
  "calculator": "emi",
  "title": "Loan EMI",
  "answer": "₹20,516.53 per month",
  "value": 20516.53,
  "unit": "INR/month",
  "formula": "EMI = P × r × (1+r)^n ÷ ((1+r)^n − 1)",
  "steps": ["..."],
  "assumptions": ["..."],
  "confidence": 0.98,
  "metadata": {
    "routing_source": "local"
  }
}
```

Invalid or incomplete input returns HTTP `422` with a human-readable message and the calculator that requested clarification.

