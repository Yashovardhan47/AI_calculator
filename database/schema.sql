CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(320) UNIQUE,
    display_name VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

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

