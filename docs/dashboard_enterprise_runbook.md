# Dashboard Enterprise Runbook

## What is included

The enterprise dashboard workspace now includes:

- Overview
- Executive Command Center
- Operational Analytics
- Working Capital
- Commercial Review
- Governance & Trust
- Decision Center
- Portfolio Intelligence
- Capabilities
- Runtime Without Services
- Service Directory
- Report Directory

## Main endpoints

- Workspace JSON: `/api/v1/dashboard-hub/workspace?upload_id=<upload_id>`
- Workspace HTML: `/api/v1/dashboard-hub/<upload_id>/view`
- Direct page route: `/api/v1/dashboard-hub/<upload_id>/page/<page_key>`
- Published artifact: `/api/v1/dashboard-hub/artifact/<upload_id>`

## Local generation

```bash
bash scripts/load_demo_data.sh --upload-id demo-pro-csv-db
python scripts/generate_dashboard_workspace.py demo-pro-csv-db --refresh
```

## Page keys

- `overview`
- `executive`
- `operations`
- `working_capital`
- `commercial`
- `governance`
- `decision`
- `portfolio`
- `capabilities`
- `runtime`
- `services`
- `reports`

## Notes on service links

The service directory uses the compose overlays inside `compose/`.
It shows configured local access URLs based on the declared port mappings.
It does not probe live containers.

## Notes on runtime without services

The runtime page reports what is already available from local files and generated artifacts:

- upload metadata
- source CSV path
- transform summary
- forecast summary
- starter dashboard summary
- published workspace JSON
- published workspace HTML

This makes it clear what can be reviewed even before the Docker stack is running.
