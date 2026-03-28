select
    max(order_date) as latest_business_date,
    sum(total_revenue) as total_revenue,
    sum(total_orders) as total_orders,
    case when sum(total_orders) = 0 then 0 else sum(total_revenue) / sum(total_orders) end as avg_order_value,
    sum(low_stock_items) as low_stock_items,
    avg(on_time_rate) as avg_on_time_rate
from mart.mart_store_kpis;
