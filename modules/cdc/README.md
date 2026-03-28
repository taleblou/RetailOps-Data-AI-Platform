# CDC module

This module covers the phase 20 change-data-capture layer for PostgreSQL-based sources.

## Main purpose

It gives technical teams a clear starting point for moving from batch ingestion to row-level database change capture while keeping the core platform optional-module friendly.

## Included assets

- `service.py`, `router.py`, and `schemas.py` for the blueprint API
- `config/debezium-postgres.json` as the starter connector definition
- `config/cdc_profile.yaml` for project-specific CDC settings
- `Dockerfile` and `main.py` for standalone execution when needed

## Delivered outputs

- Debezium connector configuration starter
- snapshot strategy and replication-slot planning
- topic naming conventions for raw change events
- artifact generation for the Pro platform summary endpoints

## Operational note

The repository gives a structurally complete CDC module. Final production hardening still depends on the customer environment, PostgreSQL permissions, and connector deployment choices.
