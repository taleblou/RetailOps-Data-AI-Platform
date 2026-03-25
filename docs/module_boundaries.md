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
- phase 6 placeholder for first transform run
- future dbt or SQL model execution hooks

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
Purpose: forecast runners and model-serving starter code.
Consumes curated features or marts. Must not own raw ingestion.

### `modules/shipment_risk`, `modules/stockout_intelligence`, `modules/reorder_engine`, `modules/returns_intelligence`
Purpose: optional business modules.
These extend analytics and ML capabilities. They must remain swappable.

### `modules/cdc`, `modules/streaming`, `modules/lakehouse`, `modules/metadata`, `modules/feature_store`, `modules/advanced_serving`, `modules/ml_registry`, `modules/dashboards`
Purpose: advanced platform add-ons.
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
