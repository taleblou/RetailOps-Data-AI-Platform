# Core Platform

The `core/` directory contains the reusable platform layers that multiple modules build on.

## Subsystems

### `api/`

The public HTTP surface. This area composes the FastAPI application, registers routers, owns shared schemas, and exposes setup, source-management, monitoring, serving, and platform-summary endpoints.

### `ingestion/`

The source-ingestion foundation. This area owns connector contracts, registry composition, source records, raw loading, state tracking, and repository abstractions.

### `transformations/`

Trusted transformation assets and wrappers around the curated mart layer.

### `setup/`

The onboarding workflow engine used by the setup wizard and first-run bootstrap flows.

### `serving/`

Shared model-serving orchestration, artifact surfaces, and deployment metadata.

### `monitoring/`

Monitoring artifacts, alert summaries, governance controls, and override workflows.

### `worker/`

Background job orchestration for recurring analytics, bundle generation, and operational tasks.

### `ai/`

Dataset-builder helpers, feature contracts, and AI-facing shared assets.

### `db/`

Shared SQL schema and migration assets.

## Design rules

- Core code should stay reusable across modules.
- Shared abstractions belong here only when more than one module benefits from them.
- Connector enablement and setup source types should stay aligned with the runtime registry.
- Optional dependency handling should fail gracefully when a capability is not installed.

## Main integration points

- `config/settings.py` for typed runtime settings
- `core/api/main.py` for API composition
- `core/ingestion/base/registry.py` for connector registration
- `core/ingestion/base/repository.py` for persistence backends
- `core/setup/service.py` for setup-session workflows
- `core/worker/jobs.py` for background jobs

## Maintenance notes

- Update tests whenever a route contract, registry contract, or artifact path changes.
- Keep core file headers, README text, and docs terminology synchronized.
- Preserve backwards compatibility for public routes unless docs and tests are updated in the same change.
