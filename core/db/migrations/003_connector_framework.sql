CREATE TABLE IF NOT EXISTS ops.sources (
    source_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops.connector_state (
    source_id BIGINT PRIMARY KEY REFERENCES ops.sources(source_id) ON DELETE CASCADE,
    last_sync_at TIMESTAMPTZ,
    cursor_value TEXT,
    error_count INTEGER NOT NULL DEFAULT 0,
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    last_run_status TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ops.connector_errors (
    connector_error_id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES ops.sources(source_id) ON DELETE CASCADE,
    error_type TEXT NOT NULL,
    message TEXT NOT NULL,
    details_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.import_rows (
    raw_row_id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL REFERENCES ops.sources(source_id) ON DELETE CASCADE,
    import_job_id BIGINT NOT NULL REFERENCES ops.import_jobs(import_job_id) ON DELETE CASCADE,
    row_num INTEGER NOT NULL,
    payload_json JSONB NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sources_type ON ops.sources(type);
CREATE INDEX IF NOT EXISTS idx_connector_errors_source_id ON ops.connector_errors(source_id);
CREATE INDEX IF NOT EXISTS idx_raw_import_rows_source_id ON raw.import_rows(source_id);
