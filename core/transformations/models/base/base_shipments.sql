select
    shipment_id,
    order_id,
    store_id,
    carrier,
    shipment_status,
    promised_date,
    actual_delivery_date,
    ingested_at
from {{ source('raw', 'shipments') }}
