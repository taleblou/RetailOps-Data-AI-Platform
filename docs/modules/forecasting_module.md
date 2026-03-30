# Forecasting Module

Forecasting provides batch demand projections, grouped metrics, interval outputs, and product-level explanations.

## Inputs

Trusted demand, inventory, pricing, and calendar signals from transformed marts.

## Outputs

Summary metrics, grouped forecasts, item-level explanations, and artifact files used by dashboards or downstream decision modules.

## Repository pointers

- `modules/forecasting/service.py`
- `modules/forecasting/router.py`
- `modules/forecasting/features/`
- `modules/forecasting/dbt_models/`
