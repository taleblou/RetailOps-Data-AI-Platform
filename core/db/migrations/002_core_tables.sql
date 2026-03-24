CREATE TABLE IF NOT EXISTS mart.stores (
    store_id BIGSERIAL PRIMARY KEY,
    store_code TEXT UNIQUE NOT NULL,
    store_name TEXT NOT NULL,
    country TEXT,
    city TEXT,
    timezone TEXT,
    currency_code TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mart.stores (
    store_id BIGSERIAL PRIMARY KEY,
    store_code TEXT UNIQUE NOT NULL,
    store_name TEXT NOT NULL,
    country TEXT,
    city TEXT,
    timezone TEXT,
    currency_code TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mart.stores (
    store_id BIGSERIAL PRIMARY KEY,
    store_code TEXT UNIQUE NOT NULL,
    store_name TEXT NOT NULL,
    country TEXT,
    city TEXT,
    timezone TEXT,
    currency_code TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mart.stores (
    store_id BIGSERIAL PRIMARY KEY,
    store_code TEXT UNIQUE NOT NULL,
    store_name TEXT NOT NULL,
    country TEXT,
    city TEXT,
    timezone TEXT,
    currency_code TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mart.order_items (
    order_item_id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES mart.orders(order_id) ON DELETE CASCADE,
    product_id BIGINT REFERENCES mart.products(product_id),
    sku TEXT,
    quantity NUMERIC(12,2) NOT NULL,
    unit_price NUMERIC(12,2),
    discount_amount NUMERIC(12,2),
    line_total NUMERIC(12,2)
);

CREATE TABLE IF NOT EXISTS mart.payments (
    payment_id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES mart.orders(order_id) ON DELETE CASCADE,
    payment_method TEXT,
    payment_status TEXT,
    paid_amount NUMERIC(12,2),
    paid_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS mart.shipments (
    shipment_id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES mart.orders(order_id) ON DELETE CASCADE,
    shipment_status TEXT,
    carrier_name TEXT,
    tracking_number TEXT,
    shipped_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    promised_delivery_at TIMESTAMPTZ
);


CREATE TABLE IF NOT EXISTS mart.inventory_snapshots (
    inventory_snapshot_id BIGSERIAL PRIMARY KEY,
    store_id BIGINT NOT NULL REFERENCES mart.stores(store_id),
    product_id BIGINT NOT NULL REFERENCES mart.products(product_id),
    snapshot_date DATE NOT NULL,
    on_hand_qty NUMERIC(12,2) NOT NULL,
    reserved_qty NUMERIC(12,2) NOT NULL DEFAULT 0,
    available_qty NUMERIC(12,2) NOT NULL DEFAULT 0,
    in_transit_qty NUMERIC(12,2) NOT NULL DEFAULT 0,
    UNIQUE (store_id, product_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS mart.promotions (
    promotion_id BIGSERIAL PRIMARY KEY,
    store_id BIGINT NOT NULL REFERENCES mart.stores(store_id),
    promotion_name TEXT NOT NULL,
    promotion_type TEXT,
    start_at TIMESTAMPTZ,
    end_at TIMESTAMPTZ,
    discount_value NUMERIC(12,2),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS ops.import_jobs (
    import_job_id BIGSERIAL PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_name TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    rows_received BIGINT DEFAULT 0,
    rows_loaded BIGINT DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS ops.sync_runs (
    sync_run_id BIGSERIAL PRIMARY KEY,
    connector_name TEXT NOT NULL,
    sync_mode TEXT,
    status TEXT NOT NULL,
    cursor_value TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    rows_processed BIGINT DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS ops.dq_results (
    dq_result_id BIGSERIAL PRIMARY KEY,
    check_name TEXT NOT NULL,
    check_scope TEXT NOT NULL,
    status TEXT NOT NULL,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    affected_rows BIGINT DEFAULT 0,
    details JSONB
);

CREATE TABLE IF NOT EXISTS ops.model_runs (
    model_run_id BIGSERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    model_version TEXT,
    run_type TEXT,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    metrics JSONB,
    params JSONB
);

CREATE TABLE IF NOT EXISTS ops.prediction_runs (
    prediction_run_id BIGSERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    model_version TEXT,
    target_name TEXT,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    row_count BIGINT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ops.drift_runs (
    drift_run_id BIGSERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    feature_set_name TEXT,
    status TEXT NOT NULL,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    summary JSONB
);

CREATE TABLE IF NOT EXISTS ops.override_logs (
    override_log_id BIGSERIAL PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    reason TEXT,
    changed_by TEXT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw.orders_csv_import (
    raw_id BIGSERIAL PRIMARY KEY,
    import_job_id BIGINT,
    payload JSONB NOT NULL,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);