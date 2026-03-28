with base as (
    select
        snapshot_date,
        store_id,
        product_id,
        on_hand_qty,
        reserved_qty,
        available_qty,
        in_transit_qty
    from mart.inventory_snapshots
),
demand as (
    select
        feature_date,
        store_id,
        product_id,
        units_sold_7d
    from features.product_demand_daily
)
select
    b.snapshot_date,
    b.store_id,
    b.product_id,
    b.on_hand_qty,
    b.reserved_qty,
    b.available_qty,
    b.in_transit_qty,
    case
        when coalesce(d.units_sold_7d, 0) = 0 then 999
        else round(b.available_qty / nullif(d.units_sold_7d / 7.0, 0), 2)
    end as days_of_cover_estimate,
    case
        when b.available_qty <= 0 then true
        else false
    end as is_out_of_stock,
    now() as feature_generated_at
from base b
left join demand d
    on b.store_id = d.store_id
   and b.product_id = d.product_id
   and b.snapshot_date = d.feature_date;
