CREATE TABLE IF NOT EXISTS ops.monitoring_runs (
    monitoring_run_id TEXT PRIMARY KEY,
    upload_id TEXT NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_row_count INTEGER NOT NULL DEFAULT 0,
    source_file_count INTEGER NOT NULL DEFAULT 0,
    total_alerts INTEGER NOT NULL DEFAULT 0,
    warning_alerts INTEGER NOT NULL DEFAULT 0,
    critical_alerts INTEGER NOT NULL DEFAULT 0,
    retrain_recommended BOOLEAN NOT NULL DEFAULT FALSE,
    disable_prediction_recommended BOOLEAN NOT NULL DEFAULT FALSE,
    model_usage_total INTEGER NOT NULL DEFAULT 0,
    model_coverage NUMERIC(10, 4) NOT NULL DEFAULT 0.0,
    abstention_rate NUMERIC(10, 4) NOT NULL DEFAULT 0.0,
    api_latency_ms NUMERIC(10, 2) NOT NULL DEFAULT 0.0,
    data_checks_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    ml_checks_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    dashboard_metrics_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    alerts_json JSONB NOT NULL DEFAULT '[]'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_monitoring_runs_upload_id
    ON ops.monitoring_runs (upload_id, generated_at DESC);

CREATE TABLE IF NOT EXISTS ops.monitoring_alerts (
    alert_id TEXT PRIMARY KEY,
    monitoring_run_id TEXT NOT NULL REFERENCES ops.monitoring_runs (monitoring_run_id),
    severity TEXT NOT NULL,
    category TEXT NOT NULL,
    check_name TEXT NOT NULL,
    message TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    retrain_recommended BOOLEAN NOT NULL DEFAULT FALSE,
    disable_prediction_recommended BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_run_id
    ON ops.monitoring_alerts (monitoring_run_id);

CREATE TABLE IF NOT EXISTS ops.monitoring_override_feedback (
    override_id TEXT PRIMARY KEY,
    upload_id TEXT NOT NULL,
    prediction_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    original_decision JSONB NOT NULL,
    override_decision JSONB NOT NULL,
    reason TEXT NOT NULL,
    feedback_label TEXT,
    user_id TEXT,
    retraining_feedback_kept BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_monitoring_override_feedback_upload_id
    ON ops.monitoring_override_feedback (upload_id, created_at DESC);
