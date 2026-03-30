# Compose Profiles

The `compose/` directory contains Docker Compose overlays for assembling RetailOps environments from reusable capability slices instead of one monolithic deployment file.

## What lives here

- `compose.core.yaml` for shared base services.
- `compose.connectors.yaml` for source integration services.
- `compose.analytics.yaml` for dashboarding and reporting services.
- `compose.ml.yaml` for model lifecycle and related runtime services.
- `compose.monitoring.yaml` for observability and governance services.
- `compose.cdc.yaml`, `compose.streaming.yaml`, `compose.lakehouse.yaml`, `compose.metadata.yaml`, `compose.feature_store.yaml`, `compose.query.yaml`, and `compose.advanced_serving.yaml` for optional platform extensions.

## Usage model

Operators combine these overlays with environment settings from `config/` and helper scripts from `scripts/`. This keeps deployment profiles modular and lets teams enable only the components they need.

## Maintenance notes

- Keep service names, ports, volumes, and environment variables aligned with `config/` and `docs/operations/`.
- Add new overlays as focused capability slices instead of expanding unrelated compose files.
- Keep extension overlays optional. The base stack should stay usable without them.
