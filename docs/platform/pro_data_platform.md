# Pro Data Platform

The Pro deployment profile extends the core RetailOps platform with optional data-platform services that can be enabled independently.

## Included capabilities

- CDC bundles for PostgreSQL to Debezium to Redpanda
- streaming bundles for topic design, consumer groups, and processors
- lakehouse bundles for Iceberg layout, object storage, and Spark jobs
- metadata bundles for OpenMetadata ingestion and lineage
- feature-store bundles for Feast configuration and materialization schedules
- query-layer bundles for Trino catalogs and federation SQL
- advanced-serving bundles for BentoML runtime deployment and shadow routing

## Deployment model

The repository ships two parts for every Pro capability:

1. **runtime overlays** in `compose/` for local or self-hosted deployment
2. **control-plane artifacts** in module services and `scripts/generate_pro_platform_bundle.py`

This keeps the core stack independent while still letting technical teams switch on advanced modules when they need them.

## Recommended activation order

1. Start the core platform.
2. Add connector overlays if the store ingests from more than CSV.
3. Enable CDC and streaming if row-level change capture is required.
4. Enable lakehouse and query-layer services when analytical table formats or federation are needed.
5. Enable metadata and feature-store services when lineage and serving parity become operational requirements.
6. Enable advanced serving when a separate model runtime or shadow deployment path is needed.

## Operational outputs

A complete Pro deployment now includes:

- compose overlays for every extension surface
- generated deployment bundles under `data/artifacts/pro_platform/`
- readiness summaries from `/api/v1/pro-platform/readiness`
- sample configuration templates for every extension module
- health and packaging scripts for install, upgrade, backup, restore, and validation

## What remains installation-specific

Credentials, hostnames, certificates, storage backends, and capacity planning remain installation-specific. The repository covers the module boundaries, APIs, compose assets, generated configs, and operator runbooks needed to operationalize those services.
