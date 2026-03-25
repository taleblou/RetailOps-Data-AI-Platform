with sales as (
    select
        order_date,
        store_id,
        gross_sales,
        order_count,
        customer_count,
        avg_order_value
    from "retailops"."analytics_mart"."fct_daily_sales"
),
shipments as (
    select
        store_id,
        count(*) as shipment_count,
        sum(case when is_delayed then 1 else 0 end) as delayed_shipment_count
    from "retailops"."analytics_mart"."fct_shipments"
    group by 1
),
inventory as (
    select
        store_id,
        snapshot_date,
        count(*) as sku_count,
        sum(case when is_out_of_stock then 1 else 0 end) as out_of_stock_sku_count,
        avg(available_qty) as avg_available_qty
    from "retailops"."analytics_mart"."fct_inventory_daily"
    group by 1, 2
)
select
    s.order_date,
    s.store_id,
    s.gross_sales,
    s.order_count,
    s.customer_count,
    s.avg_order_value,
    coalesce(sh.shipment_count, 0) as shipment_count,
    coalesce(sh.delayed_shipment_count, 0) as delayed_shipment_count,
    case
    when nullif(coalesce(sh.shipment_count, 0), 0) is null then null
    when nullif(coalesce(sh.shipment_count, 0), 0) = 0 then null
    else coalesce(sh.delayed_shipment_count, 0)::numeric / nullif(coalesce(sh.shipment_count, 0), 0)::numeric
end as delayed_shipment_rate,
    coalesce(i.sku_count, 0) as inventory_sku_count,
    coalesce(i.out_of_stock_sku_count, 0) as out_of_stock_sku_count,
    case
    when nullif(coalesce(i.sku_count, 0), 0) is null then null
    when nullif(coalesce(i.sku_count, 0), 0) = 0 then null
    else coalesce(i.out_of_stock_sku_count, 0)::numeric / nullif(coalesce(i.sku_count, 0), 0)::numeric
end as out_of_stock_rate,
    i.avg_available_qty
from sales s
left join shipments sh
    on s.store_id = sh.store_id
left join inventory i
    on s.store_id = i.store_id
   and s.order_date = i.snapshot_date