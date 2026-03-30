# Ingestion Base Layer

Standardizes external-system interaction for the ingestion base workflow. Normalizes source fields and structures for ingestion base processing.
It underpins source registration, extraction, validation, mapping, and raw-loading workflows reused by connector modules.

## Directory contents

- `connector.py` — Implements adapter logic for the ingestion base integration surface.
- `api_connector.py` — Implements adapter logic for the ingestion base integration surface.
- `mapper.py` — Maps source structures used by the ingestion base workflow.
- `models.py` — Defines domain models for the ingestion base module.
- `raw_loader.py` — Provides implementation support for the ingestion base workflow.
- `registry.py` — Registers and resolves components for the ingestion base workflow.
- `repository.py` — Implements repository access patterns for the ingestion base layer.
- `state_store.py` — Provides implementation support for the ingestion base workflow.
- `validator.py` — Validates inputs and invariants for the ingestion base workflow.
- `__init__.py` — Defines the core.ingestion.base package surface and package-level exports.

## Interfaces and data contracts

- Main types: BaseApiConnector, BaseConnector, ColumnMapper, SourceType, SourceStatus, ColumnInfo, SourceCreateRequest, SourceRecord, TestConnectionResult, RawLoader, ConnectorRegistry, RepositoryProtocol.
- Key APIs and entry points: build_default_registry, now_utc.

## Operational notes

- Scope profile: internal (8), adapter (2).
- Status profile: stable (9), internal (1).
- Important dependencies: Standard library only, __future__, json, abc, typing, urllib.error, urllib.parse, core.ingestion.base.mapper, core.ingestion.base.models, core.ingestion.base.raw_loader, datetime, enum, pydantic, core.ingestion.base.repository.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. External-system assumptions must remain aligned with connector contracts and mapping rules. Internal interfaces should remain aligned with adjacent modules and repository conventions.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies. Python 3.11+ with repository configuration dependencies.
- Maintenance guidance: changes here can affect multiple modules, so update downstream tests and docs in the same change set.

## Related areas

- `modules/connector_*/` concrete source adapters built on this base layer
- `core/api/routes/sources.py` public source-management endpoints
- `data/` sample uploads and raw artifact roots
