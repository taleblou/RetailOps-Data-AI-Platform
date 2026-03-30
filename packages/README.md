# Package Workspaces

The `packages/` directory contains lightweight packaging workspaces for selectively distributing repository capabilities as typed Python packages.

## Packages

- `retailops_core/` shared platform metadata and package surface for core capabilities.
- `retailops_ingestion/` package surface for ingestion-oriented capabilities.
- `retailops_forecasting/` package surface for forecasting-oriented capabilities.
- `retailops_monitoring/` package surface for observability and governance capabilities.
- `retailops_analytics/` package surface for analytics and reporting capabilities.

## Design intent

These workspaces are intentionally thin. They describe distribution boundaries and typed exports without duplicating the full monorepo implementation.

## Maintenance notes

- Keep package metadata and README descriptions aligned with the corresponding monorepo modules.
- Avoid placing heavy runtime logic in the package entry points.
- Keep typed export markers and `pyproject.toml` metadata synchronized.
