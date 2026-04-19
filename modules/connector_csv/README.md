# CSV Connector

Supports the connector csv layer inside the modular repository architecture. Standardizes external-system interaction for the connector csv workflow.
It follows the repository module pattern of service logic, API surface, schemas, optional runtime entry points, and deployment assets when those concerns are applicable.

## Directory contents

- `main.py` — Provides implementation support for the connector csv workflow.
- `connector.py` — Implements adapter logic for the connector csv integration surface.
- `schemas.py` — Defines schemas for the connector csv data contracts.
- `__init__.py` — Defines the modules.connector_csv package surface and package-level exports.
- `Dockerfile` — Container build definition for this component.

## Interfaces and data contracts

- Main types: CsvConnector, CsvConnectorConfig.
- Key APIs and entry points: main.

## Operational notes

- Scope profile: internal (3), adapter (1).
- Status profile: stable (3), internal (1).
- Important dependencies: Standard library only, __future__, csv, pathlib, typing, core.ingestion.base.connector, core.ingestion.base.models, time, pydantic.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. External-system assumptions must remain aligned with connector contracts and mapping rules. Internal interfaces should remain aligned with adjacent modules and repository conventions.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies. Python 3.11+ with repository configuration dependencies.
- Maintenance guidance: keep routers, schemas, services, artifacts, and README examples synchronized when this module evolves.

## Related areas

- `tests/connector_csv/` automated checks for this module when present
- `modules/common/` shared parsing and upload utilities
- `docs/` long-form capability and architecture references
