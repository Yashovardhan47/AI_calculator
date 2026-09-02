# OmniCalc + CalcGraph

OmniCalc is a natural-language calculation workspace. The CalcGraph research contribution adds a typed, inspectable calculation intermediate representation between user intent and deterministic execution. Every accepted request now returns the result, graph, static-verification report, formula provenance, and a downloadable evidence receipt.

The original CodeAlpha Age Calculator files remain in the repository for history. The new application lives in separate `frontend`, `backend`, `database`, and `api_keys` folders.

## First implemented calculation families

- Safe arithmetic expressions
- Exact age and date differences
- Loan EMI and total-interest calculations
- Mean, median, population standard deviation, minimum, and maximum
- Unit and temperature conversion

The deterministic engine performs every numerical operation. If `OPENAI_API_KEY` is configured, AI is used only to route and normalize natural-language requests; it cannot add operations, bypass graph verification, or provide the accepted numeric result. An automatic local router keeps the application functional without a paid key.

## CalcGraph research pipeline

```text
Natural-language goal
        ↓
Typed CalcGraph compiler
        ↓
Static verifier (operation, signature, type, edge, DAG, finite value, dimension)
        ↓
Allowlisted deterministic executor
        ↓
Result + formula provenance + reproducibility receipt
```

The current research prototype integrates five domain packs. It is deliberately honest about scope: the contribution is a verifiable cross-domain calculation protocol, not a claim that every calculation in the world is already implemented.

## Project structure

```text
frontend/                 React + Vite calculation workspace
backend/                  FastAPI API and verified Python calculation engine
  app/calculator/modules/ Independent domain calculators
  app/calcgraph/          Typed IR, compiler, verifier, executor, and receipts
  app/services/           Optional AI intent routing
  tests/                  Engine tests
database/                 PostgreSQL schema and database notes
api_keys/                 Secret-management and provider documentation
docs/                     Architecture and API documentation
research/                 Research claim, experiment plan, and benchmark
```

## Run with Docker

1. Copy `.env.example` to `.env`.
2. Leave `OPENAI_API_KEY` blank for local deterministic routing, or add your key.
3. Run `docker compose up --build`.
4. Open `http://localhost:5173`.

The API documentation is available at `http://localhost:8000/docs`.

## Run without Docker

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Research benchmark:

```bash
backend/.venv/bin/python research/run_benchmark.py
```

## Security rules

- Real API keys belong only in `.env`; never put them in frontend code or Git.
- AI proposes a calculator route but never supplies the trusted numeric result.
- Only versioned operations in the formula registry can execute.
- Static verification rejects malformed edges, cycles, type errors, non-finite values, and incompatible unit dimensions.
- Arithmetic is parsed with a restricted Python syntax tree; arbitrary code is not evaluated.
- Live rates must retain their provider and retrieval timestamp when added.

See `docs/ARCHITECTURE.md`, `docs/API.md`, `research/README.md`, and `api_keys/README.md` for details.
