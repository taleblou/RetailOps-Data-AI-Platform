# retailops_forecasting Source Package

Provides a minimal package entry point for forecasting distribution metadata and typed imports.
It keeps packaging metadata intentionally small so distribution boundaries remain clear and import cycles stay out of the export surface.

## Directory contents

- `__init__.py` — Exports forecasting package metadata for demand-planning and forecast-service capabilities.
- `py.typed` — PEP 561 marker declaring inline typing support.

## Interfaces and data contracts

- Main types: PackageMetadata.
- Key APIs and entry points: PACKAGE_NAME, PACKAGE_ROLE, package_info.

## Operational notes

- Scope profile: internal (1).
- Status profile: stable (1).
- Important dependencies: Shared standard-library metadata only.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles or runtime-only dependencies.
- Compatibility: Python 3.11+ and repository-supported packaging workflows.
- Packaging guidance: keep package metadata, typed exports, and README claims consistent with the corresponding monorepo implementation.

## Related areas

- `packages/README.md` packaging workspace overview
- `pyproject.toml` build metadata for the package
- `src/` typed package source files
