# Lakehouse module

This module provides the phase 20 lakehouse starter layer for teams that want object-storage analytics beyond the core PostgreSQL workflow.

## Included assets

- `service.py`, `router.py`, and `schemas.py` for the lakehouse blueprint API
- `config/lakehouse_layout.yaml` for bronze, silver, and gold conventions
- `jobs/bronze_to_silver.sql` as a starter transformation asset
- `Dockerfile` and `main.py` for standalone module execution

## Delivered outputs

- object-storage folder layout guidance
- Iceberg catalog planning
- bronze, silver, and gold zone definitions
- starter job assets for Spark-oriented processing

## Scope note

This repository focuses on structural completeness and a clear extension path. Real object storage, Spark infrastructure, and catalog deployment still need environment-specific setup.
