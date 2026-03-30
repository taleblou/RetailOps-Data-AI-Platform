CREATE TABLE IF NOT EXISTS predictions.forecast_batch_runs (
    forecast_run_id TEXT PRIMARY KEY,
    upload_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    nightly_batch_job TEXT NOT NULL,
    product_count INTEGER NOT NULL DEFAULT 0,
    summary JSONB NOT NULL DEFAULT '{}'::JSONB
);

CREATE TABLE IF NOT EXISTS predictions.product_demand_forecasts (
    forecast_run_id TEXT NOT NULL
        REFERENCES predictions.forecast_batch_runs(forecast_run_id)
        ON DELETE CASCADE,
    upload_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    category TEXT,
    product_group TEXT,
    horizon_days INTEGER NOT NULL,
    point_forecast NUMERIC(18, 2) NOT NULL DEFAULT 0,
    p10 NUMERIC(18, 2) NOT NULL DEFAULT 0,
    p50 NUMERIC(18, 2) NOT NULL DEFAULT 0,
    p90 NUMERIC(18, 2) NOT NULL DEFAULT 0,
    stockout_probability NUMERIC(18, 6) NOT NULL DEFAULT 0,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    feature_timestamp TIMESTAMPTZ NOT NULL,
    backtest_metrics JSONB NOT NULL DEFAULT '{}'::JSONB,
    explanation_summary TEXT,
    PRIMARY KEY (forecast_run_id, product_id, horizon_days)
);

CREATE INDEX IF NOT EXISTS idx_predictions_product_demand_forecasts_lookup
    ON predictions.product_demand_forecasts (upload_id, product_id, horizon_days);
