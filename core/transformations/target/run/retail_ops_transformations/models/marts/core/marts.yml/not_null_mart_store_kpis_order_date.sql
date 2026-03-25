
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select order_date
from "retailops"."analytics_mart"."mart_store_kpis"
where order_date is null



  
  
      
    ) dbt_internal_test