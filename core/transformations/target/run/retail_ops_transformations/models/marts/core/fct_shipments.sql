
  
    

  create  table "retailops"."analytics_mart"."fct_shipments__dbt_tmp"
  
  
    as
  
  (
    select
    shipment_id,
    order_id,
    store_id,
    carrier,
    shipment_status,
    promised_date,
    actual_delivery_date,
    case
        when actual_delivery_date is not null
         and promised_date is not null
         and actual_delivery_date > promised_date
        then true
        else false
    end as is_delayed,
    case
        when actual_delivery_date is null or promised_date is null then null
        else actual_delivery_date - promised_date
    end as delivery_delay_days
from "retailops"."analytics_staging"."stg_shipments"
  );
  