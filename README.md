# RetailOps Data & AI Platform

A modular, self-hosted retail data and AI platform for stores that want one package for ingestion, canonical modeling, KPI dashboards, forecasting, operational recommendations, and optional advanced modules such as CDC, lakehouse, metadata, feature services, and advanced serving.

This repository is aligned to **phases 1 to 20** of the roadmap described in the project PDF and also includes phase 21 to 24 business extensions added during the completion passes.
It includes the core platform, business modules, setup wizard, packaging layer, and a phase 20 Pro data-platform surface.

## Coverage summary

1. **Phase 1** - product definition, personas, tiering, and module boundaries
2. **Phase 2** - modular monorepo skeleton and quality tooling
3. **Phase 3** - Docker Compose architecture for core and add-on services
4. **Phase 4** - canonical retail data model and SQL migrations
5. **Phase 5** - connector framework for CSV, database, Shopify, WooCommerce, Adobe Commerce, BigCommerce, and PrestaShop sources
6. **Phase 6** - easy CSV onboarding path with upload, preview, mapping, validation, import, transform, dashboard publish, and first forecast
7. **Phase 7** - dbt Core transformations for staging and marts
8. **Phase 8** - KPI analytics module and dashboard starter assets
9. **Phase 9** - feature contracts, dataset builders, and feature tables
10. **Phase 10** - forecasting module with interval outputs and backtest helpers
11. **Phase 11** - shipment-risk module with explanations and manual review
12. **Phase 12** - stockout intelligence
13. **Phase 13** - reorder engine
14. **Phase 14** - returns intelligence
15. **Phase 15** - ML registry lifecycle and promotion gates
16. **Phase 16** - serving layer with standard response envelopes and explain endpoints
17. **Phase 17** - monitoring, drift checks, alerts, and override logging
18. **Phase 18** - onboarding and setup wizard
19. **Phase 19** - packaging, release, quickstarts, and operational scripts
20. **Phase 20** - CDC, streaming, lakehouse, query-layer, metadata, feature-store, and advanced-serving blueprints

## Repository structure

- `core/` - shared platform capabilities used by all modules
- `modules/` - connector, analytics, AI, registry, operations, and Pro platform modules
- `compose/` - composable Docker stacks for core and optional overlays
- `config/` - runtime settings and sample profile env files
- `data/` - demo CSVs, uploads, and generated artifacts
- `docs/` - product, architecture, audits, gap reports, quickstarts, and phase docs
- `scripts/` - install, upgrade, backup, restore, demo-data, and health commands
- `tests/` - phase-aligned tests for ingestion, analytics, AI, serving, monitoring, setup, packaging, and phase 20 Pro modules
- `packages/` - starter package wrappers for future package split work

## Phase-to-file highlights

### Phase 1

- `docs/product_definition.md`
- `docs/personas.md`
- `docs/tiering.md`
- `docs/module_boundaries.md`
- `docs/architecture_overview.md`
- `docs/architecture/phase-1-solution-architecture.drawio`

### Phase 2

- `pyproject.toml`
- `README.md`
- `.env.example`
- `.gitignore`
- `.pre-commit-config.yaml`
- `Makefile`

### Phase 3

- `compose/compose.core.yaml`
- `compose/compose.connectors.yaml`
- `compose/compose.analytics.yaml`
- `compose/compose.ml.yaml`
- `compose/compose.monitoring.yaml`
- `compose/compose.cdc.yaml`
- `compose/compose.streaming.yaml`
- `compose/compose.lakehouse.yaml`
- `compose/compose.query.yaml`
- `compose/compose.metadata.yaml`
- `compose/compose.feature_store.yaml`
- `compose/compose.advanced_serving.yaml`

### Phase 4

- `core/db/migrations/001_schemas.sql`
- `core/db/migrations/002_core_tables.sql`
- `core/db/migrations/003_connector_framework.sql`
- `docs/canonical_data_model.md`

### Phase 5

- `core/ingestion/base/`
- `modules/connector_csv/`
- `modules/connector_db/`
- `modules/connector_shopify/`
- `modules/connector_woocommerce/`
- `modules/connector_adobe_commerce/`
- `modules/connector_bigcommerce/`
- `modules/connector_prestashop/`
- `core/api/routes/sources.py`

### Phase 6

