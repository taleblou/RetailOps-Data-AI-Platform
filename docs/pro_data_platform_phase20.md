# Phase 20 - Pro Data Platform

This document completes the roadmap through phase 20.
It turns the repository from a phase 19 packaged product into a structurally complete phase 20 Pro data platform.

## Scope completed in this repository

The repository now includes structural assets for all seven phase 20 modules:

1. `modules/cdc`
2. `modules/streaming`
3. `modules/lakehouse`
4. `modules/query_layer`
5. `modules/metadata`
6. `modules/feature_store`
7. `modules/advanced_serving`

Each module now has:

- a package directory with Python entry points
- a router, schema, and service layer for a phase 20 blueprint API
- module documentation
- starter config assets
- a Dockerfile for module-local execution where applicable
- compose overlays for the Pro runtime profile

## Important boundary

This repository now contains the platform-facing scaffolding and configuration surface for Redpanda, Debezium, Iceberg, Spark, Trino, OpenMetadata, Feast, Redis, and BentoML.
It does not claim that every external distributed service is fully production-tuned inside this offline editing session.
The goal here is to make the repository structurally complete, phase-aligned, and ready for technical teams to extend and operate.

## Module-by-module coverage

### CDC

Files:

- `modules/cdc/service.py`
- `modules/cdc/router.py`
- `modules/cdc/schemas.py`
- `modules/cdc/config/debezium-postgres.json`
- `modules/cdc/config/cdc_profile.yaml`
- `compose/compose.cdc.yaml`

Outputs:

- Debezium PostgreSQL connector blueprint
- raw CDC topic naming convention
- snapshot and connector management plan

### Streaming

Files:

- `modules/streaming/service.py`
- `modules/streaming/router.py`
- `modules/streaming/schemas.py`
- `modules/streaming/config/topics.yaml`
- `modules/streaming/config/processors.yaml`
- `compose/compose.streaming.yaml`

Outputs:

- Redpanda topic plan
- consumer-group plan
- stream-processor blueprint

### Lakehouse

Files:

- `modules/lakehouse/service.py`
- `modules/lakehouse/router.py`
- `modules/lakehouse/schemas.py`
- `modules/lakehouse/config/lakehouse_layout.yaml`
- `modules/lakehouse/jobs/bronze_to_silver.sql`
- `compose/compose.lakehouse.yaml`

Outputs:

- Iceberg catalog starter
- bronze, silver, and gold table layout
- object storage conventions
- Spark job starter assets

### Query layer

Files:

- `modules/query_layer/service.py`
- `modules/query_layer/router.py`
- `modules/query_layer/schemas.py`
- `modules/query_layer/config/catalogs/postgres.properties`
- `modules/query_layer/config/catalogs/iceberg.properties`
- `compose/compose.query.yaml`

Outputs:

- Trino catalog definitions
- federation query examples
- analytics query access plan

### Metadata

Files:

- `modules/metadata/service.py`
- `modules/metadata/router.py`
- `modules/metadata/schemas.py`
- `modules/metadata/config/openmetadata_ingestion.yaml`
- `compose/compose.metadata.yaml`

Outputs:

- OpenMetadata deployment starter
- ingestion workflows for PostgreSQL, dbt, and Trino
- lineage and catalog capture plan

### Feature store

Files:

- `modules/feature_store/service.py`
- `modules/feature_store/router.py`
- `modules/feature_store/schemas.py`
- `modules/feature_store/repo/feature_store.yaml`
- `modules/feature_store/repo/feature_views.py`
- `compose/compose.feature_store.yaml`

Outputs:

- Feast repository starter
- feature-view definitions
- offline and online store plan
- materialization schedule

### Advanced serving

Files:

- `modules/advanced_serving/service.py`
- `modules/advanced_serving/router.py`
- `modules/advanced_serving/schemas.py`
- `modules/advanced_serving/bentofile.yaml`
- `modules/advanced_serving/bentoml/service.py`
- `compose/compose.advanced_serving.yaml`

Outputs:

- BentoML service blueprint
- separate model runtime plan
- shadow deployment plan

## API surface added for phase 20

The main FastAPI app now includes read-only blueprint endpoints:

- `GET /api/v1/pro/cdc/blueprint`
- `GET /api/v1/pro/streaming/blueprint`
- `GET /api/v1/pro/lakehouse/blueprint`
- `GET /api/v1/pro/query-layer/blueprint`
- `GET /api/v1/pro/metadata/blueprint`
- `GET /api/v1/pro/feature-store/blueprint`
- `GET /api/v1/pro/advanced-serving/blueprint`
- `GET /api/v1/pro-platform/summary`

These endpoints give technical teams a generated phase 20 control surface and artifact set without creating a hard runtime dependency for the core platform.

## Packaging updates

The Pro packaging profile now includes:

- `compose/compose.streaming.yaml`
- `compose/compose.query.yaml`
- `compose/compose.feature_store.yaml`
- `compose/compose.advanced_serving.yaml`

It also updates:

- `scripts/common.sh`
- `scripts/health.sh`
- `config/samples/pro.env`
- `docs/quickstart/pro.md`
- `README.md`

## Validation

Phase 20 is covered by:

- `tests/pro_platform/test_phase20_pro_platform.py`
- `docs/phase_1_to_20_gap_report.md`
- `docs/phase_1_to_20_audit.md`
