# Dashboard Hub

Exposes HTTP endpoints for dashboard hub capabilities. Encapsulates core processing and artifact generation for dashboard hub workflows.
It follows the repository module pattern of service logic, API surface, schemas, optional runtime entry points, and deployment assets when those concerns are applicable.

## Directory contents

- `router.py` — Defines API routes for the dashboard hub module.
- `service.py` — Implements the dashboard hub service layer and business logic.
- `schemas.py` — Defines schemas for the dashboard hub data contracts.
- `__init__.py` — Defines the modules.dashboard_hub package surface and package-level exports.

## Interfaces and data contracts

- Main types: DashboardWorkspaceResponse, DashboardWorkspacePublishRequest, DashboardWorkspaceArtifactResponse.
- Key APIs and entry points: router, get_dashboard_workspace, publish_workspace, get_published_workspace_artifact, get_dashboard_workspace_html, build_dashboard_workspace, render_dashboard_workspace_html, publish_dashboard_workspace, load_dashboard_workspace_artifact.

## Operational notes

- Scope profile: internal (3), public API (1).
- Status profile: stable (3), internal (1).
- Important dependencies: __future__, router, service, pathlib, fastapi, fastapi.responses, schemas, typing, pydantic, html, json, modules.analytics_kpi.service.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. Public request and response behavior should remain backward compatible with documented API flows. Internal interfaces should remain aligned with adjacent modules and repository conventions.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies. Python 3.11+ with FastAPI-compatible runtime dependencies.
- Maintenance guidance: keep routers, schemas, services, artifacts, and README examples synchronized when this module evolves.

## Related areas

- `tests/dashboard_hub/` automated checks for this module when present
- `modules/common/` shared parsing and upload utilities
- `docs/` long-form capability and architecture references
