# Ingestion Tests

Validates ingestion behavior and protects the repository against regressions.
It should evolve alongside the implementation under test so fixtures, sample artifacts, and API expectations remain aligned.

## Directory contents

- `test_csv_connector.py` — Contains automated tests for the ingestion workflows and behaviors.
- `test_easy_csv_api.py` — Contains automated tests for the ingestion workflows and behaviors.
- `test_easy_csv_workflow.py` — Contains automated tests for the ingestion workflows and behaviors.
- `test_mapper.py` — Contains automated tests for the ingestion workflows and behaviors.
- `test_platform_connectors.py` — Contains automated tests for the ingestion workflows and behaviors.
- `test_sources_api.py` — Contains automated tests for the ingestion workflows and behaviors.
- `test_validator.py` — Contains automated tests for the ingestion workflows and behaviors.

## Interfaces and data contracts

- Main types: this area is centered on functions, configuration, or documentation rather than exported classes.
- Key APIs and entry points: build_source, test_csv_connector_discovers_schema_and_extracts_rows, test_easy_csv_upload_and_preview, test_easy_csv_json_workflow, test_easy_csv_wizard_html_flow, test_mapper_detects_aliases_and_required_columns, test_woocommerce_connector_extracts_rows_with_mocked_request, test_adobe_connector_extracts_items_payload, test_bigcommerce_connector_extracts_data_payload, test_sources_api_can_register_test_and_import_csv, test_validator_detects_missing_and_duplicate_values.

## Operational notes

- Scope profile: test (7).
- Status profile: stable (7).
- Important dependencies: datetime, pathlib, core.ingestion.base.models, core.ingestion.base.raw_loader, core.ingestion.base.repository, core.ingestion.base.state_store, fastapi.testclient, core.api.main, core.ingestion.base.mapper, __future__, core.ingestion.base.validator.
- Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
- Compatibility: Python 3.11+ with pytest and repository test dependencies.
- Test guidance: keep fixtures, sample artifacts, and endpoint expectations aligned with the production modules under test.

## Related areas

- `core/` shared runtime services under test
- `modules/` business and platform modules exercised by these tests
- `data/` sample inputs and generated artifacts used during test runs
