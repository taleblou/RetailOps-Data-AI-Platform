select
    shipment_id,
    order_id,
    promised_date,
    delivered_date,
    delayed,
    delay_days
from mart.fct_shipments
order by promised_date desc, shipment_id;
