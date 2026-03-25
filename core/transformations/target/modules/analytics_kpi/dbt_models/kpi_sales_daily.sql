
  create view "retailops"."analytics_mart"."kpi_sales_daily__dbt_tmp"
    
    
  as (
    

select
    order_date,
    store_id,
    gross_sales,
    order_count,
    customer_count,
    avg_order_value
from "retailops"."analytics_mart"."mart_store_kpis"
  );