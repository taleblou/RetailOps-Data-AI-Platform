# Architecture Overview

## High-Level Architecture
The platform is designed as a self-hosted modular system for retail data and AI operations.

## Main Flow
1. Data enters from CSV files, databases, APIs, or optional CDC streams.
2. Ingestion loads data into raw tables.
3. Transformations standardize data into staging and mart layers.
4. Feature tables are built for AI use cases.
5. Models generate forecasts and risk predictions.
6. Results are served through APIs, dashboards, and operational workflows.
7. Monitoring tracks data quality, model quality, drift, and usage.

## Core Design Rule
The core platform must run without Pro modules.

## Core Layers
- Sources
- Ingestion
- Data model
- Feature layer
- Model layer
- Serving
- Monitoring

## Optional Pro Extensions
- CDC
- Streaming
- Lakehouse
- Metadata
- Feature store
- Advanced model serving

## Why This Architecture
- Supports small users and advanced teams
- Keeps the initial setup simple
- Allows gradual expansion
- Prevents the core from being blocked by advanced dependencies