# Phase 14 - Returns Intelligence

This document records the files added to complete the roadmap through phase 14.
The earlier repository already had the phase 9 feature placeholder for returns.
Phase 14 required a real scoring module with return probability, expected return cost, and risky products.

## Gap found in the uploaded ZIP

Before repair, `modules/returns_intelligence/` only contained:

- a short placeholder README
- a feature README
- one starter SQL asset

It did not yet include:

- a runnable service implementation
- API routes and response schemas
- a module container entrypoint
- a phase 14 migration for `predictions.return_risk_scores`
- tests for order-level scoring and risky product rollups
- repository-level documentation showing support through phase 14

## What was added

### Module runtime

- `modules/returns_intelligence/service.py`
- `modules/returns_intelligence/router.py`
- `modules/returns_intelligence/schemas.py`
- `modules/returns_intelligence/main.py`
- `modules/returns_intelligence/Dockerfile`
- `modules/returns_intelligence/__init__.py`
- `modules/returns_intelligence/README.md`

### Database layer

- `core/db/migrations/009_returns_intelligence_phase14.sql`

The migration creates:

- `features.return_risk_features`
- `predictions.return_risk_scores`

### Tests

- `tests/returns_intelligence/test_phase14_returns.py`

### Platform wiring

- `core/api/main.py`
- `compose/compose.ml.yaml`
- `README.md`
- `docs/module_boundaries.md`
- `docs/phase_1_to_14_audit.md`

## Phase 14 API surface

The repaired repository now exposes:

- `GET /api/v1/returns-risk/orders`
- `GET /api/v1/returns-risk/orders/{order_id}`
- `GET /api/v1/returns-risk/products`

## Scoring design

The phase 14 implementation stays deterministic so it works inside the self-contained repository without extra model-training infrastructure.
It uses available order-history signals and falls back to safe heuristics when the source CSV is minimal.

Signals used:

- category or inferred category
- discount rate and discount level
- shipment delay days
- customer return rate over a 180-day lookback window
- SKU return rate over a 180-day lookback window
- quantity and price context

Outputs produced:

- order-level return probability
- expected return cost
- risk band and return-cost band
- top factors and recommended action
- risky product rollups for operational review

That makes phase 14 concrete and testable while staying aligned with the roadmap requirement to connect AI to profitability.
