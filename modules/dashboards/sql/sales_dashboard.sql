select
    order_date,
    store_id,
    total_revenue,
    total_orders,
    total_quantity
from mart.fct_daily_sales
order by order_date desc, store_id;
