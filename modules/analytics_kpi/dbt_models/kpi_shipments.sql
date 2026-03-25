{{ config(alias='kpi_shipments', schema='mart', materialized='view', tags=['module', 'analytics_kpi']) }}

select
    store_id,
    carrier,
    count(*) as shipment_count,
    sum(case when is_delayed then 1 else 0 end) as delayed_shipment_count,
    {{ safe_divide('sum(case when is_delayed then 1 else 0 end)', 'count(*)') }} as delayed_shipment_rate
from {{ ref('fct_shipments') }}
group by 1, 2
