# Returns Intelligence Module

Supports the returns intelligence layer inside the modular repository architecture. Exposes HTTP endpoints for returns intelligence capabilities.
It follows the repository module pattern of service logic, API surface, schemas, optional runtime entry points, and deployment assets when those concerns are applicable.

## Directory contents

- `main.py` — Provides implementation support for the returns intelligence workflow.
- `router.py` — Defines API routes for the returns intelligence module.
- `service.py` — Implements the returns intelligence service layer and business logic.
- `schemas.py` — Defines schemas for the returns intelligence data contracts.
- `__init__.py` — Defines the modules.returns_intelligence package surface and package-level exports.
- `Dockerfile` — Container build definition for this component.
- `features/` — Reusable SQL or contract assets that feed scoring, training, or reporting workflows.

## Interfaces and data contracts

- Main types: ReturnRiskPredictionResponse, ReturnRiskProductResponse, ReturnRiskSummaryResponse, ReturnRiskArtifactResponse, ReturnRiskArtifactNotFoundError, ReturnRiskPredictionArtifact, ReturnRiskProductArtifact, ReturnRiskSummaryArtifact, ReturnRiskArtifact, _ResolvedUpload.
- Key APIs and entry points: main, router, list_return_risk_orders, get_return_risk_order_detail, list_return_risk_products, run_returns_intelligence, load_returns_artifact, get_or_create_returns_artifact, get_return_risk_scores, get_return_risk_order, get_return_risk_products.

## Operational notes

- Scope profile: internal (4), public API (1).
- Status profile: stable (4), internal (1).
- Important dependencies: __future__, time, pathlib, fastapi, schemas, service, pydantic, csv, json, uuid, collections, dataclasses.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. Internal interfaces should remain aligned with adjacent modules and repository conventions. Public request and response behavior should remain backward compatible with documented API flows.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies. Python 3.11+ with FastAPI-compatible runtime dependencies.
- Maintenance guidance: keep routers, schemas, services, artifacts, and README examples synchronized when this module evolves.

## Related areas

- `tests/returns_intelligence/` automated checks for this module when present
- `modules/common/` shared parsing and upload utilities
- `docs/` long-form capability and architecture references
