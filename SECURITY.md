# Security policy

## Supported version

The `omnicalc-production` branch is the supported deployment line. Research branches may contain experimental interfaces.

## Reporting

Do not open a public issue containing credentials, tokens, personal data, or an exploitable proof. Contact the repository owner privately and include the affected version, impact, reproduction conditions, and a minimal proof with secrets removed.

## Deployment assumptions

OmniCalc must use HTTPS in production. Production mode validates secure cookies, an explicit origin allowlist, a non-default JWT secret, and PostgreSQL persistence at startup. Operators remain responsible for gateway rate limits, TLS, backups, monitoring, dependency updates, and secret management.

## Sensitive values

Never commit `.env`, database passwords, `JWT_SECRET`, `OPENAI_API_KEY`, raw JWTs, or Google ID tokens. The Google OAuth Web Client ID is public configuration and may appear in frontend output; a Google client secret is not used by this sign-in design.
