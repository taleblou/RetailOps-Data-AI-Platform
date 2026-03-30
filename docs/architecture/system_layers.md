# System Layers

## Source and ingestion layer

Connectors, file uploads, column mapping, validation, and raw loading. This layer owns source-state tracking and shields downstream code from source-specific extraction details.

## Trust and transformation layer

Canonical schemas, dbt assets, marts, and reusable operational views. The goal is to produce stable retail entities that downstream modules can trust.

## KPI and intelligence layer

Dashboards, KPI APIs, forecasting, shipment risk, stockout intelligence, reorder logic, and returns intelligence. These modules convert trusted data into decisions, metrics, and action queues.

## AI operations layer

Feature contracts, dataset builders, model registry, serving, monitoring, and override management. This layer standardizes how AI assets are trained, delivered, and governed.

## Business reporting layer

Executive packs, commercial review reports, working-capital summaries, governance reports, and decision-intelligence outputs that package module results for stakeholders.

## Platform extension layer

CDC, streaming, lakehouse, metadata, feature store, query federation, and advanced serving. These services expand how data is moved, modeled, queried, and delivered without redefining core contracts.
