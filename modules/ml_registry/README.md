# ML Registry Module

This module completes phase 15 of the roadmap.

## What it adds

- named registries for `forecasting_model`, `shipment_delay_model`, `stockout_model`, and `return_risk_model`
- experiment-tracking metadata for each model version
- alias policy with `champion`, `challenger`, and `shadow`
- evaluation contracts and threshold gates
- promotion workflow with stored rollback points
- rollback workflow for failed promotions or degraded models

## API endpoints

- `GET /api/v1/ml-registry/summary`
- `GET /api/v1/ml-registry/models/{registry_name}`
- `POST /api/v1/ml-registry/models/{registry_name}/promote`
- `POST /api/v1/ml-registry/models/{registry_name}/rollback`

## Artifact output

The module writes a persisted state file to:

- `data/artifacts/model_registry/phase15_model_registry.json`

This keeps the current alias map, promotion history, rollback history, and evaluation state in one place.
