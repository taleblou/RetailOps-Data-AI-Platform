select
    product_id,
    sku,
    product_name,
    category,
    unit_price,
    is_active,
    ingested_at as record_loaded_at
from {{ ref('stg_products') }}
