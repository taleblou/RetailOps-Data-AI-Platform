# Reorder Engine Module

Supports the reorder engine layer inside the modular repository architecture. Exposes HTTP endpoints for reorder engine capabilities.
It follows the repository module pattern of service logic, API surface, schemas, optional runtime entry points, and deployment assets when those concerns are applicable.

## Directory contents

- `main.py` — Provides implementation support for the reorder engine workflow.
- `router.py` — Defines API routes for the reorder engine module.
- `service.py` — Implements the reorder engine service layer and business logic.
- `schemas.py` — Defines schemas for the reorder engine data contracts.
- `__init__.py` — Defines the modules.reorder_engine package surface and package-level exports.
- `Dockerfile` — Container build definition for this component.

## Interfaces and data contracts

- Main types: ReorderRecommendationResponse, ReorderSummaryResponse, ReorderRecommendationListResponse, ReorderArtifactNotFoundError, ReorderRecommendationArtifact, ReorderSummaryArtifact, ReorderArtifact, _SupplyOverride.
- Key APIs and entry points: main, router, list_reorder_recommendations, get_reorder_sku, run_reorder_engine, load_reorder_artifact, get_or_create_reorder_artifact, get_reorder_recommendations, get_reorder_recommendation.

## Operational notes

- Scope profile: internal (4), public API (1).
- Status profile: stable (4), internal (1).
- Important dependencies: __future__, router, time, pathlib, fastapi, schemas, service, pydantic, csv, json, math, uuid, dataclasses.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. Internal interfaces should remain aligned with adjacent modules and repository conventions. Public request and response behavior should remain backward compatible with documented API flows.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies. Python 3.11+ with FastAPI-compatible runtime dependencies.
- Maintenance guidance: keep routers, schemas, services, artifacts, and README examples synchronized when this module evolves.

## Related areas

- `tests/reorder_engine/` automated checks for this module when present
- `modules/common/` shared parsing and upload utilities
- `docs/` long-form capability and architecture references
