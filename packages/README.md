# Package Workspaces

The `packages/` directory contains thin packaging workspaces that describe selective distribution surfaces for the repository.

## Available workspaces

- `retailops_core/` shared platform package surface
- `retailops_ingestion/` connector and ingestion package surface
- `retailops_forecasting/` forecasting package surface
- `retailops_monitoring/` monitoring and governance package surface
- `retailops_analytics/` analytics and reporting package surface

## Design intent

These workspaces stay intentionally small. They expose package metadata and typed markers without duplicating the full monorepo implementation.

## How to use them

Use the package workspaces when you want a narrower distribution boundary than the full repository, or when you need typed package metadata for downstream tooling.

## Maintenance rules

- Keep package README text aligned with the monorepo capability it represents.
- Keep `pyproject.toml`, `README.md`, and `src/*/__init__.py` metadata synchronized.
- Avoid adding heavy runtime logic to the package surface.
