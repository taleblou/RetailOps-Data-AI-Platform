# Stockout Intelligence Module

Supports the stockout intelligence layer inside the modular repository architecture. Exposes HTTP endpoints for stockout intelligence capabilities.
It follows the repository module pattern of service logic, API surface, schemas, optional runtime entry points, and deployment assets when those concerns are applicable.

## Directory contents

- `main.py` — Provides implementation support for the stockout intelligence workflow.
- `router.py` — Defines API routes for the stockout intelligence module.
- `service.py` — Implements the stockout intelligence service layer and business logic.
- `schemas.py` — Defines schemas for the stockout intelligence data contracts.
- `__init__.py` — Defines the modules.stockout_intelligence package surface and package-level exports.
- `Dockerfile` — Container build definition for this component.
- `features/` — Reusable SQL or contract assets that feed scoring, training, or reporting workflows.

## Interfaces and data contracts

- Main types: StockoutRiskSkuResponse, StockoutRiskSummaryResponse, StockoutRiskSkuListResponse, StockoutArtifactNotFoundError, StockoutObservationRow, StockoutSkuPredictionArtifact, StockoutRiskSummaryArtifact, StockoutRiskArtifact, _ResolvedUpload.
- Key APIs and entry points: main, router, get_stockout_risk_skus, get_stockout_risk_sku, run_stockout_risk_analysis, load_stockout_artifact, get_or_create_stockout_artifact, get_stockout_sku_predictions, get_stockout_sku_prediction.

## Operational notes

- Scope profile: internal (4), public API (1).
- Status profile: stable (4), internal (1).
- Important dependencies: __future__, router, time, pathlib, fastapi, schemas, service, pydantic, csv, json, uuid, dataclasses, datetime.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. Internal interfaces should remain aligned with adjacent modules and repository conventions. Public request and response behavior should remain backward compatible with documented API flows.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies. Python 3.11+ with FastAPI-compatible runtime dependencies.
- Maintenance guidance: keep routers, schemas, services, artifacts, and README examples synchronized when this module evolves.

## Related areas

- `tests/stockout_intelligence/` automated checks for this module when present
- `modules/common/` shared parsing and upload utilities
- `docs/` long-form capability and architecture references
