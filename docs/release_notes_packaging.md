# Release Notes and Packaging

This note summarizes packaging expectations for the modular repository.

## Included in a clean source package

- code under `core/`, `modules/`, `config/`, `scripts/`, and `tests/`
- profile quickstarts and architecture documentation
- compose overlays and package workspaces
- demo data and reproducible sample assets

## Excluded from a clean source package

- local secrets and environment-specific `.env` files
- `__pycache__`, `.pytest_cache`, and compiled Python artifacts
- transient runtime outputs that should be regenerated after installation

The goal is a repository bundle that is structurally complete for development and evaluation while remaining clean and portable.
