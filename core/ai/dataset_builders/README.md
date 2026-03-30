# Dataset Builders

Constructs reusable datasets or artifacts for AI dataset builders processing. Captures the structural rules that AI dataset builders producers and consumers must follow.

## Directory contents

- `builder.py` — Builds derived assets for the AI dataset builders workflow.
- `contracts.py` — Defines contracts and validation rules for the AI dataset builders layer.
- `freshness.py` — Implements freshness checks for the AI dataset builders workflow.
- `models.py` — Defines domain models for the AI dataset builders module.
- `__init__.py` — Defines the core.ai.dataset_builders package surface and package-level exports.

## Interfaces and data contracts

- Main types: DatasetWindow, FreshnessResult, FreshnessPolicy, FeatureContract.
- Key APIs and entry points: build_backtest_windows, build_point_in_time_dataset_sql, load_feature_contract, load_feature_contracts, evaluate_feature_freshness, evaluate_feature_freshness_map.

## Operational notes

- Scope profile: internal (5).
- Status profile: stable (4), internal (1).
- Important dependencies: builder, contracts, freshness, models, __future__, dataclasses, datetime, pathlib, yaml, typing.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. Internal interfaces should remain aligned with adjacent modules and repository conventions. File-system paths and serialized artifact formats must remain stable for downstream consumers.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies.
- Maintenance guidance: changes here can affect multiple modules, so update downstream tests and docs in the same change set.

## Related areas

- `README.md` repository-level overview and navigation entry point
