# Phase 18 setup wizard

This folder contains the onboarding layer that turns the platform from a developer-oriented repository into a guided product install.

## What this area covers

The setup flow matches the roadmap steps from the PDF:

1. create the store profile
2. choose the first data source
3. test the connection or upload path
4. map source fields to the canonical model
5. run the first import
6. trigger the first dbt transformation run
7. enable business modules
8. launch the first model training and scoring steps
9. publish dashboards and return a completion manifest

## Main runtime files

- `service.py` builds and updates the setup manifest
- `router.py` exposes the stateful API used by the wizard UI
- `schemas.py` defines typed request and response models
- `manifest.py` holds the persisted setup-state structure

## Artifact output

Setup progress is written under `data/artifacts/setup/` so installs can be retried safely and inspected later.

## Notes

This implementation is intentionally lightweight and file-based. It is enough for a hosted-self package, while leaving room for a future database-backed orchestration layer.
