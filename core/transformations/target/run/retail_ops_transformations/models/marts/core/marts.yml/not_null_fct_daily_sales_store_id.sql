
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select store_id
from "retailops"."analytics_mart"."fct_daily_sales"
where store_id is null



  
  
      
    ) dbt_internal_test