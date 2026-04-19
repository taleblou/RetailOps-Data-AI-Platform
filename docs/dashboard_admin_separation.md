# Dashboard / API separation

This project now separates dashboard pages from JSON APIs.

## Dashboard routes

- `/dashboard`
- `/dashboard/<upload_id>`
- `/dashboard/<upload_id>/<page_key>`

## API routes

All JSON APIs stay on their original `/api/...` paths, including:

- `/api/v1/dashboard-hub/workspace`
- `/api/v1/dashboard-hub/artifact/<upload_id>`
- `/api/v1/business-reports/...`
- `/api/v1/kpis/...`
- `/api/v1/forecasting/...`
- and the rest of the operational modules

## Notes

- The previous HTML route `/api/v1/dashboard-hub/<upload_id>/view` now redirects to `/dashboard/<upload_id>`.
- The admin information architecture was adapted to a Gentelella-style left-sidebar admin layout while remaining self-contained for this repository.
- The Service Directory page reads configured services and local access links from the compose files.
- The Runtime Without Services page shows offline artifact readiness without requiring external services to be running.
