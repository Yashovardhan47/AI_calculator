CREATE TABLE IF NOT EXISTS calcgraphs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calculation_history_id UUID REFERENCES calculation_history(id) ON DELETE CASCADE,
    graph_version VARCHAR(30) NOT NULL,
    graph_fingerprint CHAR(64) NOT NULL,
    status VARCHAR(30) NOT NULL CHECK (status IN ('compiled', 'verified', 'executed', 'rejected')),
    goal TEXT NOT NULL,
    calculator_id VARCHAR(80) NOT NULL,
    graph JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (graph_fingerprint, calculation_history_id)
);

CREATE INDEX IF NOT EXISTS idx_calcgraphs_fingerprint ON calcgraphs (graph_fingerprint);
CREATE INDEX IF NOT EXISTS idx_calcgraphs_calculator_created ON calcgraphs (calculator_id, created_at DESC);

CREATE TABLE IF NOT EXISTS calculation_receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calcgraph_id UUID NOT NULL REFERENCES calcgraphs(id) ON DELETE CASCADE,
    engine_version VARCHAR(30) NOT NULL,
    result_digest CHAR(64) NOT NULL,
    reproducibility_hash CHAR(64) NOT NULL,
    verification_report JSONB NOT NULL,
    formula_provenance JSONB NOT NULL,
    executed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (reproducibility_hash, calcgraph_id)
);

CREATE INDEX IF NOT EXISTS idx_receipts_reproducibility_hash ON calculation_receipts (reproducibility_hash);

CREATE TABLE IF NOT EXISTS formula_registry (
    operation VARCHAR(120) NOT NULL,
    formula_version VARCHAR(30) NOT NULL,
    formula_id VARCHAR(160) NOT NULL,
    input_signature JSONB NOT NULL,
    output_type VARCHAR(100) NOT NULL,
    equation TEXT NOT NULL,
    source TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (operation, formula_version)
);
