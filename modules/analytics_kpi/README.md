# analytics_kpi

Starter KPI analytics module for the RetailOps project.

This package is designed to fit the current module shape you already have:

- `main.py` can stay as the lightweight service heartbeat entrypoint.
- `service.py` keeps the existing dashboard artifact publishing behavior and adds KPI builders.
- `router.py` exposes file-based KPI endpoints that work with the `transform_summary` payload produced by earlier pipeline steps.

## Files

```text
modules/analytics_kpi/
├── __init__.py
├── router.py
├── service.py
├── schemas.py
├── queries.py
├── export.py
└── README.md
```

## What this module does

It turns a `transform_summary` JSON payload into:

- overview KPI cards
- daily sales rows
- revenue by category rows
- inventory health rows
- shipment SLA summary
- a stored dashboard artifact JSON file
- CSV or JSON exports for downstream UI use

## Expected input

The router accepts a body shaped like this:

```json
{
  "total_orders": 42,
  "total_quantity": 128,
  "total_revenue": 3599.5,
  "daily_sales": [
    {"sales_date": "2026-03-20", "revenue": 1000, "order_count": 10},
    {"sales_date": "2026-03-21", "revenue": 2599.5, "order_count": 32}
  ],
  "revenue_by_category": [
    {"category": "Shoes", "revenue": 2100, "order_count": 18},
    {"category": "Bags", "revenue": 1499.5, "order_count": 24}
  ],
  "inventory_health": [
    {"sku": "SKU-001", "on_hand": 5, "days_of_cover": 3, "low_stock": true},
    {"sku": "SKU-002", "on_hand": 80, "days_of_cover": 25, "low_stock": false}
  ],
  "shipments": [
    {
      "shipment_id": "SHP-1",
      "promised_date": "2026-03-22",
      "delivered_date": "2026-03-21",
      "delayed": false,
      "delay_days": 0
    },
    {
      "shipment_id": "SHP-2",
      "promised_date": "2026-03-22",
      "delivered_date": "2026-03-24",
      "delayed": true,
      "delay_days": 2
    }
  ]
}
```

The service also accepts a few fallback key names such as `category_sales`, `inventory`, `shipment_rows`, and `gross_revenue`.

## API endpoints

All routes are mounted under `/api/v1/kpis`.

- `GET /overview?upload_id=<id>`
- `GET /sales-daily?upload_id=<id>&format=json|csv`
- `GET /revenue-by-category?upload_id=<id>&format=json|csv`
- `GET /inventory-health?upload_id=<id>&format=json|csv`
- `GET /shipments?upload_id=<id>`
- `POST /overview`
- `POST /sales-daily?format=json|csv`
- `POST /revenue-by-category?format=json|csv`
- `POST /inventory-health?format=json|csv`
- `POST /shipments`
- `POST /dashboard/publish`
- `GET /dashboard/artifact/{upload_id}/{dashboard_id}`
- `POST /dashboard/export/cards?format=json|csv`

## How to register the router

In your API app:

```python
from modules.analytics_kpi import router as analytics_kpi_router

app.include_router(analytics_kpi_router)
```

## Local run with uv

```bash
uv sync
uv run uvicorn core.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Example curl

### Overview

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/kpis/overview" \
  -H "Content-Type: application/json" \
  -d @sample_transform_summary.json
```

### Daily sales CSV

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/kpis/sales-daily?format=csv" \
  -H "Content-Type: application/json" \
  -d @sample_transform_summary.json \
  -o sales_daily.csv
```

### Publish dashboard artifact

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/kpis/dashboard/publish" \
  -H "Content-Type: application/json" \
  -d '{
    "upload_id": "upl_001",
    "filename": "orders.csv",
    "artifact_dir": "artifacts/analytics_kpi",
    "transform_summary": {
      "total_orders": 42,
      "total_quantity": 128,
      "total_revenue": 3599.5,
      "daily_sales": [
        {"sales_date": "2026-03-20", "revenue": 1000, "order_count": 10}
      ]
    }
  }'
```

## Notes

- This package is file-based and summary-based, so it works immediately with the current lightweight `analytics_kpi` service.
- If you later move to PostgreSQL and mart tables, you can keep the router and replace only the service/query layer.
