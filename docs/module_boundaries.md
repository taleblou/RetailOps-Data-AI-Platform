# Module Boundaries

This document defines the execution boundaries for the RetailOps platform. The platform is modular. Core services must run without optional modules. Optional modules may depend on core contracts, but core must not depend on optional modules.

## Core Layer

### `core/api`
Purpose: HTTP entry point for source registration, ingestion workflows, and the simple CSV onboarding path.

Inputs:
- API requests
- validated configuration
- repository and registry dependencies

Outputs:
- JSON API responses
- orchestration calls into ingestion, state, and raw loading services

Depends on:
- `config`
- `core/ingestion/base`
- optional module contracts only through the repository or service interfaces

Must not depend on:
- dashboard code
- forecasting code
- CDC or lakehouse internals

### `core/ingestion/base`
Purpose: reusable connector framework.

Responsibilities:
- connector contracts
- column mapping
- validation
- source state tracking
- raw loading
- repository protocol and implementations

This layer is the platform backbone for phases 4 to 6.

### `core/db`
Purpose: SQL migrations and database bootstrap assets.

Responsibilities:
- schema creation
- core platform tables
- connector framework tables

### `core/worker`
Purpose: background execution entry point.

Current scope:
- worker heartbeat and future async jobs

### `core/transformations`
Purpose: starter location for transform orchestration.

Current scope:
- first transform orchestration for the easy CSV path
- dbt or SQL model execution hooks for staged and mart data

### `core/monitoring`
Purpose: monitoring service starter.

Current scope:
- platform health heartbeat
- future alerting and observability hooks

## Optional Module Layer

### `modules/connector_csv`
Provides CSV file ingestion.
Required for Lite tier.

### `modules/connector_db`
Provides database source ingestion.
Required for Standard tier and above.

### `modules/connector_shopify`
Provides Shopify connector contract and starter implementation.
Optional until external credentials are available.

### `modules/analytics_kpi`
Purpose: KPI service and dashboard bootstrap assets.
Consumes curated data. Must not own ingestion logic.

### `modules/forecasting`
Purpose: forecast runners, batch scoring jobs, and forecast-serving APIs.
Consumes curated features or marts. Must not own raw ingestion.

### `modules/shipment_risk`
Purpose: shipment-delay scoring, explanation, and manual-review triggers for open orders.
Consumes shipment feature views or uploaded shipment files. Must not own ingestion.

### `modules/stockout_intelligence`
Purpose: days-to-stockout, stockout risk scoring, and reorder urgency outputs.
Consumes demand history plus inventory signals. Must not own raw ingestion.

### `modules/reorder_engine`
Purpose: convert forecast and stockout outputs into reorder date, reorder quantity, urgency, and rationale.
Consumes forecast artifacts, stockout artifacts, and supply-side rules. Must not own raw ingestion.

### `modules/returns_intelligence`
Purpose: return-risk scoring with expected return cost and risky-product rollups.
Consumes order-history signals such as category, discount, shipment delay, and prior return behaviour.
Must stay optional and must not own raw ingestion.

### `modules/cdc`
Purpose: PostgreSQL CDC blueprint and Debezium connector planning.

### `modules/streaming`
Purpose: Redpanda topic planning, consumer groups, and stream processors.

### `modules/lakehouse`
Purpose: Iceberg-based bronze, silver, and gold lakehouse layout.

### `modules/query_layer`
Purpose: Trino federation catalogs and analytics query access.

### `modules/metadata`
Purpose: OpenMetadata ingestion, lineage, and catalog starter flows.

### `modules/feature_store`
Purpose: Feast repo, feature views, and online materialization planning.

### `modules/advanced_serving`
Purpose: BentoML service blueprints, separate runtime planning, and shadow deployment.

### `modules/ml_registry`, `modules/dashboards`
Purpose: supporting advanced platform add-ons.
They are outside the minimum Lite workflow and must stay optional.

## Dependency Rules

1. Core may be used alone.
2. Optional modules may import core contracts.
3. Optional modules must not require each other unless the dependency is declared.
4. Ingestion writes to raw first. It must not write directly to marts.
5. Analytics and forecasting consume transformed data, not raw connector internals.
6. Monitoring may observe all layers, but it must not become a hard runtime dependency for core execution.

## Tier Mapping

### Lite
- core/api
- core/ingestion/base
- core/db
- core/worker
- modules/connector_csv
- modules/analytics_kpi
- modules/forecasting
- core/monitoring

### Standard
- all Lite modules
- modules/connector_db
- shipment and stock modules
- ML registry starter

### Pro
- all Standard modules
- CDC
- streaming
- lakehouse
- metadata
- feature store
- advanced serving

## Disabled Module Principle

When an optional module is disabled:
- the core API must still start
- the database and CSV flow must still work
- compose files must allow selective startup
- docs must describe which workflows need the module and which do not
