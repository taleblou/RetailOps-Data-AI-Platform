
  
    

  create  table "retailops"."analytics_mart"."dim_product__dbt_tmp"
  
  
    as
  
  (
    select
    product_id,
    sku,
    product_name,
    category,
    unit_price,
    is_active,
    ingested_at as record_loaded_at
from "retailops"."analytics_staging"."stg_products"
  );
  