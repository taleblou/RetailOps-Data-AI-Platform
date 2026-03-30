# Returns Intelligence Tests

Validates returns intelligence behavior and protects the repository against regressions.
It should evolve alongside the implementation under test so fixtures, sample artifacts, and API expectations remain aligned.

## Directory contents

- `test_returns_intelligence.py` — Contains automated tests for the returns intelligence workflows and behaviors.

## Interfaces and data contracts

- Main types: this area is centered on functions, configuration, or documentation rather than exported classes.
- Key APIs and entry points: test_run_returns_returns_builds_scores_and_risky_products, test_get_return_risk_order_reads_saved_artifact, test_returns_router_returns_orders_products_and_detail.

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
