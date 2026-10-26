# API keys and secrets

No paid key is required for the five verified calculator families in the first release.

## Used now

| Variable | Required | Purpose |
|---|---:|---|
| `OPENAI_API_KEY` | No | Routes complex natural-language requests to a verified calculator. The numeric result is still produced locally. |
| `OPENAI_MODEL` | No | Selects the routing model; defaults to `gpt-5-mini`. |
| `DATABASE_URL` | For persistence | PostgreSQL connection string. It is configuration, not an API key. |
| `JWT_SECRET` | Yes in production | Signs OmniCalc access and refresh tokens. Generate at least 64 random URL-safe characters. |
| `GOOGLE_CLIENT_ID` | For Google sign-in | Expected OAuth Web Client ID used by the backend to verify the token audience. |
| `VITE_GOOGLE_CLIENT_ID` | For Google sign-in | The same public client ID embedded in the frontend. This is not a secret. |
| `ALLOWED_ORIGINS` | Yes in production | Comma-separated exact browser origins trusted by CORS and authentication endpoints. |

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
5. `VITE_GOOGLE_CLIENT_ID` is the exception because an OAuth client ID is public application identity, not a credential.
6. Rotate a key immediately if it is ever committed, shown in a screenshot, or included in logs.

This folder contains documentation only. It must never contain real credentials.
