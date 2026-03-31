# Shipment Risk Module

Supports the shipment risk layer inside the modular repository architecture. Exposes HTTP endpoints for shipment risk capabilities.
It follows the repository module pattern of service logic, API surface, schemas, optional runtime entry points, and deployment assets when those concerns are applicable.

## Directory contents

- `main.py` — Provides implementation support for the shipment risk workflow.
- `router.py` — Defines API routes for the shipment risk module.
- `service.py` — Implements the shipment risk service layer and business logic.
- `schemas.py` — Defines schemas for the shipment risk data contracts.
- `__init__.py` — Defines the modules.shipment_risk package surface and package-level exports.
- `Dockerfile` — Container build definition for this component.
- `dbt_models/` — dbt models and marts that prepare canonical inputs for this module.
- `features/` — Reusable SQL or contract assets that feed scoring, training, or reporting workflows.

## Interfaces and data contracts

- Main types: ShipmentRiskMetricsResponse, ShipmentRiskPredictionResponse, ShipmentRiskSummaryResponse, ShipmentRiskOpenOrdersResponse, ShipmentDelayPredictRequest, ManualReviewDecisionResponse, ShipmentRiskArtifactNotFoundError, ShipmentRow, ShipmentContext, ShipmentRiskMetricsArtifact, ShipmentRiskPredictionArtifact, ShipmentRiskSummaryArtifact.
- Key APIs and entry points: main, router, get_shipment_risk_open_orders, get_shipment_risk_for_shipment, post_predict_shipment_delay, post_manual_review_decision, run_shipment_risk_analysis, get_or_create_shipment_risk_artifact, get_open_order_predictions, get_open_order_prediction, predict_shipment_delay, build_manual_review_decision.

## Operational notes

- Scope profile: internal (4), public API (1).
- Status profile: stable (4), internal (1).
- Important dependencies: __future__, router, time, pathlib, fastapi, schemas, service, pydantic, csv, json, uuid, dataclasses, datetime.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. Internal interfaces should remain aligned with adjacent modules and repository conventions. Public request and response behavior should remain backward compatible with documented API flows.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies. Python 3.11+ with FastAPI-compatible runtime dependencies.
- Maintenance guidance: keep routers, schemas, services, artifacts, and README examples synchronized when this module evolves.

## Related areas

- `tests/shipment_risk/` automated checks for this module when present
- `modules/common/` shared parsing and upload utilities
- `docs/` long-form capability and architecture references
