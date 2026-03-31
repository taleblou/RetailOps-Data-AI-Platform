# Seasonality Intelligence Module

Supports the seasonality intelligence layer inside the modular repository architecture. Exposes HTTP endpoints for seasonality intelligence capabilities.
It follows the repository module pattern of service logic, API surface, schemas, optional runtime entry points, and deployment assets when those concerns are applicable.

## Directory contents

- `main.py` — Provides implementation support for the seasonality intelligence workflow.
- `router.py` — Defines API routes for the seasonality intelligence module.
- `service.py` — Implements the seasonality intelligence service layer and business logic.
- `schemas.py` — Defines schemas for the seasonality intelligence data contracts.
- `__init__.py` — Defines the modules.seasonality_intelligence package surface and package-level exports.
- `Dockerfile` — Container build definition for this component.

## Interfaces and data contracts

- Main types: SeasonalitySummaryResponse, SeasonalitySkuResponse, SeasonalityArtifactResponse.
- Key APIs and entry points: main, router, get_seasonality_summary, get_seasonality_detail, build_seasonality_artifact, get_seasonality_artifact, get_seasonality_sku.

## Operational notes

- Scope profile: internal (4), public API (1).
- Status profile: stable (4), internal (1).
- Important dependencies: __future__, time, pathlib, fastapi, schemas, service, pydantic, collections, typing, modules.common.upload_utils.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. Internal interfaces should remain aligned with adjacent modules and repository conventions. Public request and response behavior should remain backward compatible with documented API flows.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies. Python 3.11+ with FastAPI-compatible runtime dependencies.
- Maintenance guidance: keep routers, schemas, services, artifacts, and README examples synchronized when this module evolves.

## Related areas

- `tests/seasonality_intelligence/` automated checks for this module when present
- `modules/common/` shared parsing and upload utilities
- `docs/` long-form capability and architecture references
