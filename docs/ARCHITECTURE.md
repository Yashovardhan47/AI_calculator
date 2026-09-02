# Architecture

## Trust boundary

```text
User request
    ↓
Frontend validation
    ↓
AI or local intent router         untrusted interpretation
    ↓
CalcGraph compiler                typed intermediate representation
    ↓
Static graph verifier             trusted policy gate
    ↓
Allowlisted graph executor        trusted numeric computation
    ↓
Result + provenance + evidence receipt
```

The AI layer is optional and untrusted. It may select a calculator and normalize wording, but it cannot add an executable operation, alter the formula registry, bypass verification, or supply the accepted final number.

## Components

- **Frontend:** React workspace with category selection, natural-language composer, results, error states, and device-local history.
- **API:** FastAPI endpoints for health, calculator discovery, complete calculations, graph compilation, graph verification, and graph execution.
- **Router:** Local keyword router by default; optional OpenAI structured-output router with automatic local fallback.
- **CalcGraph compiler:** Produces typed input and operation nodes, declared outputs, assumptions, and versioned formula provenance.
- **Static verifier:** Checks IR version, unique nodes, finite values, the operation allowlist, formula signatures, semantic types, edge references, unit dimensions, outputs, and acyclicity.
- **Executor:** Runs verified graphs with deterministic domain calculators and generates content hashes plus a unique evidence receipt.
- **Modules:** Pure Python domain functions that can be tested independently of the web framework.
- **Database:** PostgreSQL schema for history, reusable workflows, time-stamped provider data, graph artifacts, formula versions, and evidence receipts.

## CalcGraph IR

A graph has a version, goal, calculator domain, typed nodes, declared outputs, assumptions, constraints, and formula provenance. Input nodes hold normalized values. Operation nodes reference inputs by node ID and name a versioned operation from `FORMULA_REGISTRY`.

The graph fingerprint is SHA-256 over canonical semantic graph content. Random graph IDs, timestamps, and execution status are excluded. A result digest hashes the normalized calculator result. The reproducibility hash binds the graph fingerprint and result digest; independent executions of identical content produce the same value.

## Request flow

1. The browser sends a goal and optional trusted calculator hint.
2. The local router or optional OpenAI router selects a registered domain; AI output remains untrusted.
3. The compiler resolves explicit inputs or returns structured clarification questions.
4. The verifier rejects invalid operations, types, edges, values, dimensions, outputs, or cycles.
5. The executor dispatches only to a registered deterministic handler.
6. The API returns the normal OmniCalc result plus the graph, verification evidence, and receipt.
7. The browser renders the graph trace and lets the user download the evidence JSON.

## Adding a calculator

1. Add a pure calculation module under `backend/app/calculator/modules`.
2. Add a versioned operation signature and provenance entry to `calcgraph/formulas.py`.
3. Add a goal compiler that emits typed nodes in `calcgraph/compiler.py`.
4. Add the allowlisted execution adapter in `calcgraph/executor.py`.
5. Add its metadata to `registry.py` and deterministic routing rules to `parser.py`.
6. Add the calculator to the optional AI router's allowlist and JSON schema.
7. Add compiler, verifier, executor, boundary, and invalid-graph tests.
8. Add its frontend category only after the API and research benchmark pass.

## Planned evolution

The next research increments are multi-operation graph planning, symbolic algebra with SymPy, uncertainty and interval nodes, dimensional analysis with Pint, independent executor implementations, signed receipts, property-based benchmark generation, database persistence with authentication, and provenance-aware live data.
