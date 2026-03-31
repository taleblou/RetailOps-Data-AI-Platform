# Repo

Supports the feature store repo layer inside the modular repository architecture.

## Directory contents

- `feature_views.py` — Provides implementation support for the feature store repo workflow.
- `feature_store.yaml` — Feast repository configuration for feature-store resources.

## Interfaces and data contracts

- Main types: this area is centered on functions, configuration, or documentation rather than exported classes.
- Key APIs and entry points: no file-level callable surface is documented here.

## Operational notes

- Scope profile: internal (1).
- Status profile: stable (1).
- Important dependencies: __future__, datetime, feast, feast.types.
- Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies.
- Maintenance guidance: keep routers, schemas, services, artifacts, and README examples synchronized when this module evolves.

## Related areas

- `tests/feature_store/` automated checks for this module when present
- `modules/common/` shared parsing and upload utilities
- `docs/` long-form capability and architecture references
