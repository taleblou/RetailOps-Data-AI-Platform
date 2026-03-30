# Retailops Analytics

This directory contains supporting assets for the retailops analytics area of the repository.
It keeps packaging metadata intentionally small so distribution boundaries remain clear and import cycles stay out of the export surface.

## Directory contents

- `.python-version` — Local runtime version hint for development tooling.
- `pyproject.toml` — Package build metadata and distribution settings.
- `src/` — src implementation assets and supporting documentation.

## Interfaces and data contracts

- Main types: this area is centered on functions, configuration, or documentation rather than exported classes.
- Key APIs and entry points: no file-level callable surface is documented here.

## Operational notes

- Packaging guidance: keep package metadata, typed exports, and README claims consistent with the corresponding monorepo implementation.

## Related areas

- `packages/README.md` packaging workspace overview
- `pyproject.toml` build metadata for the package
- `src/` typed package source files
