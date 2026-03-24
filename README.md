# RetailOps Data & AI Platform

A modular self-hosted retail data and AI platform for data ingestion, analytics, forecasting, monitoring, and operational decision support.

## Current state

This repository now includes:

- product and architecture docs for phases 1 to 4
- fixed SQL migrations for the canonical data model
- a working phase 5 connector framework
- three initial connectors: CSV, generic database, and Shopify skeleton
- FastAPI endpoints for source registration, testing, importing, status, and errors
- tests for mapper, validator, CSV connector, and source API

## Quick start with uv

```bash
uv sync
cp .env.example .env
uv run uvicorn core.api.main:app --reload --host 0.0.0.0 --port 8000
```

Open Swagger at `http://localhost:8000/docs`.

## Quick start with Docker Compose

```bash
docker compose -f compose/compose.core.yaml up -d postgres
uv run uvicorn core.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Run tests

```bash
uv run pytest
```
