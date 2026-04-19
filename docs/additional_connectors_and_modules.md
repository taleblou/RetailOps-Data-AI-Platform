# Additional Connectors and Modules

This document summarizes capability areas that extend the baseline connector, analytics, and intelligence surface of the repository.

## Additional connectors

- `connector_woocommerce`
- `connector_adobe_commerce`
- `connector_bigcommerce`
- `connector_prestashop`

These modules expand ingestion beyond CSV, database, and Shopify sources while keeping the same source-management and raw-loading contracts.

## Additional commercial modules

- `promotion_pricing_intelligence`
- `supplier_procurement_intelligence`
- `customer_intelligence`
- `payment_reconciliation`
- `assortment_intelligence`
- `basket_affinity_intelligence`
- `profitability_intelligence`
- `customer_cohort_intelligence`
- `inventory_aging_intelligence`
- `abc_xyz_intelligence`
- `customer_churn_intelligence`
- `sales_anomaly_intelligence`
- `seasonality_intelligence`
- `fulfillment_sla_intelligence`

## Representative API endpoints

- `GET /api/v1/promotion-pricing/summary`
- `GET /api/v1/supplier-procurement/summary`
- `GET /api/v1/customer-intelligence/summary`
- `GET /api/v1/payment-reconciliation/summary`
- `GET /api/v1/customer-cohorts/summary`
- `GET /api/v1/inventory-aging/summary`
- `GET /api/v1/abc-xyz/summary`
- `GET /api/v1/customer-churn/summary`
- `GET /api/v1/sales-anomalies/summary`
- `GET /api/v1/seasonality/summary`
- `GET /api/v1/fulfillment-sla/summary`

The common theme is modular growth: new capabilities are added as focused modules that reuse the shared API, ingestion, artifact, and monitoring conventions of the repository.
