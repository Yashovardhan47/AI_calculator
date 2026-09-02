# Architecture

## Trust boundary

```text
User request
    ↓
Frontend validation
    ↓
AI or local intent router         untrusted interpretation
    ↓
Calculator registry              allowlisted tool selection
    ↓
Verified Python calculator       trusted numeric computation
    ↓
Formula + steps + assumptions
```

The AI layer is optional and untrusted. It may select a calculator and normalize wording, but it cannot add a new executable tool or supply the accepted final number.

## Components

- **Frontend:** React workspace with category selection, natural-language composer, results, error states, and device-local history.
- **API:** FastAPI endpoints for health, calculator discovery, and calculation requests.
- **Router:** Local keyword router by default; optional OpenAI structured-output router with automatic local fallback.
- **Engine:** Calculator allowlist, standardized errors, request IDs, and normalized result envelopes.
- **Modules:** Pure Python domain functions that can be tested independently of the web framework.
- **Database:** PostgreSQL schema prepared for authenticated history, reusable workflows, and time-stamped provider data.

## Adding a calculator

1. Add a pure calculation module under `backend/app/calculator/modules`.
2. Register its handler in `engine.py`.
3. Add its metadata to `registry.py`.
4. Add deterministic routing rules to `parser.py`.
5. Add the calculator to the AI router's allowlist and JSON schema.
6. Add success, boundary, and invalid-input tests.
7. Add its frontend category only after the API implementation passes tests.

## Planned evolution

The next safe increments are algebra with SymPy, compound-interest and goal solvers, expanded units with Pint, database persistence with authentication, live currency rates, and reusable multi-step workflows.

