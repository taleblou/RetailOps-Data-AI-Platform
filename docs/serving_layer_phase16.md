# Phase 16 - Serving Layer

This phase turns the prediction modules into a more consistent serving layer.

## What was missing before this phase

Before this completion pass, the repository already had working online APIs in the individual modules.
That meant phases 10 to 15 could score and return useful results.
But phase 16 was still incomplete because three important serving-layer pieces were missing:

- no single batch-serving orchestration for the required nightly jobs
- no shared response contract across forecast, shipment, stockout, and reorder endpoints
- no dedicated explain endpoints for the online serving layer

## What is now included

### 1. Batch serving orchestration

A new serving service now runs and summarizes the three batch jobs required by the roadmap:

- nightly forecast
- stockout daily scoring
- shipment open-order scoring

The serving-layer batch artifact is stored under:

- `data/artifacts/serving/`

### 2. Standard response envelope

The serving layer now returns one standard response shape for online inference:

- `prediction`
- `confidence`
- `interval`
- `model_version`
- `feature_timestamp`
- `explanation_summary`

Forecast uses an interval block.
Shipment delay, stockout risk, and reorder use a confidence score.
For reorder, the confidence is an operational decision-confidence derived from urgency and stockout evidence.

### 3. Explain endpoints

Each serving route now has a companion explain endpoint.
That gives a stable place for explanation text, top factors, supporting signals, and recommended action.

### 4. Artifact and schema support

Phase 16 now adds:

- `core/serving/schemas.py`
- `core/serving/service.py`
- `core/api/routes/serving.py`
- `core/db/migrations/011_serving_layer_phase16.sql`

## Added files for phase 16

- `core/db/migrations/011_serving_layer_phase16.sql`
- `core/serving/__init__.py`
- `core/serving/schemas.py`
- `core/serving/service.py`
- `core/api/routes/serving.py`
- `docs/serving_layer_phase16.md`
- `docs/phase_1_to_16_audit.md`
- `tests/serving/test_phase16_serving.py`

## API endpoints

### Batch serving

- `POST /api/v1/serving/batch/run`
- `GET /api/v1/serving/batch/summary`

### Online serving

- `GET /api/v1/serving/forecast/products/{product_id}`
- `GET /api/v1/serving/forecast/products/{product_id}/explain`
- `GET /api/v1/serving/shipment-risk/open-orders/{shipment_id}`
- `GET /api/v1/serving/shipment-risk/open-orders/{shipment_id}/explain`
- `POST /api/v1/serving/predict/shipment-delay`
- `POST /api/v1/serving/predict/shipment-delay/explain`
- `GET /api/v1/serving/stockout-risk/{sku}`
- `GET /api/v1/serving/stockout-risk/{sku}/explain`
- `GET /api/v1/serving/reorder/{sku}`
- `GET /api/v1/serving/reorder/{sku}/explain`

## Expected result

With this phase in place, the platform now has both:

- batch serving for the required recurring jobs
- online serving with a consistent response contract

That closes the main structural gap between phase 15 lifecycle management and the later monitoring and productization phases.
