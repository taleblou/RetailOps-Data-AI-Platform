# Module Library

The `modules/` directory contains the bounded capabilities that sit on top of the shared `core/` platform.

## Module families

### Connector modules

- `connector_csv/`
- `connector_db/`
- `connector_shopify/`
- `connector_adobe_commerce/`
- `connector_bigcommerce/`
- `connector_prestashop/`
- `connector_woocommerce/`

These adapters plug into the shared ingestion base layer and expose source-specific extraction or discovery behavior.

### Operational intelligence modules

- `forecasting/`
- `shipment_risk/`
- `stockout_intelligence/`
- `reorder_engine/`
- `returns_intelligence/`

These modules turn curated retail data into operational recommendations, scores, forecasts, and explanations.

### Commercial and planning modules

This family includes assortment, profitability, payment reconciliation, seasonality, cohorts, churn, supplier procurement, customer intelligence, sales anomaly detection, inventory aging, and related intelligence packs.

### Reporting and dashboard modules

- `analytics_kpi/`
- `dashboard_hub/`
- `dashboards/`
- `business_review_reporting/`

These modules build dashboard artifacts, KPI APIs, business review packs, and executive-facing outputs.

### Platform extension modules

- `cdc/`
- `streaming/`
- `lakehouse/`
- `metadata/`
- `feature_store/`
- `query_layer/`
- `advanced_serving/`

These modules extend the base platform with optional data-platform or serving capabilities.

## Common structure

Most modules follow a familiar layout:

- `service.py` for business logic and artifact generation.
- `router.py` for API endpoints when the module has an HTTP surface.
- `schemas.py` for request or response contracts.
- `main.py` for lightweight entry-point wiring when needed.
- `Dockerfile` and related runtime assets for deployable components.

## Maintenance notes

- Keep module README files aligned with the file headers in the same directory.
- Keep shared parsing or upload behavior in `modules/common/` when reused across modules.
- Update the related tests and long-form docs whenever a module contract changes.
