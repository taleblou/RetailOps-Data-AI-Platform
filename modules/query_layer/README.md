# Query layer module

This module adds the dedicated phase 20 query-federation surface requested by the roadmap.

## Included assets

- `service.py`, `router.py`, and `schemas.py` for the query-layer blueprint API
- `config/catalogs/postgres.properties` and `config/catalogs/iceberg.properties` for Trino catalogs
- `Dockerfile` and `main.py` for standalone packaging

## Delivered outputs

- starter catalog definitions for PostgreSQL and Iceberg
- federation query examples and access patterns
- a clear boundary between the operational core database and the broader analytical query layer

## Scope note

This repository does not pretend to provide a fully tuned distributed query cluster. It does provide the code, config, and documentation surface that a phase 20 package should expose.
