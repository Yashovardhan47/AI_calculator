# Known limitations and validity boundaries

This document is part of the deployable product contract. It records what OmniCalc and CalcGraph do **not** guarantee.

## Calculation coverage

- OmniCalc executes only registered calculator packs and allowlisted formulas. It does not calculate every possible problem.
- The rule-based parser may reject valid requests whose wording or domain is not registered.
- The advanced pack is a curated collection, not a general computer-algebra system, theorem prover, numerical simulator, or domain expert.
- Results are not professional medical, legal, investment, structural-engineering, or safety advice.
- Currency conversion, market prices, tax rules, regulations, and other live facts are not available without a separately governed data adapter.
- Floating-point arithmetic can introduce rounding error. Financial displays are rounded, while internal intermediate values may retain more precision.

## CalcGraph verification

- Static verification proves structural properties: registered operations, type compatibility, valid edges, acyclicity, unit dimensions, finite inputs, formula identity, and declared provenance.
- Verification does not prove that the user's intent was interpreted correctly.
- Verification does not prove that a registered formula is scientifically appropriate for every real-world context.
- A reproducibility hash proves equality of canonical serialized graph and result data; it is not a third-party digital signature.
- Formula sources in the registry are descriptive provenance. Publication-grade claims require citations, independent review, and version governance.

## Uncertainty and sensitivity analysis

- Uncertainty intervals use deterministic corner enumeration over independently varied scalar inputs.
- Corner enumeration is exact for monotonic functions over the declared box but is not a formal global bound for arbitrary non-monotonic functions.
- Input correlations, probability distributions, covariance, and Bayesian uncertainty are not modeled.
- Local sensitivity uses a central finite difference and depends on the chosen step.
- Analysis currently supports scalar numeric graph inputs and scalar numeric outputs only.
- At most eight uncertain inputs and twenty counterfactual scenarios are accepted per request to bound exponential work and denial-of-service risk.
- Counterfactual results show model behavior under overrides; they do not establish causality.

## AI routing

- The optional OpenAI router normalizes intent and selects a registered calculator; it is not permitted to execute code or directly produce the verified numeric result.
- When AI routing fails, the application falls back to local routing.
- Prompt ambiguity can still require clarification and should not be silently guessed in consequential domains.

## Authentication and privacy

- Local JWT authentication and Google ID-token exchange are implemented, but production validity depends on correct secrets, HTTPS, cookie policy, and Google Console origins.
- Access JWTs are stored in browser session storage; a successful same-origin script injection could read them. A strict Content Security Policy and dependency hygiene remain required.
- Refresh tokens are HttpOnly cookies and are stored server-side only as hashes, but compromised devices or sessions can still be abused until revoked.
- The application does not yet implement MFA, organization SSO, device management, breach-password screening, or user-facing session inventory.
- Calculation history can contain sensitive inputs. Operators must define retention, deletion, backup, and access-control policies.

## Operations and deployment

- Passing CI is not equivalent to a live production smoke test.
- Production requires PostgreSQL, unique secrets, HTTPS-only origins, secure cookies, backups, monitoring, alerting, and a tested rollback.
- Docker startup and real Google OAuth must be tested in the target environment.
- Rate limiting, edge/WAF controls, centralized audit logging, dependency scanning, and disaster-recovery exercises are operator responsibilities unless explicitly configured.
- The current demo is an interface preview and does not prove that the full backend, database, and OAuth stack are deployed.

## Research and publication

- The current benchmark is a prototype suite, not evidence of broad real-world superiority.
- A publication requires frozen datasets, independently implemented baselines, statistical testing, ablations, error taxonomy, reproducibility artifacts, and disclosure of failed cases.
- Novelty must be supported by a literature review. Product breadth alone is not a research contribution.
- Results generated on synthetic or author-created cases must be labeled as such.
