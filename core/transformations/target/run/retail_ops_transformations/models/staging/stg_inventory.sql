
  create view "retailops"."analytics_staging"."stg_inventory__dbt_tmp"
    
    
  as (
    select
    cast(store_id as bigint) as store_id,
    cast(product_id as bigint) as product_id,
    cast(snapshot_date as date) as snapshot_date,
    cast(on_hand_qty as integer) as on_hand_qty,
    cast(reserved_qty as integer) as reserved_qty,
    cast(available_qty as integer) as available_qty,
    cast(ingested_at as timestamp) as ingested_at
from "retailops"."analytics_staging"."base_inventory"
where product_id is not null
  );