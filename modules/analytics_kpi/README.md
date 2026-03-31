# Analytics KPI Module

Supports the analytics kpi layer inside the modular repository architecture. Exposes HTTP endpoints for analytics kpi capabilities.
It follows the repository module pattern of service logic, API surface, schemas, optional runtime entry points, and deployment assets when those concerns are applicable.

## Directory contents

- `main.py` — Provides implementation support for the analytics kpi workflow.
- `router.py` — Defines API routes for the analytics kpi module.
- `service.py` — Implements the analytics kpi service layer and business logic.
- `schemas.py` — Defines schemas for the analytics kpi data contracts.
- `export.py` — Provides implementation support for the analytics kpi workflow.
- `queries.py` — Provides implementation support for the analytics kpi workflow.
- `__init__.py` — Defines the modules.analytics_kpi package surface and package-level exports.
- `Dockerfile` — Container build definition for this component.
- `dbt_models/` — dbt models and marts that prepare canonical inputs for this module.

## Interfaces and data contracts

- Main types: DashboardCardResponse, DashboardArtifactResponse, DailySalesPoint, RevenueByCategoryPoint, InventoryHealthItem, ShipmentItem, DashboardCardArtifact, DashboardArtifact, SalesDailyItem, CategoryRevenueItem, ShipmentSummary.
- Key APIs and entry points: rows_to_csv_text, csv_response, json_download_response, main, get_first_scalar, get_first_sequence, router, get_overview_by_upload, get_sales_daily_by_upload, get_revenue_by_category_by_upload, get_inventory_health_by_upload, get_shipments_by_upload.

## Operational notes

- Scope profile: internal (6), public API (1).
- Status profile: stable (6), internal (1).
- Important dependencies: __future__, router, service, csv, io, json, collections.abc, typing, time, pathlib, fastapi, export, schemas, pydantic.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. File-system paths and serialized artifact formats must remain stable for downstream consumers. Internal interfaces should remain aligned with adjacent modules and repository conventions.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies. Python 3.11+ with FastAPI-compatible runtime dependencies.
- Maintenance guidance: keep routers, schemas, services, artifacts, and README examples synchronized when this module evolves.

## Related areas

- `tests/analytics_kpi/` automated checks for this module when present
- `modules/common/` shared parsing and upload utilities
- `docs/` long-form capability and architecture references
