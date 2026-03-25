select
    cast(shipment_id as bigint) as shipment_id,
    cast(order_id as bigint) as order_id,
    cast(store_id as bigint) as store_id,
    trim(cast(carrier as text)) as carrier,
    lower(trim(cast(shipment_status as text))) as shipment_status,
    cast(promised_date as date) as promised_date,
    cast(actual_delivery_date as date) as actual_delivery_date,
    cast(ingested_at as timestamp) as ingested_at
from {{ ref('base_shipments') }}
where shipment_id is not null
