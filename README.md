# RetailOps Data & AI Platform

A modular self-hosted retail data and AI platform for ingestion, analytics, forecasting, monitoring, and operational decision support.

## Phase coverage in this repository

This repository is tightened around phases 1 to 6 of the project plan:

- phase 1: product, personas, tiering, architecture, and module-boundary docs
- phase 2: monorepo layout, uv workflow, lint/test setup, env template, and clean ignore rules
- phase 3: core and optional Docker Compose stacks with starter services, networks, volumes, env files, and health checks
- phase 4: canonical data model migrations and raw/staging/mart-oriented database layout
- phase 5: connector framework, source API, CSV/database connectors, mapper, validator, and state handling
- phase 6: Easy CSV wizard and API flow for upload, preview, mapping, validation, raw import, first transform, starter dashboard, and starter forecast

## Quick start with uv

```bash
uv sync
cp .env.example .env
uv run uvicorn core.api.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- Swagger: `http://localhost:8000/docs`
- Easy CSV wizard: `http://localhost:8000/easy-csv/wizard`

## Quick start with Docker Compose

```bash
docker compose -f compose/compose.core.yaml up -d postgres metabase
uv run uvicorn core.api.main:app --reload --host 0.0.0.0 --port 8000
```

Optional stacks:

```bash
docker compose -f compose/compose.core.yaml -f compose/compose.analytics.yaml up -d analytics
docker compose -f compose/compose.core.yaml -f compose/compose.ml.yaml up -d forecasting
docker compose -f compose/compose.core.yaml -f compose/compose.monitoring.yaml up -d monitoring
docker compose -f compose/compose.core.yaml -f compose/compose.cdc.yaml up -d cdc
docker compose -f compose/compose.core.yaml -f compose/compose.lakehouse.yaml up -d lakehouse
docker compose -f compose/compose.core.yaml -f compose/compose.metadata.yaml up -d metadata
```

## Run tests

```bash
uv run pytest
```

## Notes for scope

- The Shopify connector remains a starter implementation because it needs live tenant credentials and tenant-specific testing.
- The first transform, dashboard, and forecast in phase 6 are starter implementations designed to prove the full user path before the later specialized phases deepen them.
- Extra local-only artifacts and package subprojects were removed so the repository stays focused on phases 1 to 6.
