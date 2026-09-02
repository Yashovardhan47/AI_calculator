# Database

`schema.sql` prepares PostgreSQL for calculation history, reusable calculation workflows, and timestamped live-rate snapshots.

The first release deliberately stores browser history on the user's device and does not write to PostgreSQL yet. Database persistence will be enabled together with authentication so one user's calculations can never be associated with another user accidentally.

Design rules:

- Store calculation inputs and structured results, never API keys.
- Retain the provider and retrieval time for every live external rate.
- Use JSONB for calculator-specific details while keeping identity, calculator, and timestamp fields queryable.
- Delete user-owned history and workflows automatically when a user is deleted.

