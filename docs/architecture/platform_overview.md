# Platform Overview

RetailOps is a modular retail operations platform that can be deployed as one repository while still keeping clear capability boundaries.

## End-to-end flow

1. Source data enters through CSV, database, or commerce-platform connector modules.
2. Ingestion validates, maps, and lands records in raw storage.
3. Transformations standardize raw records into trusted staging and mart layers.
4. KPI, intelligence, and reporting modules consume trusted tables instead of connector internals.
5. Outputs are delivered through APIs, dashboards, generated JSON artifacts, and report packs.
6. Serving, monitoring, and registry services govern operational model use.

## Design principles

- core services stay lightweight and reusable
- optional modules depend on shared contracts rather than on each other by default
- artifacts are reproducible from source data and module configuration
- onboarding supports both technical and non-technical operators
- extension modules add new platform reach without changing the base repository layout

## Repository reading order

Start with `core/` to understand shared contracts, then inspect `modules/` for optional capabilities, `compose/` for deployment profiles, `scripts/` for operations, and `docs/` for role-specific guidance.
