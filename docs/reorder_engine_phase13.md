# Phase 13 Reorder Engine Module

Phase 13 turns prediction into a direct operational recommendation. It consumes phase 10 forecast output and phase 12 stockout output, then adds simple supply-side rules.

## What the module now does

- reads demand forecast signals from the phase 10 artifact
- reads stockout risk signals from the phase 12 artifact
- combines current inventory, inbound stock, supplier lead time, MOQ, and service target
- outputs reorder date, reorder quantity, urgency, and rationale for each SKU
- stores a reusable reorder artifact for API reuse

## Inputs

The service expects an uploaded CSV for the given `upload_id` and reuses earlier artifacts.
Useful columns are:

- `sku`
- `store_code`
- `lead_time_days`
- `supplier_moq` or `moq`
- `service_level_target`
- inventory columns already used by phase 12

## Output artifact

Artifacts are written under `data/artifacts/reorder/` and include:

- summary counts for total SKUs, urgent SKUs, and recommendations that should be placed today
- recommended reorder date and quantity per SKU
- urgency score and rationale text
- traceable feature timestamp and model version

## Database layer

Migration `core/db/migrations/008_reorder_phase13.sql` adds `predictions.reorder_recommendations`.
That keeps the roadmap requirement explicit even though this repository version stores API reuse data in JSON artifacts.

## API surface

- `GET /api/v1/reorder/recommendations`
- `GET /api/v1/reorder/{sku}`

## Decision logic in this repository version

This repository version uses a hybrid rules plus model-output approach.
It is not a heavy optimization solver.
The engine combines:

- phase 10 forecast horizons
- phase 12 stockout probability and days-to-stockout
- current inventory and inbound stock
- supplier MOQ
- service level target

That makes phase 13 concrete and testable without introducing external optimization dependencies.
