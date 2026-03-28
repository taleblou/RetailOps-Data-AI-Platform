# Phase 11 Shipment Risk Module

Phase 11 adds a real shipment-delay module on top of the feature layer prepared in phase 9.

## What the module now does

- scores open shipments for delay risk
- returns probability and risk band
- explains the strongest factors for each score
- recommends an operational action
- raises a manual-review flag for risky orders
- stores a JSON artifact for reuse by the API layer

## Inputs

The phase 11 service reads a shipment CSV for a given `upload_id`.

Expected columns:

- `Shipment ID`
- `Order ID`
- `Store Code`
- `Carrier`
- `Shipment Status`
- `Promised Date`
- `Actual Delivery Date`
- optional `Order Date`
- optional `Inventory Lag Days`

## Output artifact

Artifacts are written under `data/artifacts/shipment_risk/` and include:

- summary counts for open, high-risk, and manual-review orders
- evaluation metrics: ROC-AUC, PR-AUC, calibration gap, precision, and recall
- ranked open-order predictions with probability, band, factors, and action

## API surface

- `GET /api/v1/shipment-risk/open-orders`
- `GET /api/v1/shipment-risk/open-orders/{shipment_id}`
- `POST /api/v1/predict/shipment-delay`
- `POST /api/v1/shipment-risk/manual-review`

## Scoring logic in this repository version

This repository version uses a deterministic rules-plus-history scorer so the project remains fully self-contained.
It uses the following operational signals:

- carrier delay rate over the recent 30 day window
- store or region delay trend over the recent 30 day window
- warehouse backlog over the recent 7 day window
- overdue days versus the promised date
- inventory lag days when available
- shipment status and weekend ordering effect

This is enough to make the phase 11 module concrete and testable without requiring external model files.
