# Forecasting Module

This module now covers the roadmap through phase 10.

## Scope

- starter first forecast for the easy CSV path
- phase 10 batch forecast service for all active SKUs in an uploaded dataset
- baseline model comparison between seasonal naive and moving average
- rolling backtest metrics: MAE, RMSE, MAPE, and bias
- interval outputs for 7, 14, and 30 day demand forecasts
- stockout probability estimation from uploaded or demand-derived inventory
- FastAPI endpoints:
  - `GET /api/v1/forecast/summary`
  - `GET /api/v1/forecast/products/{product_id}`

## Main files

- `modules/forecasting/service.py`
- `modules/forecasting/router.py`
- `modules/forecasting/schemas.py`
- `modules/forecasting/dbt_models/forecast_training_base.sql`
- `modules/forecasting/features/product_demand_daily.sql`
