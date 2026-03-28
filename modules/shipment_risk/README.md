# Shipment Risk Module

This module now covers the roadmap through phase 11.

## Scope

- feature contract and feature SQL from phase 9
- phase 11 shipment-delay scoring for open orders
- evaluation metrics for ROC-AUC, PR-AUC, calibration, precision, and recall
- probability, risk band, explanation factors, and recommended action per shipment
- manual-review trigger for risky orders
- FastAPI endpoints:
  - `GET /api/v1/shipment-risk/open-orders`
  - `GET /api/v1/shipment-risk/open-orders/{shipment_id}`
  - `POST /api/v1/predict/shipment-delay`
  - `POST /api/v1/shipment-risk/manual-review`

## Main files

- `modules/shipment_risk/service.py`
- `modules/shipment_risk/router.py`
- `modules/shipment_risk/schemas.py`
- `modules/shipment_risk/dbt_models/shipment_risk_features.sql`
- `modules/shipment_risk/features/shipment_delay_features.sql`
- `core/db/migrations/006_shipment_risk_phase11.sql`
