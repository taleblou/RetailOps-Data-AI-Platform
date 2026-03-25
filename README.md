# RetailOps Data & AI Platform

A modular, self-hosted retail data and AI platform for stores that want one package for ingestion, canonical modeling, KPI dashboards, forecasting, and optional advanced modules such as CDC, lakehouse, metadata, and feature services.

## What this package covers

This repository now contains the deliverables for phases 1 to 7 of the platform roadmap:

1. **Product definition and module boundaries** in `docs/`
2. **Modular monorepo skeleton** with Python tooling, quality gates, and environment samples
3. **Composable Docker deployment** for core and optional add-on services
4. **Canonical retail data model** with SQL migrations and documentation
5. **Connector framework** for CSV, database, and Shopify-style sources
6. **Easy CSV path** with upload, preview, mapping, validation, raw import, starter transform, dashboard, and forecast
7. **Modular dbt Core project** for staging and mart transformations

## Repository structure

- `core/` - platform capabilities shared by all modules
- `modules/` - optional business and connector modules
- `compose/` - Docker Compose stacks for core and add-ons
- `docs/` - product, architecture, and data-model documentation
- `tests/` - API, ingestion, and workflow tests

## Phase mapping

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
- `compose/compose.lakehouse.yaml`
- `compose/compose.metadata.yaml`

### Phase 4

- `core/db/migrations/001_schemas.sql`
- `core/db/migrations/002_core_tables.sql`
- `docs/canonical_data_model.md`

### Phase 5

- `core/ingestion/base/`
- `modules/connector_csv/`
- `modules/connector_db/`
- `modules/connector_shopify/`
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
make test
```

## Start Docker stacks

### Core only

```bash
docker compose -f compose/compose.core.yaml up -d
```

### Core plus starter analytics and connectors

```bash
docker compose \
  -f compose/compose.core.yaml \
  -f compose/compose.connectors.yaml \
  -f compose/compose.analytics.yaml up -d
```

### Full phase-1-to-7 stack

```bash
docker compose \
  -f compose/compose.core.yaml \
  -f compose/compose.connectors.yaml \
  -f compose/compose.analytics.yaml \
  -f compose/compose.ml.yaml \
  -f compose/compose.monitoring.yaml \
  -f compose/compose.cdc.yaml \
  -f compose/compose.lakehouse.yaml \
  -f compose/compose.metadata.yaml up -d
```

## Easy CSV workflow

Start the API and open the wizard:

```bash
uv run uvicorn core.api.main:app --reload
```

Then visit:

- `/easy-csv/wizard` for the guided HTML flow
- `/docs` for the JSON API flow

The phase 6 workflow supports:

- CSV upload
- preview
- mapping
- validation report
- raw import
- starter transform
- starter dashboard
- starter forecast

## dbt workflow

```bash
cd core/transformations
export DBT_PROFILES_DIR=profiles
export DBT_PGHOST=localhost
export DBT_PGPORT=5433
export DBT_PGUSER=postgres
export DBT_PGPASSWORD=postgres
export DBT_PGDATABASE=retailops
uv run dbt debug --project-dir . --profiles-dir profiles
uv run dbt build --project-dir . --profiles-dir profiles
```
