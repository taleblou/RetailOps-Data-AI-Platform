# Metadata module

This module implements the phase 20 metadata and lineage surface around OpenMetadata.

## Included assets

- `service.py`, `router.py`, and `schemas.py` for metadata blueprint APIs
- `config/openmetadata_ingestion.yaml` for starter ingestion workflows
- `Dockerfile` and `main.py` for module-local packaging

## What the module delivers

- metadata ingestion planning for PostgreSQL, dbt, and Trino
- lineage and catalog starter definitions
- a documented place for governance-related runtime configuration
- API output that can be aggregated in the Pro platform summary

## Why it matters

The core product can operate without a metadata catalog. This module is for technical teams that want discoverability, lineage, and governance on top of the same retail data platform.
