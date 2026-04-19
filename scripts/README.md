# Scripts

The `scripts/` directory contains operator-facing helpers for installing, upgrading, validating, and operating the platform.

## Main scripts

- `install.sh` bootstraps a profile, writes `.env` values, installs Python dependencies, and starts the selected compose overlays
- `upgrade.sh` refreshes dependencies, applies migrations when available, and restarts the selected profile
- `health.sh` runs repository-level runtime checks
- `backup.sh` and `restore.sh` manage backups
- `load_demo_data.sh` seeds demo inputs for walkthroughs and smoke tests
- `generate_dashboard_workspace.py` creates dashboard workspace artifacts
- `generate_pro_platform_bundle.py` builds Pro extension bundles
- `validate_compose_profiles.py` validates overlay structure, Dockerfile references, and profile samples
- `common.sh` contains the shared shell helpers and profile-resolution logic

## Modular install behavior

`install.sh` and `upgrade.sh` now support both connector selection and optional extra selection.

Examples:

```bash
./scripts/install.sh --profile lite --connectors csv
./scripts/install.sh --profile standard --connectors csv,database,shopify --extras reporting
./scripts/install.sh --profile pro --connectors woocommerce --extras reporting,feature-store,advanced-serving
./scripts/install.sh --list-connectors
./scripts/install.sh --list-extras
```

Profile defaults are applied when `--connectors` or `--extras` are not provided.

## Maintenance rules

- Keep shell helpers idempotent where practical.
- Keep script flags aligned with README, quickstart docs, and config samples.
- Reuse module services instead of duplicating business logic inside script helpers.
