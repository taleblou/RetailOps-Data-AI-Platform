# API Routes

Exposes HTTP entry points for API routes workflows. Marks core.api.routes as a Python package and centralizes its package-level imports.
It sits on the public API boundary and should remain aligned with request, response, and router contracts used across the platform.

## Directory contents

- `easy_csv.py` — Defines public API routes and request handling for the API routes surface.
- `monitoring.py` — Defines public API routes and request handling for the API routes surface.
- `pro_platform.py` — Defines public API routes and request handling for the API routes surface.
- `serving.py` — Defines public API routes and request handling for the API routes surface.
- `setup.py` — Defines public API routes and request handling for the API routes surface.
- `sources.py` — Defines public API routes and request handling for the API routes surface.
- `__init__.py` — Defines the core.api.routes package surface and package-level exports.

## Interfaces and data contracts

- Main types: this area is centered on functions, configuration, or documentation rather than exported classes.
- Key APIs and entry points: router, run_first_transform, run_first_forecast, wizard_home, wizard_detail, wizard_upload, run_monitoring_checks, get_monitoring_summary, post_manual_override, get_override_summary_endpoint, get_platform_extensions_summary, run_serving_batch_jobs.

## Operational notes

- Scope profile: public API (7).
- Status profile: stable (7).
- Important dependencies: Standard library only, __future__, csv, html, json, re, uuid, pathlib, fastapi, core.monitoring.schemas, core.monitoring.service, core.api.schemas.pro_platform, modules.advanced_serving.service, modules.cdc.service.
- Constraints: Public request and response behavior should remain backward compatible with documented API flows.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies. Python 3.11+ with FastAPI-compatible runtime dependencies.
- Maintenance guidance: changes here can affect multiple modules, so update downstream tests and docs in the same change set.

## Related areas

- `core/api/routes/` HTTP handlers
- `core/api/schemas/` request and response contracts
- `core/serving/` shared serving orchestration reused by API routes
