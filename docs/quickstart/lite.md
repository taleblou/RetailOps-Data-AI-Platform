# Quickstart - Lite profile

The Lite profile is for a small store that starts with CSV data and wants the shortest path to value.
It uses the core stack, connectors, and analytics.

## Included modules

- core services
- CSV and source connectors
- KPI analytics dashboards
- easy CSV onboarding

## Prerequisites

- Docker and Docker Compose
- optional: `uv` for local Python workflows

## Installation

```bash
./scripts/install.sh --profile lite
```

That command prepares the runtime directories, creates `.env` when needed, installs Python dependencies when `uv` is available, and starts the Lite Docker stack.

## Load demo data

```bash
./scripts/load_demo_data.sh --upload-id lite-demo
```

This creates upload metadata and starter artifacts under `data/artifacts/` so the platform can be demonstrated immediately.

## Open the platform

- API docs: `http://localhost:8000/docs`
- easy CSV wizard: `http://localhost:8000/easy-csv/wizard`
- phase 18 setup wizard: `http://localhost:8000/setup/wizard`
- Metabase: `http://localhost:3000`

## Smoke test

```bash
./scripts/health.sh
```

## When to choose Lite

Choose Lite when the customer only needs CSV onboarding, canonical modeling, KPI dashboards, and a minimal self-hosted footprint.
