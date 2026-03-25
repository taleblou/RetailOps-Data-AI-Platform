
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select store_id
from "retailops"."analytics_mart"."mart_store_kpis"
where store_id is null



  
  
      
    ) dbt_internal_test