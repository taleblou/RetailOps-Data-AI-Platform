# Business Tests

Validates business behavior and protects the repository against regressions.
It should evolve alongside the implementation under test so fixtures, sample artifacts, and API expectations remain aligned.

## Directory contents

- `test_additional_business_modules.py` — Contains automated tests for the business workflows and behaviors.
- `test_business_review_reports.py` — Contains automated tests for the business workflows and behaviors.
- `test_commercial_reporting.py` — Contains automated tests for the business workflows and behaviors.
- `test_customer_and_inventory_modules.py` — Contains automated tests for the business workflows and behaviors.
- `test_decision_intelligence_reporting.py` — Contains automated tests for the business workflows and behaviors.
- `test_executive_scorecards.py` — Contains automated tests for the business workflows and behaviors.
- `test_governance_reporting.py` — Contains automated tests for the business workflows and behaviors.
- `test_margin_and_assortment_modules.py` — Contains automated tests for the business workflows and behaviors.
- `test_portfolio_reporting.py` — Contains automated tests for the business workflows and behaviors.
- `test_risk_and_retention_modules.py` — Contains automated tests for the business workflows and behaviors.
- `test_working_capital_reporting.py` — Contains automated tests for the business workflows and behaviors.

## Interfaces and data contracts

- Main types: this area is centered on functions, configuration, or documentation rather than exported classes.
- Key APIs and entry points: test_additional_business_module_routes_return_artifacts, test_business_review_report_endpoints_return_expected_payloads, test_business_review_sku_deep_dive_surfaces_risk_flags, test_commercial_reporting_catalog_includes_new_reports, test_commercial_reporting_supplier_and_returns_reports, test_commercial_reporting_promotion_and_cohort_reports, test_customer_and_inventory_modules_return_expected_payloads, test_customer_inventory_detail_routes_work, test_decision_intelligence_catalog_includes_remaining_and_bonus_reports, test_decision_intelligence_scenario_and_board_pack_reports, test_decision_intelligence_playbook_decision_and_portfolio_reports, test_executive_scorecards_catalog_includes_new_reports.

## Operational notes

- Scope profile: test (11).
- Status profile: stable (11).
- Important dependencies: __future__, json, pathlib, fastapi.testclient, core.api.main, core.ingestion.base.repository, tests.business.test_portfolio_reporting.
- Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
- Compatibility: Python 3.11+ with pytest and repository test dependencies.
- Test guidance: keep fixtures, sample artifacts, and endpoint expectations aligned with the production modules under test.

## Related areas

- `core/` shared runtime services under test
- `modules/` business and platform modules exercised by these tests
- `data/` sample inputs and generated artifacts used during test runs
