# Phase 12 Stockout Intelligence Module

Phase 12 connects the forecast and feature layers to a direct inventory action.

## What the module now does

- computes days-to-stockout for each SKU
- estimates stockout probability from demand, inventory, inbound stock, and lead time
- assigns a reorder urgency score
- estimates expected lost sales during the lead-time window
- stores a reusable stockout artifact for API reuse

## Inputs

The service reads a CSV for a given `upload_id`.
Expected minimum columns:

- `order_date`
- `sku`
- `quantity`

Strongly recommended operational columns:

- `store_code`
- `available_qty` or `on_hand_qty`
- `in_transit_qty`
- `lead_time_days`
- `unit_price`

## Output artifact

Artifacts are written under `data/artifacts/stockout_risk/` and include:

- summary counts for total, at-risk, and critical SKUs
- latest days-to-stockout and stockout probability per SKU
- reorder urgency score and expected lost sales estimate
- recommended action text for planners

## Database layer

Migration `core/db/migrations/007_stockout_phase12.sql` adds `predictions.stockout_risk_daily`.
That keeps the roadmap requirement explicit even though this repository version stores API reuse data in JSON artifacts.

## API surface

- `GET /api/v1/stockout-risk/skus`
- `GET /api/v1/stockout-risk/{sku}`

## Scoring logic in this repository version

This repository version uses a deterministic operational scorer.
It combines:

- cover days versus supplier lead time
- inbound stock relief
- recent demand acceleration
- recent stockout history in the upload

That makes the phase 12 module concrete and testable without a separate trained model artifact.
