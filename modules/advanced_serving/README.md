# Advanced serving module

This module implements the phase 20 advanced-serving surface for teams that want a separate model runtime beyond the core FastAPI app.

## Scope in this repository

The repository provides the structural assets needed to start an advanced serving track without making BentoML a hard dependency of the core product.

Included assets:

- `service.py` for blueprint generation
- `router.py` and `schemas.py` for the read-only API surface
- `bentofile.yaml` for the Bento build definition
- `bentoml/service.py` for a starter runtime service
- `Dockerfile` for module-local containerization

## What the blueprint returns

- candidate runtime services such as forecasting and shipment-risk runtimes
- primary and shadow deployment modes
- model-alias usage for champion and challenger flows
- file references for the Bento service template

## Boundary

This module is a practical starter layer. It does not claim to ship a production-tuned multi-model runtime for every customer. It gives the project a complete and extendable phase 20 structure.
