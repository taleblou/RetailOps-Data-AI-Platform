# Reorder Engine Module

The reorder engine translates demand, stock, and supply signals into replenishment recommendations.

## Inputs

Forecast-aware demand signals, current inventory, safety-stock assumptions, and inbound supply context.

## Outputs

Suggested reorder quantities, urgency bands, and operational commentary for planners or dashboard consumers.

## Repository pointers

- `modules/reorder_engine/service.py`
- `modules/reorder_engine/router.py`
- `tests/reorder_engine/`
