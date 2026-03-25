# Architecture Overview

## High-Level Architecture
RetailOps is a self-hosted modular retail data and AI platform.

The design follows one rule from the start: the core platform must run on its own, and every advanced module must remain optional.

## Main End-to-End Flow
1. A store sends data from CSV, database connectors, or later API/CDC sources.
2. Ingestion validates and lands source data in `raw`.
3. Transform logic standardizes `raw` into trusted `staging` and `mart` layers.
4. Analytics and ML modules consume transformed data, not raw connector internals.
5. Results are exposed through dashboards, forecasts, and operational workflows.
6. Monitoring observes platform health, data quality, and model quality.

## Core Layers
- sources
- ingestion
- data model
- feature layer
- model layer
- serving
- monitoring

## Core Runtime Services
- PostgreSQL for storage
- FastAPI for APIs and the Easy CSV wizard
- worker for background-ready execution
- MLflow starter for experiment and model tracking
- Metabase starter for dashboards

## Optional Module Families
- connector modules for new source types
- analytics and forecasting modules for business outputs
- shipment, stockout, reorder, and returns intelligence modules for operational AI
- CDC, lakehouse, metadata, feature store, streaming, and advanced serving for platform-grade expansion

## Easy CSV Phase-6 Flow
The repository now includes a starter non-technical path:
1. upload CSV
2. preview rows and columns
3. map source columns to canonical fields
4. run validation
5. import to raw
6. run the first transform
7. publish a starter dashboard view
8. generate a starter forecast

## Why This Architecture
- it supports small CSV-first users and technical teams in one repo
- it keeps the first install small and understandable
- it allows phased growth without forcing advanced dependencies into the core
- it makes connector, analytics, and ML modules swappable over time
