CREATE SCHEMA IF NOT EXISTS ops;

CREATE TABLE IF NOT EXISTS ops.setup_sessions (
    session_id TEXT PRIMARY KEY,
    store_name TEXT NOT NULL,
    store_code TEXT NOT NULL,
    sample_mode BOOLEAN NOT NULL DEFAULT FALSE,
    source_type TEXT,
    enabled_modules_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    state_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops.setup_session_logs (
    log_id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES ops.setup_sessions(session_id) ON DELETE CASCADE,
    step_key TEXT NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_setup_session_logs_session_id_created_at
    ON ops.setup_session_logs(session_id, created_at DESC);
