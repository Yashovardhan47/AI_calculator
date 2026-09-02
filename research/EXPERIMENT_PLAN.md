# CalcGraph experiment plan

## Questions

1. Does the compiler produce a typed graph for complete goals and actionable questions for incomplete goals?
2. Does static verification reject unknown operations, malformed edges, cycles, non-finite values, and dimension errors before execution?
3. Do repeated executions of the same semantic graph produce the same graph fingerprint, result digest, and reproducibility hash?
4. Can a person inspect the formula lineage and execution evidence without reading backend code?

## Measurements

| Measure | Definition | Initial target |
|---|---|---|
| Compilation coverage | Complete benchmark goals compiled / complete goals | 100% for registered domain packs |
| Invalid-graph rejection | Invalid graphs rejected before execution / invalid graphs | 100% |
| Result agreement | Successful results matching trusted fixtures / successful cases | 100% |
| Repeatability | Repeated identical cases with equal reproducibility hashes | 100% |
| Clarification quality | Incomplete cases returning at least one missing-input question | 100% |

## Ablations

- Disable semantic-type checks and measure how many malformed edges reach the executor.
- Disable dimension checks and test mass-to-length conversion graphs.
- Remove formula versions from provenance and evaluate whether receipts still identify an executable definition.
- Compare free-form chain-of-thought style output with CalcGraph receipts for automated validation and replay.

## Threats to validity

- Benchmark cases are small and curated.
- Compiler rules share assumptions with the deterministic calculators.
- Current graphs contain a single operation; multi-operation planning needs a later benchmark.
- Fingerprints establish content identity, not external truth or regulatory suitability.

## Publication path

Freeze formula versions, expand benchmark generation, add independent reference implementations, report every failed case, and publish the IR schema plus benchmark under a stable release tag before making broader research claims.
