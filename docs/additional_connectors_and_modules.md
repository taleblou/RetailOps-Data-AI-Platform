# Additional Connectors and Business Modules

This document captures the extra scope added on top of the original phases 1 to 20 roadmap.

## Added connectors

- `connector_woocommerce`
- `connector_adobe_commerce`
- `connector_bigcommerce`
- `connector_prestashop`

These connectors extend the original CSV, database, and Shopify ingestion paths with more standard retail-platform inputs.

## Added business modules

- `promotion_pricing_intelligence`
- `supplier_procurement_intelligence`
- `customer_intelligence`
- `payment_reconciliation`

These modules close gaps between the original retail AI surface and the operational finance and commercial workflows that usually follow once forecasting, stockout, and returns are in place.

## New API endpoints

- `GET /api/v1/promotion-pricing/summary`
- `GET /api/v1/promotion-pricing/skus/{sku}`
- `GET /api/v1/supplier-procurement/summary`
- `GET /api/v1/supplier-procurement/suppliers/{supplier_id}`
- `GET /api/v1/customer-intelligence/summary`
- `GET /api/v1/customer-intelligence/customers/{customer_id}`
- `GET /api/v1/payment-reconciliation/summary`
- `GET /api/v1/payment-reconciliation/orders/{order_id}`


## Phase 22 final recheck additions

- `assortment_intelligence`
- `basket_affinity_intelligence`
- `profitability_intelligence`

These modules were added in the final recheck to strengthen merchandising, cross-sell, and profit visibility on top of the earlier connector and business-module work.


## Phase 23 expansion additions

- `customer_cohort_intelligence`
- `inventory_aging_intelligence`
- `abc_xyz_intelligence`

New endpoints:

- `GET /api/v1/customer-cohorts/summary`
- `GET /api/v1/customer-cohorts/cohorts/{cohort_month}`
- `GET /api/v1/inventory-aging/summary`
- `GET /api/v1/inventory-aging/skus/{sku}`
- `GET /api/v1/abc-xyz/summary`
- `GET /api/v1/abc-xyz/skus/{sku}`

## Phase 24 expansion additions

- `customer_churn_intelligence`
- `sales_anomaly_intelligence`
- `seasonality_intelligence`
- `fulfillment_sla_intelligence`

New endpoints:

- `GET /api/v1/customer-churn/summary`
- `GET /api/v1/customer-churn/customers/{customer_id}`
- `GET /api/v1/sales-anomalies/summary`
- `GET /api/v1/sales-anomalies/days/{order_date}`
- `GET /api/v1/seasonality/summary`
- `GET /api/v1/seasonality/skus/{sku}`
- `GET /api/v1/fulfillment-sla/summary`
- `GET /api/v1/fulfillment-sla/orders/{order_id}`
