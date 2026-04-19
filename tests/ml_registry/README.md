# ML Registry Tests

Validates ml registry behavior and protects the repository against regressions.
It should evolve alongside the implementation under test so fixtures, sample artifacts, and API expectations remain aligned.

## Directory contents

- `test_ml_registry.py` — Contains automated tests for the ml registry workflows and behaviors.

## Interfaces and data contracts

- Main types: this area is centered on functions, configuration, or documentation rather than exported classes.
- Key APIs and entry points: test_run_model_registry_builds_named_registries, test_promote_and_rollback_registry_registry_updates_aliases, test_get_model_registry_details_exposes_threshold_gates, test_registry_router_returns_summary_details_promote_and_rollback.

## Operational notes

- Scope profile: test (1).
- Status profile: stable (1).
- Important dependencies: __future__, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, modules.ml_registry.service.
- Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
- Compatibility: Python 3.11+ with pytest and repository test dependencies.
- Test guidance: keep fixtures, sample artifacts, and endpoint expectations aligned with the production modules under test.

## Related areas

- `core/` shared runtime services under test
- `modules/` business and platform modules exercised by these tests
- `data/` sample inputs and generated artifacts used during test runs
