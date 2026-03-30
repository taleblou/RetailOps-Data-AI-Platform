# Module Boundaries

RetailOps is organized by module family. Core services provide the contracts. Optional modules attach to those contracts.

## Core

- `core/api` HTTP entry point and orchestration surface
- `core/db` schema migrations and bootstrap SQL
- `core/ingestion` connector framework, validation, mapping, and loading
- `core/transformations` transform execution hooks and dbt assets
- `core/serving` standardized prediction and explanation envelopes
- `core/monitoring` governance, drift, reliability, and override tracking
- `core/setup` guided onboarding workflow
- `core/ai` feature contracts and dataset builders

## Modules

- connector modules extend ingestion without changing core APIs
- operational intelligence modules consume trusted transformed tables
- business intelligence modules publish artifacts, APIs, and report packs
- platform extension modules add CDC, lakehouse, metadata, streaming, query, and feature services

## Dependency rules

- core must not depend on optional business logic
- modules may reuse shared utility code and platform contracts
- dashboards and reporting consume artifacts from module services rather than bypassing them
- docs and tests should describe capability ownership, not sequence-based naming
