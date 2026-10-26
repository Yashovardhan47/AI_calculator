CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(320) UNIQUE NOT NULL,
    display_name VARCHAR(120),
    password_hash TEXT,
    auth_provider VARCHAR(30) NOT NULL DEFAULT 'local' CHECK (auth_provider IN ('local', 'google', 'linked')),
    google_sub VARCHAR(255) UNIQUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    avatar_url TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled')),
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash CHAR(64) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_active
    ON refresh_tokens (user_id, expires_at DESC) WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS calculation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    anonymous_session_id UUID,
    original_query TEXT NOT NULL,
    normalized_query TEXT,
    calculator_id VARCHAR(80) NOT NULL,
    result JSONB NOT NULL,
    routing_source VARCHAR(40) NOT NULL DEFAULT 'local',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (user_id IS NOT NULL OR anonymous_session_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_calculation_history_user_created
    ON calculation_history (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_calculation_history_session_created
    ON calculation_history (anonymous_session_id, created_at DESC);

CREATE TABLE IF NOT EXISTS saved_workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(160) NOT NULL,
    description TEXT,
    workflow_definition JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS provider_rate_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(100) NOT NULL,
    rate_type VARCHAR(100) NOT NULL,
    source_unit VARCHAR(30),
    target_unit VARCHAR(30),
    rate NUMERIC(30, 12) NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL,
    raw_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (provider, rate_type, source_unit, target_unit, retrieved_at)
);

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
