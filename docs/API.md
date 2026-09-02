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
    "routing_source": "local",
    "calcgraph_version": "0.1.0",
    "graph_fingerprint": "sha256..."
  },
  "calcgraph": {"graph_id": "...", "nodes": ["..."], "provenance": ["..."]},
  "verification": {"valid": true, "checks": ["..."], "topological_order": ["..."]},
  "receipt": {"receipt_id": "...", "reproducibility_hash": "sha256..."}
}
```

Invalid or incomplete input returns HTTP `422` with a human-readable message, the calculator, and structured `questions` when required inputs are missing. Invalid submitted graphs also include the complete verification report.

## Compile a graph

`POST /calcgraph/compile`

Accepts the same request as `/calculate` and returns a compiled graph plus its deterministic fingerprint without executing it.

## Verify a graph

`POST /calcgraph/verify`

Request:

```json
{"graph": {"version": "0.1.0", "goal": "...", "calculator": "...", "nodes": [], "output_node_ids": []}}
```

Returns `valid`, every pass/fail check, the topological execution order, and errors. Verification never executes graph operations.

## Execute a graph

`POST /calcgraph/execute`

Accepts `{"graph": {...}}`. The graph must pass static verification. A successful response contains `calculation`, `calcgraph`, `verification`, and `receipt`. Unknown operations, invalid types, dangling edges, cycles, non-finite values, dimension mismatches, and missing outputs return HTTP `422` before calculator dispatch.

## Evidence semantics

- `graph_fingerprint`: SHA-256 of canonical semantic graph content.
- `result_digest`: SHA-256 of the deterministic result object.
- `reproducibility_hash`: SHA-256 binding the two hashes above.
- `receipt_id`: unique execution identity; unlike the reproducibility hash, it changes on every run.
