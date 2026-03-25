select
    cast(product_id as bigint) as product_id,
    trim(cast(sku as text)) as sku,
    trim(cast(product_name as text)) as product_name,
    trim(cast(category as text)) as category,
    cast(unit_price as numeric(18, 2)) as unit_price,
    cast(is_active as boolean) as is_active,
    cast(ingested_at as timestamp) as ingested_at
from {{ ref('base_products') }}
where product_id is not null
