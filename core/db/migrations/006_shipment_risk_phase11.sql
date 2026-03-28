create schema if not exists predictions;
create schema if not exists ops;

create table if not exists predictions.shipment_risk_scores (
    shipment_risk_run_id text not null,
    shipment_id text not null,
    order_id text,
    store_code text,
    carrier text,
    shipment_status text,
    promised_date date,
    actual_delivery_date date,
    delay_probability numeric(6, 4) not null,
    risk_band text not null,
    top_factors jsonb not null default '[]'::jsonb,
    recommended_action text not null,
    manual_review_required boolean not null default false,
    manual_review_reason text,
    feature_timestamp timestamptz,
    model_version text not null,
    explanation_summary text,
    created_at timestamptz not null default now(),
    primary key (shipment_risk_run_id, shipment_id)
);

create table if not exists ops.shipment_manual_review_queue (
    shipment_risk_run_id text not null,
    shipment_id text not null,
    order_id text,
    priority text not null,
    reason text not null,
    suggested_owner text not null default 'store-ops',
    status text not null default 'open',
    created_at timestamptz not null default now(),
    reviewed_at timestamptz,
    reviewer text,
    review_notes text,
    primary key (shipment_risk_run_id, shipment_id)
);

create index if not exists idx_shipment_risk_scores_probability
    on predictions.shipment_risk_scores (delay_probability desc);

create index if not exists idx_shipment_manual_review_status
    on ops.shipment_manual_review_queue (status, created_at desc);
