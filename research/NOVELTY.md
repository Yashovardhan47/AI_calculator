# CalcGraph novelty roadmap and implemented contribution

## Implemented research increment

CalcGraph now supports a reproducible analysis protocol in addition to verified execution:

1. compile a natural-language goal into a typed graph;
2. statically verify formula identity, types, units, edges, outputs, and DAG structure;
3. execute through an operation allowlist;
4. derive bounded uncertainty intervals by deterministic corner enumeration;
5. estimate local input-output sensitivity with central finite differences;
6. re-execute named counterfactual scenarios;
7. bind the analysis payload to an SHA-256 evidence digest.

The API returns method names and limitations with every analysis result. This keeps the evidence self-describing and prevents an interval estimate from being presented as a formal proof.

## Defensible research question

> Does an uncertainty- and provenance-aware calculation graph improve correctness auditing, failure detection, and user calibration compared with direct natural-language answer generation?

This is narrower and more testable than claiming universal calculation.

## Publication experiments still required

- Compare direct language-model answers, tool-only calculation, verified CalcGraph, and verified CalcGraph with analysis.
- Measure answer accuracy, parser coverage, unsafe acceptance rate, verification detection rate, latency, and user calibration.
- Create adversarial cases covering ambiguous language, unit mismatch, corrupted formulas, cycles, non-finite values, correlated inputs, and non-monotonic functions.
- Run ablations without types, provenance, verification, uncertainty, and receipts.
- Report confidence intervals, effect sizes, failure taxonomy, hardware/software versions, and complete dataset licenses.
- Arrange independent replication or blinded review of a held-out set.

## Next novel feature candidates

1. SMT-backed constraint certificates for algebraic and unit invariants.
2. Correlated probabilistic uncertainty using covariance-aware Monte Carlo sampling.
3. Governed live-data adapters with source snapshots, timestamps, licenses, and content hashes.
4. Formula lifecycle governance: proposed, reviewed, approved, deprecated, and revoked states.
5. Independent receipt verification CLI and public benchmark package.
6. Causal-model plugins that explicitly distinguish interventions from counterfactual arithmetic.

These should be delivered as separate evaluated increments, not claimed before implementation.
