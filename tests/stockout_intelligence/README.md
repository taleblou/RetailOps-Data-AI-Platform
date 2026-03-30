# Stockout Intelligence Tests

Validates stockout intelligence behavior and protects the repository against regressions.
It should evolve alongside the implementation under test so fixtures, sample artifacts, and API expectations remain aligned.

## Directory contents

- `test_stockout_intelligence.py` — Contains automated tests for the stockout intelligence workflows and behaviors.

## Interfaces and data contracts

- Main types: this area is centered on functions, configuration, or documentation rather than exported classes.
- Key APIs and entry points: test_run_stockout_stockout_builds_ranked_predictions, test_get_stockout_sku_prediction_reads_saved_artifact, test_stockout_router_returns_stockout_list_and_detail.

## Operational notes

- Scope profile: test (1).
- Status profile: stable (1).
- Important dependencies: __future__, json, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository.
- Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
- Compatibility: Python 3.11+ with pytest and repository test dependencies.
- Test guidance: keep fixtures, sample artifacts, and endpoint expectations aligned with the production modules under test.

## Related areas

- `core/` shared runtime services under test
- `modules/` business and platform modules exercised by these tests
- `data/` sample inputs and generated artifacts used during test runs
