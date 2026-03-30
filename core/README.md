# Core Platform

The `core/` directory contains shared platform layers reused by multiple modules. These are the repository building blocks for API composition, source management, transformations, setup, serving, monitoring, and worker execution.

## Main areas

- `api/` FastAPI composition, route registration, and request or response contracts.
- `ingestion/` connector contracts, registries, repositories, mapping, validation, and raw loading.
- `transformations/` dbt project assets and service wrappers for curated marts.
- `setup/` onboarding and setup-session workflows.
- `serving/` model-serving orchestration and serving contracts.
- `monitoring/` monitoring artifacts, dashboards, alerts, and override flows.
- `worker/` background-runtime entry points.
- `ai/` foundational AI contracts and dataset-builder helpers.
- `db/` SQL migrations for shared schemas and module persistence.

## Design intent

Core code should stay module-agnostic where possible. Business modules can depend on it, but `core/` should not accumulate module-specific reporting logic unless that logic is a shared platform concern.

## Maintenance notes

- Changes in `core/` often affect multiple modules and tests.
- Keep route contracts, repository assumptions, and artifact paths backward compatible unless the related docs and tests are updated together.
- Prefer adding shared abstractions here only when more than one module benefits from them.
