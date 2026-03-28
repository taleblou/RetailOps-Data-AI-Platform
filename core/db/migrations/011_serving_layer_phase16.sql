CREATE TABLE IF NOT EXISTS ops.serving_runs (
    serving_run_id TEXT PRIMARY KEY,
    upload_id TEXT NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL,
    forecast_artifact_path TEXT NOT NULL,
    stockout_artifact_path TEXT NOT NULL,
    shipment_artifact_path TEXT NOT NULL,
    available_online_endpoints JSONB NOT NULL DEFAULT '[]'::jsonb,
    standard_response_fields JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_serving_runs_upload_id
    ON ops.serving_runs (upload_id, generated_at DESC);

CREATE TABLE IF NOT EXISTS ops.serving_requests (
    request_id TEXT PRIMARY KEY,
    serving_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    feature_timestamp TIMESTAMPTZ,
    prediction_payload JSONB NOT NULL,
    confidence NUMERIC(10, 4),
    interval_payload JSONB,
    explanation_summary TEXT,
    source_artifact TEXT NOT NULL,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_serving_requests_type_time
    ON ops.serving_requests (serving_type, requested_at DESC);
