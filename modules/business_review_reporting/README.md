# Business Review Reporting Module

Exposes HTTP endpoints for business review reporting capabilities. Encapsulates core processing and artifact generation for business review reporting workflows.
It follows the repository module pattern of service logic, API surface, schemas, optional runtime entry points, and deployment assets when those concerns are applicable.

## Directory contents

- `router.py` — Defines API routes for the business review reporting module.
- `service.py` — Implements the business review reporting service layer and business logic.
- `schemas.py` — Defines schemas for the business review reporting data contracts.
- `commercial_reporting_schemas.py` — Provides implementation support for the business review reporting workflow.
- `commercial_reporting_service.py` — Provides implementation support for the business review reporting workflow.
- `decision_intelligence_schemas.py` — Provides implementation support for the business review reporting workflow.
- `decision_intelligence_service.py` — Provides implementation support for the business review reporting workflow.
- `executive_scorecard_schemas.py` — Provides implementation support for the business review reporting workflow.
- `executive_scorecard_service.py` — Provides implementation support for the business review reporting workflow.
- `governance_reporting_schemas.py` — Provides implementation support for the business review reporting workflow.
- `governance_reporting_service.py` — Provides implementation support for the business review reporting workflow.
- `portfolio_reporting_schemas.py` — Provides implementation support for the business review reporting workflow.
- `portfolio_reporting_service.py` — Provides implementation support for the business review reporting workflow.
- `working_capital_reporting_schemas.py` — Provides implementation support for the business review reporting workflow.
- `working_capital_reporting_service.py` — Provides implementation support for the business review reporting workflow.
- `__init__.py` — Defines the modules.business_review_reporting package surface and package-level exports.

## Interfaces and data contracts

- Main types: SupplierProcurementPackRowResponse, SupplierProcurementPackSummaryResponse, SupplierProcurementPackResponse, ReturnsLeakageWaterfallResponse, ReturnsProfitLeakageCategoryResponse, ReturnsProfitLeakageSummaryResponse, ScenarioSimulationRowResponse, ScenarioFocusSkuResponse, ScenarioSimulationSummaryResponse, ScenarioSimulationReportResponse, PlaybookLaneResponse, AlertActionResponse.
- Key APIs and entry points: get_supplier_procurement_pack, get_returns_profit_leakage_report, get_promotion_pricing_effectiveness_report, get_customer_cohort_retention_review, build_scenario_simulation_report, build_alert_to_action_playbook_report, build_cross_module_decision_intelligence_report, build_portfolio_opportunity_matrix_report, build_board_style_pdf_pack, get_scenario_simulation_report, list_executive_scorecard_reports, get_operating_executive_scorecard.

## Operational notes

- Scope profile: internal (15), public API (1).
- Status profile: stable (15), internal (1).
- Important dependencies: __future__, router, pydantic, collections, datetime, pathlib, typing, modules.common.upload_utils, statistics, pypdf, modules.abc_xyz_intelligence.service, csv, fastapi, working_capital_reporting_schemas.
- Constraints: Package exports should stay lightweight and avoid introducing import cycles. Internal interfaces should remain aligned with adjacent modules and repository conventions. File-system paths and serialized artifact formats must remain stable for downstream consumers.
- Compatibility: Python 3.11+ and repository-supported runtime dependencies. Python 3.11+ with repository configuration dependencies.
- Maintenance guidance: keep routers, schemas, services, artifacts, and README examples synchronized when this module evolves.

## Related areas

- `tests/business_review_reporting/` automated checks for this module when present
- `modules/common/` shared parsing and upload utilities
- `docs/` long-form capability and architecture references
