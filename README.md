# OmniCalc + CalcGraph

OmniCalc is a deployable AI-assisted calculation workspace. A user describes a goal in natural language; CalcGraph compiles it into a typed calculation graph, verifies the graph, executes only allowlisted deterministic formulas, and returns a result with provenance and a reproducibility receipt.

This production branch includes email/password authentication, Google Identity Services sign-in, short-lived JWT access tokens, rotating refresh sessions, PostgreSQL-backed user data, synchronized calculation history, and reusable workflows.

## What is implemented

- Safe arithmetic expressions
- Exact age and calendar differences
- Loan EMI, total payment, total interest, and interest-share graphs
- Mean, median, population standard deviation, minimum, and maximum
- Length, mass, and temperature conversion
- Linear and quadratic algebra, common geometry formulas, simple and compound interest, discounts
- Factorials, GCD, LCM, permutations, combinations, BMI, average speed, and degree-mode trigonometry
- CalcGraph typed IR, static verification, versioned formula registry, deterministic execution, and evidence receipts
- Local registration/login plus server-verified Google sign-in
- Account-scoped history and saved workflows
- Docker development and production stacks plus CI

AI is optional. When `OPENAI_API_KEY` is configured, it only routes and normalizes a request. It cannot add executable operations, bypass graph verification, or supply the accepted number. The local router keeps the application functional without a paid AI key.

## Repository structure

```text
frontend/                 React + Vite authenticated workspace
backend/                  FastAPI, authentication, CalcGraph, calculators
  app/auth/               Google verification and JWT session lifecycle
  app/calculator/modules/ Deterministic domain calculators
  app/calcgraph/          IR, compiler, type system, verifier, executor
  app/routers/            Account-scoped workspace endpoints
  tests/                  API, auth, graph, and calculator tests
database/                 PostgreSQL schema and migrations
api_keys/                 Configuration and secret-handling guide
docs/                     Architecture, authentication, API, deployment
research/                 Claim, experiment plan, benchmark, metrics
```

## Start locally

1. Copy `.env.example` to `.env`.
2. Generate `JWT_SECRET` using the command shown in `.env.example`.
3. Add a Google OAuth Web Client ID to both `GOOGLE_CLIENT_ID` and `VITE_GOOGLE_CLIENT_ID`, or leave both blank while testing email/password auth.
4. Run:

```bash
docker compose up --build
```

Open `http://localhost:5173`. API documentation is at `http://localhost:8000/docs`.

The Docker frontend uses its Nginx `/api` proxy by default. For a separate Vite development server, create `frontend/.env.local` containing `VITE_API_BASE_URL=http://localhost:8000`.

## Validate

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
cd ..
python research/run_benchmark.py

cd frontend
npm ci
npm run build
```

## Production

`compose.production.yml` fails fast unless PostgreSQL, a unique JWT secret, secure cookies, explicit origins, and Google client IDs are configured. Put HTTPS in front of the frontend container, then run:

```bash
docker compose -f compose.production.yml up -d --build
```

Read [Authentication](docs/AUTHENTICATION.md) and [Deployment](docs/DEPLOYMENT.md) before deploying. The [research folder](research/README.md) states the current contribution and its limits; it does not claim that every possible calculation is implemented.

## Security invariants

- Passwords are salted and hashed with scrypt; plaintext passwords are never stored.
- Google ID tokens are verified by the backend for signature, issuer, audience, expiry, stable subject, and verified email.
- Access JWTs live in browser session storage and expire quickly.
- Refresh JWTs live only in `HttpOnly` cookies; only SHA-256 token hashes are stored server-side and every refresh rotates the session.
- Browser authentication requests are restricted to configured origins.
- Production refuses the development JWT secret, in-memory persistence, insecure cookies, or wildcard origins.
- Arbitrary Python or AI-generated code is never evaluated by the calculation engine.

Never commit `.env` or real credentials. See [API keys and secrets](api_keys/README.md) and [Security](SECURITY.md).
