# returns_intelligence

Phase 14 turns the earlier feature placeholder into a runnable return-risk module.

## What it does

The module scores order lines for:

- return probability within a configurable 30-day decision window
- expected return cost
- risky products that should be reviewed before the next campaign

## Inputs used in the phase 14 implementation

The phase 14 service reads the uploaded order CSV for a given `upload_id`.
When the source file already includes extra columns such as category, discount, delay, or return flags,
it uses them directly.
When they are missing, it falls back to deterministic heuristics so the module still works on the
simple demo CSV files that already exist in the repository.

Signals include:

- category or inferred category bucket
- discount level
- shipment delay days
- customer return rate over the recent 180-day history window
- SKU return rate over the recent 180-day history window

## Outputs

- phase 14 JSON artifact under `data/artifacts/returns_risk/`
- order-level scores for `predictions.return_risk_scores`
- product rollups for risky SKUs
- API routes for orders, order detail, and risky products

## API routes

- `GET /api/v1/returns-risk/orders`
- `GET /api/v1/returns-risk/orders/{order_id}`
- `GET /api/v1/returns-risk/products`
