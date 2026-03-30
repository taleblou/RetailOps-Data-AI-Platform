# Transformation Layer

Encapsulates core processing and artifact generation for transformations workflows. Marks core.transformations as a Python package and centralizes its package-level imports.

## Directory contents

- `service.py` — Implements the transformations service layer and business logic.
- `__init__.py` — Defines the core.transformations package surface and package-level exports.
- `.env.example` — Example environment variables for local configuration.
- `dbt_project.yml` — dbt project manifest for transformation models and macros.
- `profiles.yml` — dbt connection profile template for this transformation workspace.
- `macros/` — Macros implementation assets and supporting documentation.
- `models/` — Models implementation assets and supporting documentation.
- `profiles/` — Profile-specific configuration assets for local or packaged execution.

## Interfaces and data contracts

- Main types: TransformDailyMetricArtifact, TransformArtifact.
- Key APIs and entry points: run_first_transform.

## Operational notes

- Scope profile: internal (2).
- Status profile: internal (1), stable (1).
- Important dependencies: __future__, csv, json, uuid, dataclasses, datetime.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. File-system paths and serialized artifact formats must remain stable for downstream consumers.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies.
- Maintenance guidance: changes here can affect multiple modules, so update downstream tests and docs in the same change set.

## Related areas

- `README.md` repository-level overview and navigation entry point
