# stockout_intelligence

Phase 12 upgrades this module from feature scaffolding into a runnable stockout-risk service.

## What it now does

- computes days-to-stockout per SKU
- estimates stockout probability
- assigns a reorder urgency score
- estimates expected lost sales value during supplier lead time
- exposes SKU-level APIs for the latest stockout artifact
- writes a reusable JSON artifact under `data/artifacts/stockout_risk/`

## Expected input columns

The phase 12 service reads an order or inventory-style CSV for a given `upload_id`.
Useful columns are:

- `order_date`
- `sku`
- `quantity`
- `store_code`
- optional `available_qty` or `on_hand_qty`
- optional `in_transit_qty`
- optional `lead_time_days`
- optional `unit_price`

## API surface

- `GET /api/v1/stockout-risk/skus`
- `GET /api/v1/stockout-risk/{sku}`

## Notes for this repository version

This repository version keeps the phase 12 logic deterministic and self-contained.
It uses recent demand, available inventory, inbound stock, and lead time to rank SKU risk.
That keeps the project testable without external model files while still producing a concrete operational output.
