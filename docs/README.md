# RetailOps Data & AI Platform

A modular self-hosted data and AI platform for retail operations.

## Repository Structure

- core/: shared platform capabilities
- modules/: optional business and pro modules
- compose/: docker compose stacks
- config/: environment and app configs
- tests/: test suites
- docs/: project documents
- scripts/: installation and utility scripts

## Development Stack

- Python 3.12
- uv
- Ruff
- MyPy
- pre-commit
- Docker

## Initial Goal

Build a modular monorepo where Core can run independently and optional modules can be added later.