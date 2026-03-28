CREATE TABLE IF NOT EXISTS ops.ml_experiment_runs (
    experiment_run_id BIGSERIAL PRIMARY KEY,
    registry_name TEXT NOT NULL,
    run_id TEXT NOT NULL UNIQUE,
    model_version TEXT NOT NULL,
    source_module TEXT NOT NULL,
    source_artifact TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metrics_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    baseline_metrics_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    calibration_error DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    drift_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    evaluation_passed BOOLEAN NOT NULL DEFAULT FALSE,
    promotion_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    tags_json JSONB NOT NULL DEFAULT '[]'::JSONB,
    explanation_summary TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_ml_experiment_runs_registry_name
    ON ops.ml_experiment_runs (registry_name);

CREATE INDEX IF NOT EXISTS idx_ml_experiment_runs_model_version
    ON ops.ml_experiment_runs (model_version);

CREATE TABLE IF NOT EXISTS ops.ml_registry_aliases (
    registry_alias_id BIGSERIAL PRIMARY KEY,
    registry_name TEXT NOT NULL,
    alias_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by TEXT NOT NULL DEFAULT 'phase15-bootstrap',
    UNIQUE (registry_name, alias_name)
);

CREATE INDEX IF NOT EXISTS idx_ml_registry_aliases_registry_name
    ON ops.ml_registry_aliases (registry_name);

CREATE TABLE IF NOT EXISTS ops.ml_registry_events (
    registry_event_id BIGSERIAL PRIMARY KEY,
    registry_name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    from_aliases_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    to_aliases_json JSONB NOT NULL DEFAULT '{}'::JSONB,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_ml_registry_events_registry_name
    ON ops.ml_registry_events (registry_name);
