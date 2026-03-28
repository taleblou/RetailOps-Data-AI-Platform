# Phase 9 Feature Platform

This document closes the main gap between phases 8 and 9 in the uploaded ZIP.

## What was added

- feature contracts in `core/ai/feature_contracts/`
- typed loaders and dataset builders in `core/ai/dataset_builders/`
- physical feature table migration in `core/db/migrations/004_feature_platform.sql`
- modular SQL assets in:
  - `modules/forecasting/features/`
  - `modules/shipment_risk/features/`
  - `modules/stockout_intelligence/features/`
  - `modules/returns_intelligence/features/`

## Covered phase 9 requirements

### Feature contracts

Every contract includes:

- `name`
- `entity`
- `source`
- `transformation`
- `freshness`
- `null_handling`
- `owner`
- `training_serving_parity`

### Initial feature tables

The repository now defines starter schemas for:

- `features.product_demand_daily`
- `features.inventory_position_daily`
- `features.shipment_delay_features`
- `features.stockout_features`
- `features.customer_return_features`

### Dataset builder

`core/ai/dataset_builders/builder.py` generates point-in-time joins that enforce:

- feature timestamp must be earlier than or equal to the prediction timestamp
- latest eligible row only
- explicit train, validation, and backtest windows

### Freshness checks

`core/ai/dataset_builders/freshness.py` evaluates each feature set against warn/error
thresholds defined in the YAML contracts.

## Why this structure is useful

It keeps the phase 9 AI data layer modular and production-friendly without forcing the
repository to jump ahead into later orchestration or serving phases.
