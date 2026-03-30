# Release and Operations

This document summarizes how the modular repository is installed, upgraded, checked, backed up, and restored.

## Main operational entrypoints

- `scripts/install.sh` bootstrap dependencies and optionally start a profile
- `scripts/upgrade.sh` refresh the active profile
- `scripts/health.sh` run static repository and service checks
- `scripts/backup.sh` and `scripts/restore.sh` manage local backups
- `scripts/load_demo_data.sh` seed demo workflows for validation or demos

## Deployment profiles

- **Lite** for onboarding, transformations, dashboards, and starter analytics
- **Standard** for operational intelligence and monitoring
- **Pro** for platform extensions and advanced services

Operators should treat credentials, external services, and storage paths as environment-specific concerns layered on top of this source distribution.
