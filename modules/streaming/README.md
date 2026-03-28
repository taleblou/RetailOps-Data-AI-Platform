# Streaming module

This module implements the phase 20 streaming surface for Redpanda-compatible event transport.

## Included assets

- `service.py`, `router.py`, and `schemas.py` for streaming blueprints
- `config/topics.yaml` for topic planning
- `config/processors.yaml` for stream-processor definitions
- `Dockerfile` and `main.py` for standalone module packaging

## What the module delivers

- topic definitions for CDC and downstream consumers
- consumer-group planning
- starter processor descriptions for event enrichment and routing
- artifact generation for the Pro platform summary

## Operational note

The module is intentionally blueprint-oriented. It keeps the repository structurally complete while leaving final broker sizing, retention, and deployment policy to the target environment.
