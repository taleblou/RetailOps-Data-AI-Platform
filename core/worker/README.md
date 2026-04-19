# Worker

Provides a durable, modular background-processing engine for RetailOps jobs.

## Directory contents

- `main.py` — command-line entry point to enqueue, drain, inspect, or poll worker jobs.
- `models.py` — typed queue and run-result models.
- `jobs.py` — built-in task catalog for forecasting, shipment risk, stockout, reorder, returns, serving, monitoring, and Pro bundle generation.
- `registry.py` — stable mapping between job types and handlers.
- `service.py` — queue persistence, run logging, and execution orchestration.
- `__init__.py` — package exports for worker helpers.
- `Dockerfile` — container build definition for the worker runtime.

## Built-in job types

- `forecast_batch`
- `shipment_risk_batch`
- `stockout_batch`
- `reorder_batch`
- `returns_batch`
- `serving_batch`
- `monitoring_batch`
- `pro_platform_bundle`

## Operational notes

- Queue storage defaults to `data/artifacts/worker/queue.json`.
- Completed and failed run logs are written under `data/artifacts/worker/runs/`.
- The worker can be used in one-shot mode, drain mode, or polling daemon mode.
- Jobs stay modular and reuse the same artifact-generation services used by the API layer.
