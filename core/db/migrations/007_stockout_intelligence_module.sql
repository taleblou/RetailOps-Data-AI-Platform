create schema if not exists predictions;

create table if not exists predictions.stockout_risk_daily (
    stockout_run_id text not null,
    as_of_date date not null,
    store_code text not null,
    sku text not null,
    available_qty numeric(18, 2) not null,
    inbound_qty numeric(18, 2) not null default 0,
    avg_daily_demand_7d numeric(18, 4) not null,
    avg_daily_demand_28d numeric(18, 4) not null,
    demand_trend_ratio numeric(18, 4) not null,
    days_to_stockout numeric(18, 2) not null,
    lead_time_days numeric(18, 2) not null,
    stockout_probability numeric(10, 4) not null,
    reorder_urgency_score numeric(10, 2) not null,
    expected_lost_sales_estimate numeric(18, 2) not null,
    risk_band text not null,
    recommended_action text not null,
    feature_timestamp timestamptz not null,
    explanation_summary text not null,
    created_at timestamptz not null default now(),
    primary key (stockout_run_id, store_code, sku)
);

create index if not exists idx_stockout_risk_daily_sku_date
    on predictions.stockout_risk_daily (sku, as_of_date desc);
