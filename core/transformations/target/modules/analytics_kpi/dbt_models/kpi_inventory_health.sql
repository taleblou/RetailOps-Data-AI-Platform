
  create view "retailops"."analytics_mart"."kpi_inventory_health__dbt_tmp"
    
    
  as (
    

select
    snapshot_date,
    store_id,
    count(*) as sku_count,
    sum(case when is_out_of_stock then 1 else 0 end) as out_of_stock_sku_count,
    avg(available_qty) as avg_available_qty
from "retailops"."analytics_mart"."fct_inventory_daily"
group by 1, 2
  );