# CalcGraph research contribution

CalcGraph is OmniCalc's typed, inspectable intermediate representation (IR) for natural-language calculation goals. It separates interpretation from computation: a compiler converts a goal into a directed acyclic graph; a static verifier checks that graph; an allowlisted executor runs it; and an evidence receipt binds the graph and result with deterministic hashes.

## Research claim

The prototype tests this proposition:

> A calculation assistant can remain conversational while exposing a machine-verifiable computation plan between natural-language interpretation and numeric execution.

The contribution is not a claim that all mathematical domains are solved. Its novelty target is the reusable `goal → typed graph → static proof checks → deterministic execution → evidence receipt` protocol across heterogeneous calculator families.

## Implemented artifacts

- `backend/app/calcgraph/models.py`: versioned graph, node, constraint, and fingerprint model.
- `backend/app/calcgraph/compiler.py`: goal-to-graph compilers for arithmetic, dates, EMI, statistics, and units.
- `backend/app/calcgraph/verifier.py`: allowlist, type, edge, unit-dimension, finite-value, output, and DAG checks.
- `backend/app/calcgraph/executor.py`: deterministic graph execution and evidence receipts.
- `backend/app/calcgraph/formulas.py`: versioned formula provenance registry.
- `calcgraph.schema.json`: portable JSON Schema for the versioned IR envelope.
- `benchmark/sample_cases.json`: reproducible cross-domain and failure-mode benchmark.
- `run_benchmark.py`: zero-extra-dependency benchmark runner.

## Run the research checks

```bash
cd backend
.venv/bin/python -m unittest discover -s tests -v
cd ..
backend/.venv/bin/python research/run_benchmark.py
```

## Boundaries

- The reference compiler handles the five domain packs registered in this branch.
- It uses rules, not a general theorem prover or symbolic algebra system.
- A hash proves identical serialized inputs and outputs; it does not prove that a formula is scientifically appropriate for every context.
- External live data, authentication, graph persistence, and independent replication remain future experimental work.
