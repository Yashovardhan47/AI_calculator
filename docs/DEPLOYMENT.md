# Deployment

## Required services

- A host capable of running the application containers and PostgreSQL, or equivalent managed services.
- An HTTPS domain for production.
- A Google OAuth 2.0 Web Client ID.
- A random JWT signing secret.
- Optional: an OpenAI API key for intent routing. Calculations work without it.

## 1. Configure Google Identity Services

In Google Cloud Console:

1. Configure the OAuth consent screen.
2. Create an OAuth client with application type **Web application**.
3. Add `http://localhost:5173` and the exact production HTTPS origin, such as `https://calc.example.com`, to **Authorized JavaScript origins**.
4. Copy the client ID, not a client secret, into both `GOOGLE_CLIENT_ID` and `VITE_GOOGLE_CLIENT_ID`.

This flow does not need a Google client secret. The frontend obtains an ID token and the backend verifies its signature and audience. The client ID is intentionally visible in the frontend; it identifies the application but does not authorize API access.

## 2. Create production configuration

Create a host-managed `.env` that is never committed:

```dotenv
POSTGRES_PASSWORD=use-a-long-url-safe-random-value
JWT_SECRET=use-at-least-64-random-url-safe-characters
GOOGLE_CLIENT_ID=000000000000-example.apps.googleusercontent.com
VITE_GOOGLE_CLIENT_ID=000000000000-example.apps.googleusercontent.com
ALLOWED_ORIGINS=https://calc.example.com
COOKIE_SAMESITE=lax
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5-mini
PORT=80
```

Generate a JWT secret locally:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Use a URL-safe database password because the production Compose file interpolates it into `DATABASE_URL`. On a managed platform, supply its complete `DATABASE_URL` directly.

## 3. Start the stack

```bash
docker compose -f compose.production.yml config
docker compose -f compose.production.yml up -d --build
```

Terminate TLS at a load balancer or reverse proxy and forward the public origin to the frontend container. Nginx serves the frontend and forwards `/api/*` to FastAPI on the private Compose network. PostgreSQL and FastAPI are not published publicly by the production file.

## 4. Verify

1. `GET https://your-domain/api/v1/health` reports `persistence: postgresql` and `google_auth_enabled: true`.
2. Register a local user, sign out, and sign in again.
3. Sign in with Google.
4. Run a calculation, reload, and confirm history remains.
5. Save and rerun a workflow.
6. Confirm the refresh cookie is `HttpOnly` and `Secure` in browser developer tools.
7. Run the repository CI commands before each release.

## Operational controls

- Back up PostgreSQL and test restoration.
- Rate-limit `/api/v1/auth/register`, `/login`, `/google`, and `/refresh` at the gateway.
- Set request-size limits and timeouts at the public proxy.
- Restrict database access to the backend network and use a least-privilege role.
- Rotate `JWT_SECRET` through planned session invalidation; changing it signs every user out.
- Never log passwords, Google credentials, JWTs, refresh cookies, or `.env` contents.
- Keep Python, Node, PostgreSQL, dependencies, and base images patched.

## Scaling note

Production startup refuses an empty `DATABASE_URL`, so API replicas share users, sessions, history, and workflows. JWT access verification is stateless; refresh rotation is stateful in PostgreSQL. Point every replica at the same database and keep them behind the same HTTPS origin.
