{{ config(alias='kpi_sales_daily', schema='mart', materialized='view', tags=['module', 'analytics_kpi']) }}

select
    order_date,
    store_id,
    gross_sales,
    order_count,
    customer_count,
    avg_order_value
from {{ ref('mart_store_kpis') }}
