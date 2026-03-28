INSERT INTO silver.orders
SELECT
  order_id,
  order_date,
  customer_id,
  sku,
  quantity,
  unit_price,
  store_code,
  event_timestamp
FROM bronze.orders
WHERE order_id IS NOT NULL;
