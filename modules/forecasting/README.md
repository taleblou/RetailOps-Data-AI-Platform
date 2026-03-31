# Forecasting Module

Supports the forecasting layer inside the modular repository architecture. Exposes HTTP endpoints for forecasting capabilities.
It follows the repository module pattern of service logic, API surface, schemas, optional runtime entry points, and deployment assets when those concerns are applicable.

## Directory contents

- `main.py` — Provides implementation support for the forecasting workflow.
- `router.py` — Defines API routes for the forecasting module.
- `service.py` — Implements the forecasting service layer and business logic.
- `schemas.py` — Defines schemas for the forecasting data contracts.
- `__init__.py` — Defines the modules.forecasting package surface and package-level exports.
- `Dockerfile` — Container build definition for this component.
- `dbt_models/` — dbt models and marts that prepare canonical inputs for this module.
- `features/` — Reusable SQL or contract assets that feed scoring, training, or reporting workflows.

## Interfaces and data contracts

- Main types: ForecastMetricResponse, ForecastModelScoreResponse, ForecastIntervalResponse, ForecastDailyIntervalResponse, ForecastGroupedMetricResponse, ForecastProductResponse, ForecastHorizonArtifact, ForecastDailyPointArtifact, ForecastArtifact, ForecastMetricArtifact, ForecastModelScoreArtifact, ForecastIntervalArtifact.
- Key APIs and entry points: main, router, get_forecast_summary, get_forecast_product, run_first_forecast, run_batch_forecast, load_batch_forecast_artifact, get_or_create_batch_forecast_artifact, get_product_forecast.

## Operational notes

- Scope profile: internal (4), public API (1).
- Status profile: stable (4), internal (1).
- Important dependencies: Standard library only, __future__, time, pathlib, fastapi, schemas, service, pydantic, csv, json, math, uuid, collections.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. Internal interfaces should remain aligned with adjacent modules and repository conventions. Public request and response behavior should remain backward compatible with documented API flows.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies. Python 3.11+ with FastAPI-compatible runtime dependencies.
- Maintenance guidance: keep routers, schemas, services, artifacts, and README examples synchronized when this module evolves.

## Related areas

- `tests/forecasting/` automated checks for this module when present
- `modules/common/` shared parsing and upload utilities
- `docs/` long-form capability and architecture references
