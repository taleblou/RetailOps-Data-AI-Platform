select
    order_id,
    customer_id,
    store_id,
    order_ts,
    status,
    total_amount,
    currency,
    ingested_at
from "retailops"."raw"."orders"