select
    store_id,
    product_id,
    snapshot_date,
    on_hand_qty,
    reserved_qty,
    available_qty,
    ingested_at
from {{ source('raw', 'inventory_snapshots') }}
