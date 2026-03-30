# API Layer

Provides the main application entry point and composes routers for API flows. Marks core.api as a Python package and centralizes its package-level imports.
It sits on the public API boundary and should remain aligned with request, response, and router contracts used across the platform.

## Directory contents

- `main.py` — Builds the public API surface for the API application.
- `__init__.py` — Defines the core.api package surface and package-level exports.
- `Dockerfile` — Container build definition for this component.
- `routes/` — API Routes implementation assets and supporting documentation.
- `schemas/` — API Schemas implementation assets and supporting documentation.

## Interfaces and data contracts

- Main types: this area is centered on functions, configuration, or documentation rather than exported classes.
- Key APIs and entry points: app, build_repository, create_app.

## Operational notes

- Scope profile: internal (1), public API (1).
- Status profile: internal (1), stable (1).
- Important dependencies: Standard library only, __future__, fastapi, config.settings, core.api.routes.easy_csv, core.api.routes.monitoring, core.api.routes.pro_platform.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. Public request and response behavior should remain backward compatible with documented API flows.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies. Python 3.11+ with FastAPI-compatible runtime dependencies.
- Maintenance guidance: changes here can affect multiple modules, so update downstream tests and docs in the same change set.

## Related areas

- `core/api/routes/` HTTP handlers
- `core/api/schemas/` request and response contracts
- `core/serving/` shared serving orchestration reused by API routes
