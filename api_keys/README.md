# API keys and secrets

No paid key is required for the five verified calculator families in the first release.

## Used now

| Variable | Required | Purpose |
|---|---:|---|
| `OPENAI_API_KEY` | No | Routes complex natural-language requests to a verified calculator. The numeric result is still produced locally. |
| `OPENAI_MODEL` | No | Selects the routing model; defaults to `gpt-5-mini`. |
| `DATABASE_URL` | For persistence | PostgreSQL connection string. It is configuration, not an API key. |

## Planned integrations

| Variable | Required | Purpose |
|---|---:|---|
| `EXCHANGE_RATE_API_KEY` | Only for live currency | Retrieves timestamped currency rates. |
| `WOLFRAM_APP_ID` | Only for external verification | Optional second-source verification for advanced scientific calculations. |

## Safe setup

1. Copy the root `.env.example` file to `.env`.
2. Add real values only to `.env` on your own machine or hosting provider.
3. Keep `.env` out of Git. The repository `.gitignore` already excludes it.
4. Never create `VITE_OPENAI_API_KEY` or any other secret beginning with `VITE_`; Vite exposes those values to every browser user.
5. Rotate a key immediately if it is ever committed, shown in a screenshot, or included in logs.

This folder contains documentation only. It must never contain real credentials.

