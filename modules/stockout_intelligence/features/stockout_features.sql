with inventory as (
    select
        snapshot_date as feature_date,
        store_id,
        product_id,
        available_qty,
        in_transit_qty,
        days_of_cover_estimate,
        is_out_of_stock
    from features.inventory_position_daily
),
demand as (
    select
        feature_date,
        store_id,
        product_id,
        units_sold_7d,
        units_sold_28d,
        demand_trend_7d_vs_28d
    from features.product_demand_daily
),
stockout_history as (
    select
        feature_date,
        store_id,
        product_id,
        sum(case when is_out_of_stock then 1 else 0 end) over (
            partition by store_id, product_id
            order by feature_date
            rows between 13 preceding and current row
        ) as recent_stockout_days_14d
    from inventory
)
select
    i.feature_date,
    i.store_id,
    i.product_id,
    i.available_qty,
    i.in_transit_qty as inbound_qty,
    coalesce(d.units_sold_7d, 0) as units_sold_7d,
    coalesce(d.units_sold_28d, 0) as units_sold_28d,
    coalesce(d.demand_trend_7d_vs_28d, 0) as demand_trend_7d_vs_28d,
    i.days_of_cover_estimate,
    coalesce(h.recent_stockout_days_14d, 0) as recent_stockout_days_14d,
    now() as feature_generated_at
from inventory i
left join demand d
    on i.store_id = d.store_id
   and i.product_id = d.product_id
   and i.feature_date = d.feature_date
left join stockout_history h
    on i.store_id = h.store_id
   and i.product_id = h.product_id
   and i.feature_date = h.feature_date;
