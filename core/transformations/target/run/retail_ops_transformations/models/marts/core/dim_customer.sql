
  
    

  create  table "retailops"."analytics_mart"."dim_customer__dbt_tmp"
  
  
    as
  
  (
    select distinct
    customer_id,
    min(order_ts) as first_order_ts,
    max(order_ts) as last_order_ts,
    count(*) as lifetime_order_count,
    sum(total_amount) as lifetime_revenue
from "retailops"."analytics_staging"."stg_orders"
where customer_id is not null
group by 1
  );
  