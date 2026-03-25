# RetailOps Phase 7 - Modular dbt Core Starter

This package contains a ready-to-copy Phase 7 starter for the RetailOps Data & AI Platform.

## Included structure

- `core/transformations`: dbt Core project
- `modules/analytics_kpi/dbt_models`: starter dbt models for KPI analytics
- `modules/forecasting/dbt_models`: starter dbt models for forecasting features
- `modules/shipment_risk/dbt_models`: starter dbt models for shipment-risk features

## Expected schemas

The models assume these PostgreSQL schemas already exist:

- `raw`
- `staging`
- `mart`

## Expected raw tables

- `raw.orders`
- `raw.products`
- `raw.shipments`
- `raw.inventory_snapshots`

## Quick start

```bash
cd core/transformations
export DBT_PROFILES_DIR=profiles
export DBT_PGHOST=localhost
export DBT_PGPORT=5433
export DBT_PGUSER=postgres
export DBT_PGPASSWORD=postgres
export DBT_PGDATABASE=retailops
uv run dbt debug --project-dir . --profiles-dir profiles
uv run dbt source freshness --project-dir . --profiles-dir profiles
uv run dbt build --project-dir . --profiles-dir profiles
uv run dbt docs generate --project-dir . --profiles-dir profiles
uv run dbt docs serve --project-dir . --profiles-dir profiles
```

## Notes

- `profiles/profiles.yml` is environment-variable driven.
- Source freshness expects an `ingested_at` timestamp in each raw table.
- Module-level models are kept separate from the core dbt project to preserve modular boundaries.
