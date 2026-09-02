# OmniCalc AI

OmniCalc AI is a verifiable, natural-language calculation workspace. It understands a user's goal, asks the calculation engine to use the correct domain tool, and returns the result with its formula, steps, assumptions, units, and confidence.

The original CodeAlpha Age Calculator files remain in the repository for history. The new application lives in separate `frontend`, `backend`, `database`, and `api_keys` folders.

## First implemented calculation families

- Safe arithmetic expressions
- Exact age and date differences
- Loan EMI and total-interest calculations
- Mean, median, population standard deviation, minimum, and maximum
- Unit and temperature conversion

The deterministic engine performs every numerical operation. If `OPENAI_API_KEY` is configured, AI is used only to route natural-language requests to a verified tool; an automatic local router keeps the application functional without a paid key.

## Project structure

```text
frontend/                 React + Vite calculation workspace
backend/                  FastAPI API and verified Python calculation engine
  app/calculator/modules/ Independent domain calculators
  app/services/           Optional AI intent routing
  tests/                  Engine tests
database/                 PostgreSQL schema and database notes
api_keys/                 Secret-management and provider documentation
docs/                     Architecture and API documentation
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

## Security rules

- Real API keys belong only in `.env`; never put them in frontend code or Git.
- AI proposes a calculator route but never supplies the trusted numeric result.
- Arithmetic is parsed with a restricted Python syntax tree; arbitrary code is not evaluated.
- Live rates must retain their provider and retrieval timestamp when added.

See `docs/ARCHITECTURE.md`, `docs/API.md`, and `api_keys/README.md` for details.

