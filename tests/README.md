# Test Suite

The `tests/` directory groups regression coverage by capability family.

## Main test groups

- `ingestion/` connectors, registries, repositories, and onboarding contracts
- `setup/` setup wizard flows and connector source-type behavior
- `serving/` serving APIs and deployment metadata
- `monitoring/` monitoring APIs, override summaries, and artifact workflows
- `forecasting/`, `shipment_risk/`, `stockout_intelligence/`, `reorder_engine/`, and `returns_intelligence/`
- `analytics/`, `dashboard_hub/`, and `business/` reporting and dashboard outputs
- `ml_registry/` model-registry behavior
- `worker/` background job orchestration
- `packaging/` compose, quickstart, and release-asset checks
- `transformation/` transformation-layer coverage
- `ai/` dataset-builder and AI support utilities

## Test expectations

- Public routes should stay aligned with schemas and README claims.
- Connector enablement should match the runtime registry and setup source-type APIs.
- Packaging tests should protect the modular overlay and optional-extra behavior.

## Common commands

```bash
pytest -q
python scripts/validate_compose_profiles.py
```
