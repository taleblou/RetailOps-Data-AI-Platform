
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select snapshot_date
from "retailops"."analytics_mart"."fct_inventory_daily"
where snapshot_date is null



  
  
      
    ) dbt_internal_test