# Fulfillment SLA Intelligence Module

Supports the fulfillment sla intelligence layer inside the modular repository architecture. Exposes HTTP endpoints for fulfillment sla intelligence capabilities.
It follows the repository module pattern of service logic, API surface, schemas, optional runtime entry points, and deployment assets when those concerns are applicable.

## Directory contents

- `main.py` — Provides implementation support for the fulfillment sla intelligence workflow.
- `router.py` — Defines API routes for the fulfillment sla intelligence module.
- `service.py` — Implements the fulfillment sla intelligence service layer and business logic.
- `schemas.py` — Defines schemas for the fulfillment sla intelligence data contracts.
- `__init__.py` — Defines the modules.fulfillment_sla_intelligence package surface and package-level exports.
- `Dockerfile` — Container build definition for this component.

## Interfaces and data contracts

- Main types: FulfillmentSlaSummaryResponse, FulfillmentSlaOrderResponse, FulfillmentSlaArtifactResponse.
- Key APIs and entry points: main, router, get_fulfillment_sla_summary, get_fulfillment_sla_detail, build_fulfillment_sla_artifact, get_fulfillment_sla_artifact, get_fulfillment_sla_order.

## Operational notes

- Scope profile: internal (4), public API (1).
- Status profile: stable (4), internal (1).
- Important dependencies: __future__, time, pathlib, fastapi, schemas, service, pydantic, collections, datetime, typing, modules.common.upload_utils.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. Internal interfaces should remain aligned with adjacent modules and repository conventions. Public request and response behavior should remain backward compatible with documented API flows.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies. Python 3.11+ with FastAPI-compatible runtime dependencies.
- Maintenance guidance: keep routers, schemas, services, artifacts, and README examples synchronized when this module evolves.

## Related areas

- `tests/fulfillment_sla_intelligence/` automated checks for this module when present
- `modules/common/` shared parsing and upload utilities
- `docs/` long-form capability and architecture references
