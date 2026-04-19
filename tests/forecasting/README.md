# Forecasting Tests

Validates forecasting behavior and protects the repository against regressions.
It should evolve alongside the implementation under test so fixtures, sample artifacts, and API expectations remain aligned.

## Directory contents

- `test_first_forecast_service.py` — Contains automated tests for the forecasting workflows and behaviors.
- `test_forecasting_batch.py` — Contains automated tests for the forecasting workflows and behaviors.

## Interfaces and data contracts

- Main types: this area is centered on functions, configuration, or documentation rather than exported classes.
- Key APIs and entry points: test_run_first_forecast_builds_expected_horizons, test_run_batch_forecast_builds_summary, test_get_product_forecast_reads_product_from_artifact, test_forecasting_forecast_router_returns_summary_and_product.

## Operational notes

- Scope profile: test (2).
- Status profile: stable (2).
- Important dependencies: pathlib, modules.forecasting.service, __future__, json, fastapi.testclient, core.api.main, core.ingestion.base.repository.
- Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
- Compatibility: Python 3.11+ with pytest and repository test dependencies.
- Test guidance: keep fixtures, sample artifacts, and endpoint expectations aligned with the production modules under test.

## Related areas

- `core/` shared runtime services under test
- `modules/` business and platform modules exercised by these tests
- `data/` sample inputs and generated artifacts used during test runs
