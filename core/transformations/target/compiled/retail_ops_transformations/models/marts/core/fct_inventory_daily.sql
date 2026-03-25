select
    snapshot_date,
    store_id,
    product_id,
    on_hand_qty,
    reserved_qty,
    available_qty,
    case
        when available_qty <= 0 then true
        else false
    end as is_out_of_stock
from "retailops"."analytics_staging"."stg_inventory"