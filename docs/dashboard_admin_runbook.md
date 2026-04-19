# RetailOps Admin Dashboard Runbook

This dashboard is intentionally separated from the API route space.

## Key URLs

- Dashboard home: `/dashboard/<upload_id>`
- Dashboard pages:
  - `/dashboard/<upload_id>/executive`
  - `/dashboard/<upload_id>/operations`
  - `/dashboard/<upload_id>/intelligence`
  - `/dashboard/<upload_id>/reports`
  - `/dashboard/<upload_id>/apis`
  - `/dashboard/<upload_id>/runtime`
  - `/dashboard/<upload_id>/services`
- Workspace JSON: `/api/v1/dashboard-hub/workspace?upload_id=<upload_id>`
- Published artifact metadata: `/api/v1/dashboard-hub/artifact/<upload_id>`

## Demo setup

```bash
bash scripts/load_demo_data.sh --upload-id demo-pro-csv-db
python scripts/generate_dashboard_workspace.py demo-pro-csv-db --refresh
```

## Run the API

```bash
uvicorn core.api.main:app --host 127.0.0.1 --port 8000 --reload
```

Then open:

```text
http://127.0.0.1:8000/dashboard/demo-pro-csv-db
```

## Full platform path

```bash
cp .env.example .env
./scripts/install.sh --profile pro --connectors csv,database
bash scripts/load_demo_data.sh --upload-id demo-pro-csv-db
python scripts/generate_dashboard_workspace.py demo-pro-csv-db --refresh
```

After the stack is healthy, open:

```text
http://127.0.0.1:8000/dashboard/demo-pro-csv-db
```
