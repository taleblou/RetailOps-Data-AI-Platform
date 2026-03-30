create table if not exists features.return_risk_features (
    feature_date date not null,
    order_id text not null,
    customer_id text not null,
    sku text not null,
    store_code text not null,
    category text not null,
    discount_rate numeric(10, 4) not null default 0,
    shipment_delay_days numeric(10, 2) not null default 0,
    customer_return_rate_180d numeric(10, 4) not null default 0,
    sku_return_rate_180d numeric(10, 4) not null default 0,
    feature_generated_at timestamptz not null default now(),
    primary key (feature_date, order_id)
);

create index if not exists idx_return_risk_features_sku_date
    on features.return_risk_features (sku, feature_date desc);

create table if not exists predictions.return_risk_scores (
    return_risk_run_id text not null,
    order_id text not null,
    customer_id text not null,
    sku text not null,
    store_code text not null,
    score_date date not null,
    return_probability numeric(10, 4) not null,
    expected_return_cost numeric(12, 2) not null,
    risk_band text not null,
    return_cost_band text not null,
    recommended_action text not null,
    model_version text not null,
    feature_timestamp timestamptz not null,
    created_at timestamptz not null default now(),
    primary key (return_risk_run_id, order_id)
);

create index if not exists idx_return_risk_scores_probability
    on predictions.return_risk_scores (score_date desc, return_probability desc);
