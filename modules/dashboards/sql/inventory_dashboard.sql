select
    snapshot_date,
    store_id,
    product_id,
    sku,
    on_hand_quantity,
    days_of_cover,
    case when days_of_cover <= 7 then true else false end as low_stock
from mart.fct_inventory_daily
order by snapshot_date desc, days_of_cover asc, sku;
