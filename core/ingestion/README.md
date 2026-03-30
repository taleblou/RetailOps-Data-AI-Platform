# Ingestion Layer

Marks core.ingestion as a Python package and centralizes its package-level imports.
It underpins source registration, extraction, validation, mapping, and raw-loading workflows reused by connector modules.

## Directory contents

- `__init__.py` — Defines the core.ingestion package surface and package-level exports.
- `base/` — Ingestion Base Layer implementation assets and supporting documentation.

## Interfaces and data contracts

- Main types: this area is centered on functions, configuration, or documentation rather than exported classes.
- Key APIs and entry points: no file-level callable surface is documented here.

## Operational notes

- Scope profile: internal (1).
- Status profile: internal (1).
- Important dependencies: Standard library only.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies.
- Maintenance guidance: changes here can affect multiple modules, so update downstream tests and docs in the same change set.

## Related areas

- `modules/connector_*/` concrete source adapters built on this base layer
- `core/api/routes/sources.py` public source-management endpoints
- `data/` sample uploads and raw artifact roots
