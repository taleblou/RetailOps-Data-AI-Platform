# Lite Quickstart

Use the Lite profile for CSV onboarding, trusted transformations, dashboards, and starter analytics.

## Included capabilities

- core platform services
- analytics and dashboard surfaces
- selected connector overlays only
- reporting extra by default

## Install

```bash
./scripts/install.sh --profile lite --connectors csv
```

This writes `ENABLED_CONNECTORS=csv` and `ENABLED_OPTIONAL_EXTRAS=reporting` into `.env` unless you override them.

## Optional override

```bash
./scripts/install.sh --profile lite --connectors csv --extras none
```

## Validate

```bash
./scripts/health.sh
python scripts/validate_compose_profiles.py
```

Lite is the best starting point for demos, local validation, or teams that want trusted reporting foundations before adding operational AI modules.
