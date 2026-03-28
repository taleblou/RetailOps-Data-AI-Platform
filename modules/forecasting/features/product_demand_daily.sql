with order_lines as (
    select
        o.store_id,
        oi.product_id,
        o.ordered_at::date as feature_date,
        sum(oi.quantity) as units_sold_1d,
        sum(oi.line_total) as revenue_1d
    from mart.orders o
    join mart.order_items oi
        on o.order_id = oi.order_id
    group by 1, 2, 3
),
rolling as (
    select
        store_id,
        product_id,
        feature_date,
        units_sold_1d,
        revenue_1d,
        sum(units_sold_1d) over (
            partition by store_id, product_id
            order by feature_date
            rows between 6 preceding and current row
        ) as units_sold_7d,
        sum(revenue_1d) over (
            partition by store_id, product_id
            order by feature_date
            rows between 6 preceding and current row
        ) as revenue_7d,
        sum(units_sold_1d) over (
            partition by store_id, product_id
            order by feature_date
            rows between 27 preceding and current row
        ) as units_sold_28d
    from order_lines
)
select
    feature_date,
    store_id,
    product_id,
    units_sold_1d,
    revenue_1d,
    units_sold_7d,
    revenue_7d,
    units_sold_28d,
    case
        when units_sold_28d = 0 then 0
        else round((units_sold_7d / 7.0) / nullif(units_sold_28d / 28.0, 0), 6)
    end as demand_trend_7d_vs_28d,
    now() as feature_generated_at
from rolling;
