# RetailOps Forecasting

This workspace defines the forecasting-focused package surface for demand and planning workflows.

## What is here

- `pyproject.toml` package metadata
- `src/` typed package source files
- local tool version markers where needed

## Design intent

The workspace keeps the published surface lightweight. It should describe the capability boundary without duplicating monorepo runtime logic.

## Maintenance rules

- Keep this README aligned with `packages/README.md` and the matching monorepo modules.
- Keep package metadata and typed exports synchronized.
- Avoid introducing heavy runtime-only dependencies in this workspace.
