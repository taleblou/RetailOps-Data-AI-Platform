
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select snapshot_date
from "retailops"."analytics_staging"."stg_inventory"
where snapshot_date is null



  
  
      
    ) dbt_internal_test