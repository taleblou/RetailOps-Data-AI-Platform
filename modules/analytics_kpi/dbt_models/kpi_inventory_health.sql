{{ config(alias='kpi_inventory_health', schema='mart', materialized='view', tags=['module', 'analytics_kpi']) }}

select
    snapshot_date,
    store_id,
    count(*) as sku_count,
    sum(case when is_out_of_stock then 1 else 0 end) as out_of_stock_sku_count,
    avg(available_qty) as avg_available_qty
from {{ ref('fct_inventory_daily') }}
group by 1, 2
