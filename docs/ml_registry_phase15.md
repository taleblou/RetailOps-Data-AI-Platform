# Phase 15 - Model Registry, Evaluation, and Lifecycle

This phase turns the AI layer into a production-style lifecycle instead of a set of isolated model scripts.

## What was missing before this phase

Before this completion pass, the repository had only a placeholder file in `modules/ml_registry/README.md`.
That meant phase 15 was not actually implemented even though phases 10 to 14 already produced model versions and artifacts.

## What is now included

### 1. Named registries

The project now has explicit registry definitions for:

- `forecasting_model`
- `shipment_delay_model`
- `stockout_model`
- `return_risk_model`

Each registry contains multiple model versions and an alias map.

### 2. Alias policy

The alias policy now exists in code and persisted artifact state:

- `champion`: the current production version
- `challenger`: the next version waiting for approval
- `shadow`: a version that is monitored in parallel without replacing production

### 3. Experiment tracking state

The module persists model lifecycle state to:

- `data/artifacts/model_registry/phase15_model_registry.json`

That file stores:

- experiment tracking enabled flag
- model versions per registry
- metrics and baseline metrics
- calibration error
- drift score
- evaluation result
- promotion history
- rollback history
- current alias assignments

### 4. Evaluation contract and threshold gates

Each registry now has a formal evaluation contract that defines:

- primary metric
- optimization direction (`min` or `max`)
- minimum improvement versus baseline
- maximum calibration error
- maximum drift score

A promotion is allowed only when all threshold gates pass.

### 5. Rollback flow

The rollback flow is now implemented in code.
Every promotion stores the previous alias map.
Rollback can then either:

- restore the alias map from the last promotion event
- move `champion` to an explicit target version

## Added files for phase 15

- `core/db/migrations/010_ml_registry_phase15.sql`
- `modules/ml_registry/service.py`
- `modules/ml_registry/router.py`
- `modules/ml_registry/schemas.py`
- `modules/ml_registry/main.py`
- `modules/ml_registry/Dockerfile`
- `docs/ml_registry_phase15.md`
- `tests/ml_registry/test_phase15_ml_registry.py`
- `docs/phase_1_to_15_audit.md`

## API endpoints

- `GET /api/v1/ml-registry/summary`
- `GET /api/v1/ml-registry/models/{registry_name}`
- `POST /api/v1/ml-registry/models/{registry_name}/promote`
- `POST /api/v1/ml-registry/models/{registry_name}/rollback`

## Expected result

With this phase in place, the AI stack now has a real lifecycle layer.
That closes the main structural gap between phases 14 and 15.
