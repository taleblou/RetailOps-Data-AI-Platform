# Module Library

The `modules/` directory contains the bounded capabilities built on top of the shared `core/` platform.

## Connector modules

- `connector_csv/` CSV upload and file-based ingestion
- `connector_db/` relational-database discovery and extraction
- `connector_shopify/` Shopify source integration
- `connector_woocommerce/` WooCommerce source integration
- `connector_adobe_commerce/` Adobe Commerce source integration
- `connector_bigcommerce/` BigCommerce source integration
- `connector_prestashop/` PrestaShop source integration

These modules plug into the shared ingestion registry. The active installation only enables the connectors selected through `ENABLED_CONNECTORS` and the matching compose overlays.

## Operational intelligence modules

- `forecasting/` demand and sales forecasting surfaces
- `shipment_risk/` order and shipment risk scoring
- `stockout_intelligence/` stockout-risk detection and prioritization
- `reorder_engine/` reorder recommendation logic
- `returns_intelligence/` return-probability and reason analysis

## Commercial, planning, and customer intelligence modules

- `analytics_kpi/`
- `profitability_intelligence/`
- `payment_reconciliation/`
- `assortment_intelligence/`
- `basket_affinity_intelligence/`
- `customer_intelligence/`
- `customer_cohort_intelligence/`
- `customer_churn_intelligence/`
- `promotion_pricing_intelligence/`
- `inventory_aging_intelligence/`
- `sales_anomaly_intelligence/`
- `seasonality_intelligence/`
- `supplier_procurement_intelligence/`
- `fulfillment_sla_intelligence/`
- `abc_xyz_intelligence/`

These modules turn curated retail data into decision support, KPI packs, and explanation-oriented outputs.

## Reporting and dashboard modules

- `dashboard_hub/` aggregated dashboard workspace generation
- `dashboards/` dashboard assets and API-facing dashboard utilities
- `business_review_reporting/` executive, governance, portfolio, and decision-intelligence reporting

## Platform extension modules

- `cdc/`
- `streaming/`
- `lakehouse/`
- `metadata/`
- `feature_store/`
- `query_layer/`
- `advanced_serving/`
- `ml_registry/`

These modules extend the base platform with optional data-platform, registry, and deployment surfaces.

## Shared helpers

- `common/` reusable module utilities

## Common layout

Most modules use a familiar structure:

- `service.py` for business logic or artifact generation
- `router.py` for HTTP endpoints when a module has an API surface
- `schemas.py` for request and response contracts
- `main.py` for lightweight service entry points when a module ships a dedicated container
- `Dockerfile` when the module is deployed as a separate service
- `README.md` for module-local operating guidance

## Maintenance rules

- Keep module README files aligned with routes, settings, and artifact paths.
- Keep optional platform modules isolated so they can be enabled without forcing unrelated dependencies.
- Update the matching tests and long-form docs when a module contract changes.
