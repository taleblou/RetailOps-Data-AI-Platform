
  create view "retailops"."analytics_staging"."base_products__dbt_tmp"
    
    
  as (
    select
    product_id,
    sku,
    product_name,
    category,
    unit_price,
    is_active,
    ingested_at
from "retailops"."raw"."products"
  );