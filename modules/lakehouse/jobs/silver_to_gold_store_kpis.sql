-- Materialize gold store KPI table from cleaned silver facts.
SELECT
    store_code,
    order_date,
    SUM(net_revenue) AS revenue,
    AVG(stock_coverage_days) AS stock_coverage_days,
    SUM(delayed_shipments) AS delayed_shipments
FROM silver.store_daily_facts
GROUP BY store_code, order_date;
