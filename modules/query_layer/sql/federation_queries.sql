-- RetailOps query-layer starter queries
SELECT
    o.order_id,
    o.store_code,
    f.stockout_probability,
    f.reorder_urgency_score
FROM postgres.mart.orders AS o
JOIN iceberg.gold.stockout_features AS f
    ON o.sku = f.sku;

SELECT
    store_code,
    SUM(revenue) AS revenue,
    AVG(stock_coverage_days) AS avg_stock_coverage_days
FROM iceberg.gold.store_kpis
GROUP BY store_code;
