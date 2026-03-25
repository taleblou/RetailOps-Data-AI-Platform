
  create view "retailops"."analytics_staging"."base_inventory__dbt_tmp"
    
    
  as (
    select
    store_id,
    product_id,
    snapshot_date,
    on_hand_qty,
    reserved_qty,
    available_qty,
    ingested_at
from "retailops"."raw"."inventory_snapshots"
  );