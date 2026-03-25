select
    cast(order_id as bigint) as order_id,
    cast(customer_id as bigint) as customer_id,
    cast(store_id as bigint) as store_id,
    cast(order_ts as timestamp) as order_ts,
    cast(order_ts as date) as order_date,
    lower(trim(cast(status as text))) as order_status,
    cast(total_amount as numeric(18, 2)) as total_amount,
    upper(trim(cast(currency as text))) as currency,
    cast(ingested_at as timestamp) as ingested_at
from {{ ref('base_orders') }}
where order_id is not null
