
  create view "retailops"."analytics_mart"."forecast_training_base__dbt_tmp"
    
    
  as (
    

select
    inv.snapshot_date as ds,
    inv.product_id,
    prod.category,
    inv.store_id,
    inv.on_hand_qty,
    inv.available_qty,
    coalesce(sales.gross_sales, 0) as store_daily_sales,
    coalesce(sales.order_count, 0) as store_daily_orders,
    kpi.out_of_stock_rate as store_out_of_stock_rate
from "retailops"."analytics_mart"."fct_inventory_daily" inv
left join "retailops"."analytics_mart"."dim_product" prod
    on inv.product_id = prod.product_id
left join "retailops"."analytics_mart"."fct_daily_sales" sales
    on inv.snapshot_date = sales.order_date
   and inv.store_id = sales.store_id
left join "retailops"."analytics_mart"."mart_store_kpis" kpi
    on inv.snapshot_date = kpi.order_date
   and inv.store_id = kpi.store_id
where prod.is_active = true
  );