CREATE TABLE IF NOT EXISTS features.product_demand_daily (
    feature_date DATE NOT NULL,
    store_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    units_sold_1d NUMERIC(18, 2) NOT NULL DEFAULT 0,
    revenue_1d NUMERIC(18, 2) NOT NULL DEFAULT 0,
    units_sold_7d NUMERIC(18, 2) NOT NULL DEFAULT 0,
    revenue_7d NUMERIC(18, 2) NOT NULL DEFAULT 0,
    units_sold_28d NUMERIC(18, 2) NOT NULL DEFAULT 0,
    demand_trend_7d_vs_28d NUMERIC(18, 6) NOT NULL DEFAULT 0,
    feature_generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (feature_date, store_id, product_id)
);

CREATE TABLE IF NOT EXISTS features.inventory_position_daily (
    snapshot_date DATE NOT NULL,
    store_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    on_hand_qty NUMERIC(18, 2) NOT NULL DEFAULT 0,
    reserved_qty NUMERIC(18, 2) NOT NULL DEFAULT 0,
    available_qty NUMERIC(18, 2) NOT NULL DEFAULT 0,
    in_transit_qty NUMERIC(18, 2) NOT NULL DEFAULT 0,
    days_of_cover_estimate NUMERIC(18, 2) NOT NULL DEFAULT 0,
    is_out_of_stock BOOLEAN NOT NULL DEFAULT FALSE,
    feature_generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (snapshot_date, store_id, product_id)
);

CREATE TABLE IF NOT EXISTS features.shipment_delay_features (
    shipment_id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    store_id BIGINT NOT NULL,
    feature_ts TIMESTAMPTZ NOT NULL,
    order_hour INTEGER,
    order_weekday INTEGER,
    promised_lead_days NUMERIC(18, 2) NOT NULL DEFAULT 0,
    warehouse_backlog_7d NUMERIC(18, 2) NOT NULL DEFAULT 0,
    carrier_delay_rate_30d NUMERIC(18, 6) NOT NULL DEFAULT 0,
    store_delay_rate_30d NUMERIC(18, 6) NOT NULL DEFAULT 0,
    label_is_delayed BOOLEAN,
    feature_generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS features.stockout_features (
    feature_date DATE NOT NULL,
    store_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    available_qty NUMERIC(18, 2) NOT NULL DEFAULT 0,
    inbound_qty NUMERIC(18, 2) NOT NULL DEFAULT 0,
    units_sold_7d NUMERIC(18, 2) NOT NULL DEFAULT 0,
    units_sold_28d NUMERIC(18, 2) NOT NULL DEFAULT 0,
    demand_trend_7d_vs_28d NUMERIC(18, 6) NOT NULL DEFAULT 0,
    days_of_cover_estimate NUMERIC(18, 2) NOT NULL DEFAULT 0,
    recent_stockout_days_14d INTEGER NOT NULL DEFAULT 0,
    feature_generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (feature_date, store_id, product_id)
);

CREATE TABLE IF NOT EXISTS features.customer_return_features (
    feature_date DATE NOT NULL,
    customer_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    customer_orders_90d NUMERIC(18, 2) NOT NULL DEFAULT 0,
    customer_return_rate_180d NUMERIC(18, 6) NOT NULL DEFAULT 0,
    product_return_rate_180d NUMERIC(18, 6) NOT NULL DEFAULT 0,
    discount_rate NUMERIC(18, 6) NOT NULL DEFAULT 0,
    delayed_delivery_flag BOOLEAN NOT NULL DEFAULT FALSE,
    feature_generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (feature_date, customer_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_features_product_demand_lookup
    ON features.product_demand_daily (store_id, product_id, feature_date DESC);

CREATE INDEX IF NOT EXISTS idx_features_inventory_position_lookup
    ON features.inventory_position_daily (store_id, product_id, snapshot_date DESC);

CREATE INDEX IF NOT EXISTS idx_features_stockout_lookup
    ON features.stockout_features (store_id, product_id, feature_date DESC);
