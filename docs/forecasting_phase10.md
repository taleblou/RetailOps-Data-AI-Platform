# Phase 10 Forecasting Module

This document records the concrete files added to lift forecasting from the phase 6 starter forecast to the phase 10 operational forecast module requested in the roadmap.

## What phase 10 required

The PDF roadmap requires:

- baseline models: seasonal naive and moving average
- demand forecasting for 7, 14, and 30 days
- interval outputs: p10, p50, and p90
- stockout probability in the forecast output
- rolling backtesting
- metrics: MAE, RMSE, MAPE, and bias
- a batch scoring job for all active SKUs
- API endpoints for forecast summary and per-product forecasts

## Files added or completed

- `modules/forecasting/README.md`
- `modules/forecasting/router.py`
- `modules/forecasting/schemas.py`
- `modules/forecasting/service.py` updated with phase 10 batch forecasting logic
- `core/db/migrations/005_forecasting_phase10.sql`
- `tests/forecasting/test_phase10_forecasting.py`
- `docs/phase_1_to_10_audit.md`

## Service behavior

### Baseline model comparison

The phase 10 service evaluates two baseline candidates per product:

- `seasonal_naive`
- `moving_average`

The service runs a rolling one-step backtest over each product demand history. The selected model is the one with the lowest MAE, with RMSE and bias used as tie breakers.

### Forecast outputs

Each product forecast now includes:

- 30 daily interval predictions
- 7, 14, and 30 day horizon summaries
- `p10`, `p50`, and `p90`
- `stockout_probability`
- `feature_timestamp`
- `model_version`
- explanation text describing the selected baseline and inventory source

### Inventory source

If the uploaded file includes a usable inventory column, that value is used directly.
Otherwise the service falls back to an estimated inventory proxy derived from recent demand.
The response makes this explicit through `inventory_source`.

### Batch artifact

The batch run writes a JSON artifact under `data/artifacts/forecasts/` with:

- summary statistics
- category-level backtest rollups
- product-group-level backtest rollups
- product-level forecast details

## API endpoints

### `GET /api/v1/forecast/summary`

Returns the latest batch artifact for an upload, or builds one on demand.

Query parameters:

- `upload_id`
- `uploads_dir`
- `artifact_dir`
- `refresh`

### `GET /api/v1/forecast/products/{product_id}`

Returns the product-level forecast for one SKU or product key from the batch artifact.

## Notes

This implementation keeps the existing phase 6 easy-CSV starter forecast intact. It adds the fuller phase 10 layer alongside it, so the simple onboarding path still works while the forecasting module now has a real operational interface.
