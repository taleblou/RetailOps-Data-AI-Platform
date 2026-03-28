with shipment_base as (
    select
        s.shipment_id,
        s.order_id,
        o.store_id,
        o.ordered_at,
        s.promised_delivery_at,
        s.delivered_at,
        extract(hour from o.ordered_at) as order_hour,
        extract(isodow from o.ordered_at) as order_weekday,
        extract(epoch from (s.promised_delivery_at - o.ordered_at)) / 86400.0 as promised_lead_days,
        case
            when s.delivered_at is not null and s.promised_delivery_at is not null and s.delivered_at > s.promised_delivery_at
            then true
            else false
        end as label_is_delayed
    from mart.shipments s
    join mart.orders o
        on s.order_id = o.order_id
),
carrier_history as (
    select
        current_s.shipment_id,
        avg(
            case
                when hist.delivered_at is not null and hist.promised_delivery_at is not null and hist.delivered_at > hist.promised_delivery_at
                then 1.0 else 0.0
            end
        ) as carrier_delay_rate_30d,
        count(*) as warehouse_backlog_7d
    from mart.shipments current_s
    left join mart.shipments hist
        on current_s.carrier_name = hist.carrier_name
       and hist.shipped_at < current_s.shipped_at
       and hist.shipped_at >= current_s.shipped_at - interval '30 day'
    group by 1
),
store_history as (
    select
        current_s.shipment_id,
        avg(
            case
                when hist.delivered_at is not null and hist.promised_delivery_at is not null and hist.delivered_at > hist.promised_delivery_at
                then 1.0 else 0.0
            end
        ) as store_delay_rate_30d
    from mart.shipments current_s
    join mart.orders current_o
        on current_s.order_id = current_o.order_id
    left join mart.shipments hist
        on hist.shipped_at < current_s.shipped_at
       and hist.shipped_at >= current_s.shipped_at - interval '30 day'
    left join mart.orders hist_o
        on hist.order_id = hist_o.order_id
       and hist_o.store_id = current_o.store_id
    group by 1
)
select
    sb.shipment_id,
    sb.order_id,
    sb.store_id,
    sb.ordered_at as feature_ts,
    sb.order_hour,
    sb.order_weekday,
    coalesce(sb.promised_lead_days, 0) as promised_lead_days,
    coalesce(ch.warehouse_backlog_7d, 0) as warehouse_backlog_7d,
    coalesce(ch.carrier_delay_rate_30d, 0) as carrier_delay_rate_30d,
    coalesce(sh.store_delay_rate_30d, 0) as store_delay_rate_30d,
    sb.label_is_delayed,
    now() as feature_generated_at
from shipment_base sb
left join carrier_history ch
    on sb.shipment_id = ch.shipment_id
left join store_history sh
    on sb.shipment_id = sh.shipment_id;
