# Quickstart - Standard profile

The Standard profile is the operational AI package.
It extends Lite with forecasting, shipment risk, stockout intelligence, reorder recommendations, returns intelligence, MLflow-oriented lifecycle tooling, and monitoring.

## Included modules

- everything in Lite
- forecasting
- shipment risk
- stockout intelligence
- reorder engine
- returns intelligence
- MLflow registry surfaces
- monitoring
- selected connector overlays only
- reporting extra by default

## Installation

```bash
./scripts/install.sh --profile standard --connectors csv,database,shopify
```

## Override optional extras

```bash
./scripts/install.sh --profile standard --connectors csv,database --extras reporting
```

## Upgrade an existing installation

```bash
./scripts/upgrade.sh --profile standard
```

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

Choose Standard when the customer wants real operational decision support without the added CDC, streaming, lakehouse, metadata, feature-store, and advanced-serving stack.
