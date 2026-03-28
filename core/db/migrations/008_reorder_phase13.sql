CREATE TABLE IF NOT EXISTS predictions.reorder_recommendations (
    recommendation_run_id TEXT NOT NULL,
    upload_id TEXT NOT NULL,
    sku TEXT NOT NULL,
    store_code TEXT NOT NULL DEFAULT 'unknown',
    as_of_date DATE NOT NULL,
    reorder_date DATE NOT NULL,
    reorder_quantity NUMERIC(18, 4) NOT NULL,
    urgency TEXT NOT NULL,
    urgency_score NUMERIC(10, 4) NOT NULL,
    stockout_probability NUMERIC(10, 4) NOT NULL,
    days_to_stockout NUMERIC(18, 4) NOT NULL,
    lead_time_days NUMERIC(18, 4) NOT NULL,
    supplier_moq NUMERIC(18, 4) NOT NULL,
    service_level_target NUMERIC(10, 4) NOT NULL,
    rationale TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (recommendation_run_id, sku, store_code)
);

CREATE INDEX IF NOT EXISTS idx_reorder_recommendations_upload_id
    ON predictions.reorder_recommendations (upload_id, reorder_date DESC);
