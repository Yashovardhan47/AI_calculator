# API

Base path: `/api/v1`

Authenticated endpoints use `Authorization: Bearer <access-token>`. Refresh and logout use the `omnicalc_refresh` HttpOnly cookie. Error bodies use `{"detail": {"message": "..."}}` unless FastAPI returns field-validation details.

## Authentication

| Method | Path | Body | Result |
|---|---|---|---|
| `POST` | `/auth/register` | `email`, `password`, `display_name` | Creates a local user and session |
| `POST` | `/auth/login` | `email`, `password` | Creates a session |
| `POST` | `/auth/google` | `credential` Google ID token | Verifies Google and creates a session |
| `POST` | `/auth/refresh` | none; refresh cookie required | Rotates refresh session and returns a new access JWT |
| `POST` | `/auth/logout` | none | Revokes refresh session and clears cookie |
| `GET` | `/auth/me` | bearer token | Returns the active public profile |
| `PATCH` | `/auth/me` | `display_name` | Updates the active profile |
| `DELETE` | `/auth/me` | bearer token | Deletes user-owned data through database cascades |

Registration, login, Google exchange, and refresh return:

```json
{
  "access_token": "signed-jwt",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "display_name": "User",
    "auth_provider": "local",
    "email_verified": false,
    "avatar_url": null,
    "created_at": "2026-09-18T00:00:00Z"
  }
}
```

The raw refresh JWT is never returned in JSON.

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
    "calcgraph_version": "0.2.0",
    "graph_fingerprint": "sha256..."
  },
  "calcgraph": {"graph_id": "...", "nodes": ["..."], "provenance": ["..."]},
  "verification": {"valid": true, "checks": ["..."], "topological_order": ["..."]},
  "receipt": {"receipt_id": "...", "reproducibility_hash": "sha256..."}
}
```

When a valid bearer token is present, the calculation is saved to the current user's history and `metadata.history_id` is returned. Anonymous direct API calculations remain possible but are not persisted; the web application requires authentication.

Invalid or incomplete input returns HTTP `422` with a human-readable message, the calculator, and structured `questions` when required inputs are missing. Invalid submitted graphs also include the complete verification report.

## Compile a graph

`POST /calcgraph/compile`

Accepts the same request as `/calculate` and returns a compiled graph plus its deterministic fingerprint without executing it.

## Verify a graph

`POST /calcgraph/verify`

Request:

```json
{"graph": {"version": "0.2.0", "type_system_version": "0.2.0", "goal": "...", "calculator": "...", "nodes": [], "output_node_ids": []}}
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

## Authenticated workspace

| Method | Path | Result |
|---|---|---|
| `GET` | `/history?limit=50` | Current user's calculation history |
| `DELETE` | `/history/{history_id}` | Deletes one owned history item |
| `DELETE` | `/history` | Clears current user's history |
| `GET` | `/workflows` | Current user's saved workflows |
| `POST` | `/workflows` | Saves `name`, optional `description`, and `workflow_definition` |
| `DELETE` | `/workflows/{workflow_id}` | Deletes one owned workflow |

Ownership is enforced in storage queries; record IDs alone do not grant access.
