# Shared Module Utilities

Supports the common layer inside the modular repository architecture. Marks modules.common as a Python package and centralizes its package-level imports.
It follows the repository module pattern of service logic, API surface, schemas, optional runtime entry points, and deployment assets when those concerns are applicable.

## Directory contents

- `upload_utils.py` — Provides implementation support for the common workflow.
- `__init__.py` — Defines the modules.common package surface and package-level exports.

## Interfaces and data contracts

- Main types: this area is centered on functions, configuration, or documentation rather than exported classes.
- Key APIs and entry points: to_text, to_float, to_int, normalize_key, canonical_value, parse_iso_date.

## Operational notes

- Scope profile: internal (2).
- Status profile: internal (1), stable (1).
- Important dependencies: __future__, csv, json, datetime, pathlib, typing.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. File-system paths and serialized artifact formats must remain stable for downstream consumers.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies.
- Maintenance guidance: keep routers, schemas, services, artifacts, and README examples synchronized when this module evolves.

## Related areas

- `tests/common/` automated checks for this module when present
- `modules/common/` shared parsing and upload utilities
- `docs/` long-form capability and architecture references
