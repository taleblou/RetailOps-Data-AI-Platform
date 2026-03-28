# Quickstart - Standard profile

The Standard profile is the operational AI package.
It extends Lite with forecasting, shipment risk, stockout intelligence, reorder recommendations, returns intelligence, MLflow, and monitoring.

## Included modules

- everything in Lite
- forecasting
- shipment risk
- stockout intelligence
- reorder engine
- returns intelligence
- MLflow registry
- monitoring

## Installation

```bash
./scripts/install.sh --profile standard
```

## Upgrade an existing installation

```bash
./scripts/upgrade.sh --profile standard
```

The upgrade routine refreshes dependencies, applies SQL migrations when PostgreSQL access is available, and restarts the standard stack.

## Backup and restore

Create a backup:

```bash
./scripts/backup.sh --profile standard
```

Restore the latest backup:

```bash
./scripts/restore.sh --latest --profile standard
```

## Demo run

```bash
./scripts/load_demo_data.sh --upload-id standard-demo
```

Then inspect:

- `GET /api/v1/forecast/summary?upload_id=standard-demo`
- `GET /api/v1/shipment-risk/open-orders?upload_id=standard-demo`
- `GET /api/v1/stockout-risk/skus?upload_id=standard-demo`
- `GET /api/v1/reorder/recommendations?upload_id=standard-demo`

## When to choose Standard

Choose Standard when the customer wants real operational decision support without the extra complexity of CDC, streaming, lakehouse, and metadata services.
