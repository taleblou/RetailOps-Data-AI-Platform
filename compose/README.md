# Compose Profiles

The `compose/` directory contains Docker Compose overlays split by capability slice.

## Core overlays

- `compose.core.yaml` base services that every profile needs
- `compose.analytics.yaml` dashboarding and reporting services
- `compose.ml.yaml` MLflow-oriented lifecycle services
- `compose.monitoring.yaml` observability and governance services

## Connector overlays

Each connector has its own overlay file:

- `compose.connector_csv.yaml`
- `compose.connector_db.yaml`
- `compose.connector_shopify.yaml`
- `compose.connector_woocommerce.yaml`
- `compose.connector_adobe_commerce.yaml`
- `compose.connector_bigcommerce.yaml`
- `compose.connector_prestashop.yaml`

`compose.connectors.yaml` still exists as an aggregate overlay for full-stack scenarios, but the normal install path now selects connector overlays one by one.

## Platform-extension overlays

- `compose.cdc.yaml`
- `compose.streaming.yaml`
- `compose.lakehouse.yaml`
- `compose.query.yaml`
- `compose.metadata.yaml`
- `compose.feature_store.yaml`
- `compose.advanced_serving.yaml`

## How profiles are assembled

- Lite uses the core and analytics overlays plus the selected connector overlays.
- Standard adds ML and monitoring overlays.
- Pro adds the optional data-platform overlays.

The installer writes the resolved overlay list into `COMPOSE_FILES` and uses the same resolution logic for `docker compose` commands.

## Commands

```bash
./scripts/install.sh --profile lite --connectors csv
./scripts/install.sh --profile standard --connectors csv,database,shopify
./scripts/install.sh --profile pro --connectors woocommerce
python scripts/validate_compose_profiles.py
```

## Validation expectations

- Every overlay must contain a valid `services` mapping.
- Every referenced Dockerfile must exist.
- Profile sample files must expose connector and optional-extra settings.
- Optional service Dockerfiles should install the matching Python extras.

## Maintenance rules

- Keep services isolated by capability instead of expanding unrelated overlays.
- Keep ports, volumes, env files, and service names aligned with `config/` and `scripts/`.
- Add new connector services as separate `compose.connector_*.yaml` files.
