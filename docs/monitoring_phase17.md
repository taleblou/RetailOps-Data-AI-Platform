# Phase 17 - AI Governance and Monitoring

This phase closes the gap between a working serving layer and a trustworthy operating system for AI.

## What was missing before this phase

The repository already had the pieces needed to score forecasts, shipment risk, stockout risk, reorder suggestions, and ML registry state.
But phase 17 itself was still incomplete.
The missing pieces were:

- no dedicated monitoring artifact that combines data checks, ML checks, and serving health
- no phase 17 migration for monitoring runs, alerts, and override feedback
- no monitoring API routes in the main FastAPI application
- no manual override logging flow that keeps retraining feedback
- no phase 17 test coverage
- no documentation or audit that marks the repository complete through phase 17

## What is now included

### 1. Monitoring artifact generation

A new monitoring service now builds a phase 17 artifact that combines:

- data checks
- ML checks
- alert policy results
- serving and dashboard metrics
- override summary

The artifact is stored under:

- `data/artifacts/monitoring/`

### 2. Data quality checks

The monitoring service now evaluates the roadmap checks for:

- null spikes
- out-of-range values
- row count anomaly
- freshness

These checks are derived from the uploaded CSV files for the requested `upload_id`.

### 3. ML quality checks

The monitoring service now evaluates:

- feature drift
- prediction drift
- calibration drift
- label-lag-aware performance checks

The phase 15 model registry is used as the main source for champion drift and calibration signals.
The current forecast, shipment-risk, and stockout artifacts are used to measure prediction distribution shifts.

### 4. Alert policy

The monitoring artifact now creates alert records with:

- `warn`
- `critical`
- `retrain_recommended`
- `disable_prediction_recommended`

This follows the roadmap requirement that monitoring should drive action instead of producing passive reports only.

### 5. Manual override logging

The phase 17 API now supports manual override logging for prediction-based decisions.
Each override stores:

- prediction type
- entity id
- original decision
- override decision
- reason
- optional feedback label
- optional user id

Override entries are kept under:

- `data/artifacts/monitoring/overrides/`

### 6. Monitoring API routes

Added routes:

- `POST /api/v1/monitoring/run`
- `GET /api/v1/monitoring/summary`
- `POST /api/v1/monitoring/overrides`
- `GET /api/v1/monitoring/overrides`

## Added files for phase 17

- `core/db/migrations/012_monitoring_phase17.sql`
- `core/monitoring/schemas.py`
- `core/monitoring/service.py`
- `core/api/routes/monitoring.py`
- `docs/monitoring_phase17.md`
- `docs/phase_1_to_17_audit.md`
- `tests/monitoring/test_phase17_monitoring.py`

## Expected result

With this phase in place, the platform now has the minimum governance layer needed to claim roadmap coverage through phase 17.
The system does not just produce predictions.
It also measures data health, prediction health, alert severity, override feedback, coverage, and confidence.
