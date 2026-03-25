
  create view "retailops"."analytics_mart"."kpi_shipments__dbt_tmp"
    
    
  as (
    

select
    store_id,
    carrier,
    count(*) as shipment_count,
    sum(case when is_delayed then 1 else 0 end) as delayed_shipment_count,
    case
    when count(*) is null then null
    when count(*) = 0 then null
    else sum(case when is_delayed then 1 else 0 end)::numeric / count(*)::numeric
end as delayed_shipment_rate
from "retailops"."analytics_mart"."fct_shipments"
group by 1, 2
  );