{{ config(alias='shipment_risk_features', schema='mart', materialized='view', tags=['module', 'shipment_risk']) }}

with shipments as (
    select
        shipment_id,
        order_id,
        store_id,
        carrier,
        promised_date,
        actual_delivery_date,
        is_delayed,
        coalesce(delivery_delay_days, 0) as delivery_delay_days
    from {{ ref('fct_shipments') }}
),
orders as (
    select
        order_id,
        customer_id,
        order_ts,
        order_status,
        total_amount
    from {{ ref('stg_orders') }}
)
select
    s.shipment_id,
    s.order_id,
    s.store_id,
    s.carrier,
    o.customer_id,
    extract(isodow from o.order_ts) as order_weekday,
    extract(hour from o.order_ts) as order_hour,
    o.order_status,
    o.total_amount,
    s.delivery_delay_days,
    s.is_delayed as label_is_delayed
from shipments s
left join orders o
    on s.order_id = o.order_id
