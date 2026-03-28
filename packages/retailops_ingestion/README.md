# retailops_ingestion

This package wrapper is reserved for connector and ingestion capabilities.

## Intended scope

It can later host the base connector framework, source-specific adapters, raw-load helpers, and sync-state utilities that currently live under `core/ingestion/` and the connector modules.

## Why it exists now

Keeping the wrapper in place makes the monorepo package-ready from early phases, even while the implementation is still developed in the main repository tree.
