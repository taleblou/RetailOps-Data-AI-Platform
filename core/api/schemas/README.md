# API Schemas

Supports the API schemas layer inside the modular repository architecture. Marks core.api.schemas as a Python package and centralizes its package-level imports.
It sits on the public API boundary and should remain aligned with request, response, and router contracts used across the platform.

## Directory contents

- `easy_csv.py` — Provides implementation support for the API schemas workflow.
- `pro_platform.py` — Provides implementation support for the API schemas workflow.
- `setup.py` — Provides implementation support for the API schemas workflow.
- `__init__.py` — Defines the core.api.schemas package surface and package-level exports.

## Interfaces and data contracts

- Main types: EasyCsvPreviewResponse, EasyCsvMappingRequest, EasyCsvMappingResponse, EasyCsvValidationIssue, EasyCsvValidationResponse, EasyCsvImportResponse, ProPlatformSummaryResponse, SetupLogEntry, SetupStepState, SetupSessionResponse, SetupSessionCreateRequest, SetupStoreRequest.
- Key APIs and entry points: no file-level callable surface is documented here.

## Operational notes

- Scope profile: internal (4).
- Status profile: stable (3), internal (1).
- Important dependencies: __future__, typing, pydantic.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. Internal interfaces should remain aligned with adjacent modules and repository conventions.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies. Python 3.11+ with repository configuration dependencies.
- Maintenance guidance: changes here can affect multiple modules, so update downstream tests and docs in the same change set.

## Related areas

- `core/api/routes/` HTTP handlers
- `core/api/schemas/` request and response contracts
- `core/serving/` shared serving orchestration reused by API routes
