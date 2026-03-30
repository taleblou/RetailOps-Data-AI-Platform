# Professional Dashboard Workspace

This addition creates a unified RetailOps dashboard workspace.

## Why this was added

The repository already had many analytics and reporting modules, but they were
spread across separate routes and artifact folders. The new workspace collects
those outputs into one professional view.

## What is included

- KPI overview cards
- daily sales and category revenue sections
- inventory health and shipment summary
- demand forecasting summary
- stockout and reorder control sections
- returns intelligence summary
- shipment-risk status when shipment data exists
- executive business review snapshot
- operating executive scorecard snapshot
- benchmarking snapshot
- full business report catalog
- endpoint catalog for downstream integration
- publish flow for JSON and HTML artifacts

## Main routes

- `GET /api/v1/dashboard-hub/workspace?upload_id=<id>`
- `GET /api/v1/dashboard-hub/<upload_id>/view`
- `POST /api/v1/dashboard-hub/publish`
- `GET /api/v1/dashboard-hub/artifact/<upload_id>`

## Artifact output

Default artifact root:

- `data/artifacts/dashboard_hub/`

The publish flow writes:

- `<upload_id>_dashboard_workspace.json`
- `<upload_id>_dashboard_workspace.html`
