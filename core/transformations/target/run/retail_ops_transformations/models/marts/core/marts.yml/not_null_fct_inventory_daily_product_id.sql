
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select product_id
from "retailops"."analytics_mart"."fct_inventory_daily"
where product_id is null



  
  
      
    ) dbt_internal_test