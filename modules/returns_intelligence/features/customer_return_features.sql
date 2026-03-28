with order_lines as (
    select
        o.customer_id,
        oi.product_id,
        o.ordered_at::date as feature_date,
        count(*) over (
            partition by o.customer_id
            order by o.ordered_at::date
            range between interval '89 day' preceding and current row
        ) as customer_orders_90d,
        avg(case when lower(coalesce(o.order_status, '')) = 'returned' then 1.0 else 0.0 end) over (
            partition by o.customer_id
            order by o.ordered_at::date
            range between interval '179 day' preceding and current row
        ) as customer_return_rate_180d,
        avg(case when lower(coalesce(o.order_status, '')) = 'returned' then 1.0 else 0.0 end) over (
            partition by oi.product_id
            order by o.ordered_at::date
            range between interval '179 day' preceding and current row
        ) as product_return_rate_180d,
        coalesce(oi.discount_amount / nullif(oi.line_total + oi.discount_amount, 0), 0) as discount_rate,
        case
            when s.delivered_at is not null and s.promised_delivery_at is not null and s.delivered_at > s.promised_delivery_at
            then true else false
        end as delayed_delivery_flag
    from mart.orders o
    join mart.order_items oi
        on o.order_id = oi.order_id
    left join mart.shipments s
        on o.order_id = s.order_id
)
select
    feature_date,
    customer_id,
    product_id,
    customer_orders_90d,
    coalesce(customer_return_rate_180d, 0) as customer_return_rate_180d,
    coalesce(product_return_rate_180d, 0) as product_return_rate_180d,
    discount_rate,
    delayed_delivery_flag,
    now() as feature_generated_at
from order_lines;
