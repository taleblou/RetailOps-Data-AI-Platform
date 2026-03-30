# ML Registry Module

Supports the ml registry layer inside the modular repository architecture. Exposes HTTP endpoints for ml registry capabilities.
It follows the repository module pattern of service logic, API surface, schemas, optional runtime entry points, and deployment assets when those concerns are applicable.

## Directory contents

- `main.py` — Provides implementation support for the ml registry workflow.
- `router.py` — Defines API routes for the ml registry module.
- `service.py` — Implements the ml registry service layer and business logic.
- `schemas.py` — Defines schemas for the ml registry data contracts.
- `__init__.py` — Defines the modules.ml_registry package surface and package-level exports.
- `Dockerfile` — Container build definition for this component.

## Interfaces and data contracts

- Main types: ThresholdGateResponse, ModelVersionResponse, ModelRegistryDetailsResponse, ModelRegistrySummaryItemResponse, ModelRegistrySummaryResponse, ModelRegistryPromotionRequest, ModelRegistryNotFoundError, ModelRegistryVersionArtifact, ModelRegistryDetailsArtifact, ModelRegistrySummaryItemArtifact, ModelRegistryArtifact.
- Key APIs and entry points: main, router, get_model_registry_summary_endpoint, get_model_registry_details_endpoint, promote_model_registry_candidate, rollback_model_registry_candidate, run_model_registry, get_model_registry_summary, get_model_registry_details, promote_registry_model, rollback_registry_model.

## Operational notes

- Scope profile: internal (4), public API (1).
- Status profile: stable (4), internal (1).
- Important dependencies: __future__, router, service, time, pathlib, fastapi, schemas, pydantic, json, uuid, dataclasses, datetime.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. Internal interfaces should remain aligned with adjacent modules and repository conventions. Public request and response behavior should remain backward compatible with documented API flows.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies. Python 3.11+ with FastAPI-compatible runtime dependencies.
- Maintenance guidance: keep routers, schemas, services, artifacts, and README examples synchronized when this module evolves.

## Related areas

- `tests/ml_registry/` automated checks for this module when present
- `modules/common/` shared parsing and upload utilities
- `docs/` long-form capability and architecture references
