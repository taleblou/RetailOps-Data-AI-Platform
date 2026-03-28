# Phase 18 setup wizard

This phase adds a real onboarding and setup layer to the platform.
It is designed to match the roadmap requirement for a **stateful wizard** with **progress logs**, **retry support**, and a **sample data mode**.

## What was missing in the received ZIP

The received repository already covered the roadmap through phase 17.
The `core/setup/` area still only contained a placeholder README.
That meant the project did not yet have a real phase 18 implementation.

## What has now been added

### Service layer

- `core/setup/service.py`
- `core/setup/__init__.py`

This service persists setup sessions as JSON artifacts and manages the full onboarding flow:

1. create store
2. choose source
3. test connection
4. map fields
5. first import
6. first dbt run
7. enable modules
8. first model training
9. publish dashboards

## API and wizard routes

- `core/api/routes/setup.py`
- `core/api/schemas/setup.py`

### JSON API

- `POST /api/v1/setup/sessions`
- `GET /api/v1/setup/sessions/{session_id}`
- `POST /api/v1/setup/sessions/{session_id}/store`
- `POST /api/v1/setup/sessions/{session_id}/source`
- `POST /api/v1/setup/sessions/{session_id}/test-connection`
- `POST /api/v1/setup/sessions/{session_id}/mapping`
- `POST /api/v1/setup/sessions/{session_id}/import`
- `POST /api/v1/setup/sessions/{session_id}/dbt-run`
- `POST /api/v1/setup/sessions/{session_id}/enable-modules`
- `POST /api/v1/setup/sessions/{session_id}/train`
- `POST /api/v1/setup/sessions/{session_id}/publish-dashboards`

### HTML wizard

- `GET /setup/wizard`
- `POST /setup/wizard/start`
- `GET /setup/sessions/{session_id}/wizard`

The HTML wizard is intentionally light.
It uses simple forms and the same backend service as the JSON API.

## Sample data mode

Sample mode uses `data/demo_csv/sample_orders_easy_csv_150.csv` and creates an enriched CSV inside `data/uploads/`.
The enriched sample includes:

- product id
- category
- product group
- available quantity

That lets the onboarding flow complete the first training step more reliably.

## Progress logging and retries

Each step stores:

- status
- attempt count
- last update time
- message
- optional artifact path

Each retry increments the attempt counter and appends a new log line.

## Artifacts written during setup

- setup session JSON under `data/artifacts/setup/sessions/`
- upload metadata under `data/uploads/`
- transform artifact under `data/artifacts/transforms/`
- dashboard artifact under `data/artifacts/dashboards/`
- training artifact under `data/artifacts/forecasts/`
- model registry artifact under `data/artifacts/model_registry/`

## Database migration

- `core/db/migrations/013_setup_wizard_phase18.sql`

This adds persistent database tables for setup sessions and setup logs.
The current phase 18 implementation uses JSON artifacts as the default runtime path, but the SQL tables are now present to match the roadmap structurally and support future promotion into DB-backed persistence.

## Tests

- `tests/setup/test_phase18_setup_wizard.py`

The tests cover both:

- the end-to-end JSON API flow
- the HTML wizard start page and session page

## Result

The repository is now aligned with the roadmap through phase 18.
