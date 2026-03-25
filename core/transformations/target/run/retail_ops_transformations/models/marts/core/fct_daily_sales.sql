
  
    

  create  table "retailops"."analytics_mart"."fct_daily_sales__dbt_tmp"
  
  
    as
  
  (
    select
    order_date,
    store_id,
    count(*) as order_count,
    count(distinct customer_id) as customer_count,
    sum(total_amount) as gross_sales,
    avg(total_amount) as avg_order_value
from "retailops"."analytics_staging"."stg_orders"
group by 1, 2
  );
  