# reorder_engine

Phase 13 upgrades this module from a placeholder into a runnable reorder recommendation engine.

## What it now does

- pulls demand forecast signals from phase 10
- pulls stockout risk signals from phase 12
- combines current inventory, inbound stock, lead time, MOQ, and service target
- produces reorder date, reorder quantity, urgency, and rationale per SKU
- exposes list and detail APIs for the latest reorder artifact
- writes a reusable JSON artifact under `data/artifacts/reorder/`

## Expected input columns

The phase 13 service reads the uploaded CSV for a given `upload_id`.
Useful columns are:

- `sku`
- `store_code`
- optional `lead_time_days`
- optional `supplier_moq` or `moq`
- optional `service_level_target`
- optional inventory columns already used by phase 12

## API surface

- `GET /api/v1/reorder/recommendations`
- `GET /api/v1/reorder/{sku}`

## Notes for this repository version

This repository version keeps the phase 13 logic deterministic and self-contained.
It uses a hybrid rules plus model-output approach, not a heavy optimization solver.
That keeps the module practical, testable, and aligned to the roadmap PDF.
