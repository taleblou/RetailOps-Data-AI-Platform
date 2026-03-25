
  create view "retailops"."analytics_staging"."base_shipments__dbt_tmp"
    
    
  as (
    select
    shipment_id,
    order_id,
    store_id,
    carrier,
    shipment_status,
    promised_date,
    actual_delivery_date,
    ingested_at
from "retailops"."raw"."shipments"
  );