- `core/api/routes/easy_csv.py`
- `core/api/schemas/easy_csv.py`
- `core/transformations/service.py`
- `modules/analytics_kpi/service.py`
- `modules/forecasting/service.py`

### Phase 7

- `core/transformations/dbt_project.yml`
- `core/transformations/models/`
- `modules/analytics_kpi/dbt_models/`
- `modules/forecasting/dbt_models/`
- `modules/shipment_risk/dbt_models/`

### Phases 8 to 18

See the phase documentation and audits under `docs/`.

### Additional business modules

- `modules/promotion_pricing_intelligence/`
- `modules/supplier_procurement_intelligence/`
- `modules/customer_intelligence/`
- `modules/payment_reconciliation/`
- `modules/assortment_intelligence/`
- `modules/basket_affinity_intelligence/`
- `modules/profitability_intelligence/`
- `modules/customer_cohort_intelligence/`
- `modules/inventory_aging_intelligence/`
- `modules/abc_xyz_intelligence/`
- `modules/customer_churn_intelligence/`
- `modules/sales_anomaly_intelligence/`
- `modules/seasonality_intelligence/`
- `modules/fulfillment_sla_intelligence/`
- `docs/additional_connectors_and_modules.md`
- `docs/further_business_modules.md`
- `docs/final_business_expansion_phase23.md`
- `docs/final_business_expansion_phase24.md`

### Phase 19

- `scripts/install.sh`
- `scripts/upgrade.sh`
- `scripts/backup.sh`
- `scripts/restore.sh`
- `scripts/load_demo_data.sh`
- `scripts/health.sh`
- `docs/quickstart/lite.md`
- `docs/quickstart/standard.md`
- `docs/quickstart/pro.md`
- `config/samples/lite.env`
- `config/samples/standard.env`
- `config/samples/pro.env`
- `docs/release_notes_phase19.md`

### Phase 20

- `docs/pro_data_platform_phase20.md`
- `docs/phase_1_to_20_gap_report.md`
- `docs/phase_1_to_20_audit.md`
- `core/api/routes/pro_platform.py`
- `core/api/schemas/pro_platform.py`
- `modules/cdc/`
- `modules/streaming/`
- `modules/lakehouse/`
- `modules/query_layer/`
- `modules/metadata/`
- `modules/feature_store/`
- `modules/advanced_serving/`

## Local setup

```bash
uv sync
cp .env.example .env
```

## Quality checks

```bash
make check
```

## Run tests

```bash
pytest -q
```

## Start Docker stacks manually

### Core only

```bash
docker compose -f compose/compose.core.yaml up -d
```

### Lite profile

```bash
docker compose   -f compose/compose.core.yaml   -f compose/compose.connectors.yaml   -f compose/compose.analytics.yaml up -d
```

### Standard profile

```bash
docker compose   -f compose/compose.core.yaml   -f compose/compose.connectors.yaml   -f compose/compose.analytics.yaml   -f compose/compose.ml.yaml   -f compose/compose.monitoring.yaml up -d
```

### Pro profile

```bash
docker compose   -f compose/compose.core.yaml   -f compose/compose.connectors.yaml   -f compose/compose.analytics.yaml   -f compose/compose.ml.yaml   -f compose/compose.monitoring.yaml   -f compose/compose.cdc.yaml   -f compose/compose.streaming.yaml   -f compose/compose.lakehouse.yaml   -f compose/compose.query.yaml   -f compose/compose.metadata.yaml   -f compose/compose.feature_store.yaml   -f compose/compose.advanced_serving.yaml up -d
```

## Useful phase 20 APIs

- `GET /api/v1/pro/cdc/blueprint`
- `GET /api/v1/pro/streaming/blueprint`
- `GET /api/v1/pro/lakehouse/blueprint`
- `GET /api/v1/pro/query-layer/blueprint`
- `GET /api/v1/pro/metadata/blueprint`
- `GET /api/v1/pro/feature-store/blueprint`
- `GET /api/v1/pro/advanced-serving/blueprint`
- `GET /api/v1/pro-platform/summary`

## Useful docs

- `docs/quickstart/lite.md`
- `docs/quickstart/standard.md`
- `docs/quickstart/pro.md`
- `docs/pro_data_platform_phase20.md`
- `docs/phase_1_to_20_gap_report.md`
- `docs/phase_1_to_20_audit.md`
