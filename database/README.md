# Database

`schema.sql` prepares PostgreSQL for users, refresh sessions, calculation history, reusable workflows, timestamped live-rate snapshots, CalcGraph intermediate representations, and evidence receipts. `002_calcgraph.sql` adds research tables to an existing database; `003_auth.sql` adds the production authentication fields and refresh-session table.

The backend selects PostgreSQL whenever `DATABASE_URL` is present. Without it, a thread-safe in-memory store supports local development and tests; production mode refuses to start without PostgreSQL.

Docker initialization scripts run only when the PostgreSQL data directory is first created. For an existing database created before authentication was added, apply `003_auth.sql` with your migration process before starting the production API.

Design rules:

- Store calculation inputs and structured results, never API keys.
- Store salted password hashes and refresh-token hashes, never plaintext passwords or raw refresh JWTs.
- Apply the authenticated `user_id` to every history/workflow read and mutation.
- Retain the provider and retrieval time for every live external rate.
- Use JSONB for calculator-specific details while keeping identity, calculator, and timestamp fields queryable.
- Delete user-owned history and workflows automatically when a user is deleted.
- Store graph fingerprints and result digests, not secrets, in research evidence receipts.
- Version every formula signature so a result can be tied to the exact executable definition.
