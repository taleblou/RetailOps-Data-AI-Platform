# Feature store module

This module implements the phase 20 feature-store layer and keeps it optional relative to the phase 9 PostgreSQL-first feature tables.

## What is included

- a read-only FastAPI blueprint surface in `router.py`
- feature-store artifact generation in `service.py`
- typed models in `schemas.py`
- a Feast repository starter in `repo/feature_store.yaml`
- example feature definitions in `repo/feature_views.py`
- a `Dockerfile` for standalone packaging

## What it delivers

- offline and online store planning
- entity and feature-view definitions
- materialization schedule guidance
- integration points back to forecasting, shipment risk, stockout, and returns features

## Design boundary

The core platform does not require Feast. This module exists for teams that want to extend the platform into a broader online-serving and feature-management workflow.
