# Serving Layer

Encapsulates core processing and artifact generation for serving workflows. Standardizes structured payloads used by the serving layer.

## Directory contents

- `service.py` — Implements the serving service layer and business logic.
- `schemas.py` — Defines schemas for the serving data contracts.
- `__init__.py` — Defines the core.serving package surface and package-level exports.

## Interfaces and data contracts

- Main types: ServingBatchRunRequest, ServingBatchJobResponse, ServingBatchArtifactResponse, ServingPredictionResponse, ServingExplainResponse, ServingArtifactNotFoundError.
- Key APIs and entry points: run_batch_serving, get_or_create_batch_serving_artifact, get_forecast_serving_response, get_forecast_explain_response, get_shipment_open_order_serving_response, get_shipment_open_order_explain_response.

## Operational notes

- Scope profile: internal (3).
- Status profile: stable (2), internal (1).
- Important dependencies: schemas, __future__, typing, pydantic, json, uuid, datetime, pathlib.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. Internal interfaces should remain aligned with adjacent modules and repository conventions. File-system paths and serialized artifact formats must remain stable for downstream consumers.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies. Python 3.11+ with repository configuration dependencies.
- Maintenance guidance: changes here can affect multiple modules, so update downstream tests and docs in the same change set.

## Related areas

- `README.md` repository-level overview and navigation entry point
