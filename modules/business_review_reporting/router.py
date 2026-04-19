# Project:      RetailOps Data & AI Platform
# Module:       modules.business_review_reporting
# File:         router.py
# Path:         modules/business_review_reporting/router.py
#
# Summary:      Defines API routes for the business review reporting module.
# Purpose:      Exposes HTTP endpoints for business review reporting capabilities.
# Scope:        public API
# Status:       stable
#
# Author(s):    Morteza Taleblou
# Website:      https://taleblou.ir/
# Repository:   https://github.com/taleblou/RetailOps-Data-AI-Platform
#
# License:      Apache License 2.0
# SPDX-License-Identifier: Apache-2.0
# Copyright:    (c) 2025 Morteza Taleblou
#
# Notes:
#   - Main types: None.
#   - Key APIs: router, get_catalog, get_executive_review, get_store_performance, get_category_review, get_sku_deep_dive, ...
#   - Dependencies: __future__, pathlib, typing, fastapi, working_capital_reporting_schemas, working_capital_reporting_service, ...
#   - Constraints: Public request and response behavior should remain backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from .commercial_reporting_schemas import (
    CustomerCohortRetentionReviewResponse,
    PromotionPricingEffectivenessReportResponse,
    ReturnsProfitLeakageReportResponse,
    SupplierProcurementPackResponse,
)
from .commercial_reporting_service import (
    get_customer_cohort_retention_review,
    get_promotion_pricing_effectiveness_report,
    get_returns_profit_leakage_report,
    get_supplier_procurement_pack,
)
from .decision_intelligence_schemas import (
    AlertToActionPlaybookReportResponse,
    BoardStylePdfPackResponse,
    CrossModuleDecisionIntelligenceReportResponse,
    PortfolioOpportunityMatrixReportResponse,
    ScenarioSimulationReportResponse,
)
from .decision_intelligence_service import (
    get_alert_to_action_playbook_report,
    get_board_style_pdf_pack,
    get_cross_module_decision_intelligence_report,
    get_portfolio_opportunity_matrix_report,
    get_scenario_simulation_report,
)
from .executive_scorecard_schemas import (
    CashConversionRiskReportResponse,
    CustomerJourneyFrictionReportResponse,
    DemandSupplyRiskMatrixReportResponse,
    InternalBenchmarkingReportResponse,
    MarkdownClearanceOptimizationReportResponse,
    OperatingExecutiveScorecardReportResponse,
)
from .executive_scorecard_service import (
    get_cash_conversion_risk_report,
    get_customer_journey_friction_report,
    get_demand_supply_risk_matrix_report,
    get_internal_benchmarking_report,
    get_markdown_clearance_optimization_report,
    get_operating_executive_scorecard,
)
from .governance_reporting_schemas import (
    AiGovernanceTrustReportResponse,
    AnomalyInvestigationReportResponse,
    DataQualityPipelineReliabilityReportResponse,
    FulfillmentControlTowerReportResponse,
)
from .governance_reporting_service import (
    get_ai_governance_trust_report,
    get_anomaly_investigation_report,
    get_data_quality_pipeline_reliability_report,
    get_fulfillment_control_tower_report,
)
from .portfolio_reporting_schemas import (
    AbcXyzInventoryPolicyReportResponse,
    AssortmentRationalizationReportResponse,
    BasketCrossSellOpportunityReportResponse,
    CustomerChurnRecoveryReportResponse,
    CustomerValueSegmentationReportResponse,
    PaymentRevenueAssuranceReportResponse,
    ProfitabilityMarginWaterfallReportResponse,
    SeasonalityCalendarReadinessReportResponse,
)
from .portfolio_reporting_service import (
    get_abc_xyz_inventory_policy_report,
    get_assortment_rationalization_report,
    get_basket_cross_sell_opportunity_report,
    get_customer_churn_recovery_report,
    get_customer_value_segmentation_report,
    get_payment_revenue_assurance_report,
    get_profitability_margin_waterfall_report,
    get_seasonality_calendar_readiness_report,
)
from .schemas import (
    BusinessReportCatalogResponse,
    CategoryMerchandisingReviewResponse,
    ExecutiveBusinessReviewResponse,
    SkuDeepDiveResponse,
    StorePerformancePackResponse,
)
from .service import (
    get_business_report_catalog,
    get_category_merchandising_review,
    get_executive_business_review,
    get_sku_deep_dive_report,
    get_store_performance_pack,
)
from .working_capital_reporting_schemas import (
    ForecastQualityReportResponse,
    InventoryInvestmentReportResponse,
    ReplenishmentDecisionReviewResponse,
    RevenueRootCauseReportResponse,
)
from .working_capital_reporting_service import (
    get_forecast_quality_report,
    get_inventory_investment_report,
    get_replenishment_decision_review,
    get_revenue_root_cause_report,
)

router = APIRouter(prefix="/api/v1/business-reports", tags=["business-reports"])


@router.get("/catalog", response_model=BusinessReportCatalogResponse)
async def get_catalog(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
) -> BusinessReportCatalogResponse:
    try:
        payload = get_business_report_catalog(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return BusinessReportCatalogResponse.model_validate(payload)


@router.get("/executive-review", response_model=ExecutiveBusinessReviewResponse)
async def get_executive_review(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
) -> ExecutiveBusinessReviewResponse:
    try:
        payload = get_executive_business_review(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExecutiveBusinessReviewResponse.model_validate(payload)


@router.get("/store-performance", response_model=StorePerformancePackResponse)
async def get_store_performance(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    group_by: Literal["store", "region"] = Query(default="store"),
    limit: int = Query(default=50, ge=1, le=500),
) -> StorePerformancePackResponse:
    try:
        payload = get_store_performance_pack(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            group_by=group_by,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return StorePerformancePackResponse.model_validate(payload)


@router.get("/category-merchandising", response_model=CategoryMerchandisingReviewResponse)
async def get_category_review(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> CategoryMerchandisingReviewResponse:
    try:
        payload = get_category_merchandising_review(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CategoryMerchandisingReviewResponse.model_validate(payload)


@router.get("/skus/{sku}/deep-dive", response_model=SkuDeepDiveResponse)
async def get_sku_deep_dive(
    sku: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
) -> SkuDeepDiveResponse:
    try:
        payload = get_sku_deep_dive_report(
            upload_id=upload_id,
            sku=sku,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SkuDeepDiveResponse.model_validate(payload)


@router.get("/inventory-investment", response_model=InventoryInvestmentReportResponse)
async def get_inventory_investment(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> InventoryInvestmentReportResponse:
    try:
        payload = get_inventory_investment_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return InventoryInvestmentReportResponse.model_validate(payload)


@router.get("/revenue-root-cause", response_model=RevenueRootCauseReportResponse)
async def get_revenue_root_cause(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    window_days: int = Query(default=30, ge=7, le=180),
) -> RevenueRootCauseReportResponse:
    try:
        payload = get_revenue_root_cause_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            window_days=window_days,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RevenueRootCauseReportResponse.model_validate(payload)


@router.get("/forecast-quality", response_model=ForecastQualityReportResponse)
async def get_forecast_quality(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> ForecastQualityReportResponse:
    try:
        payload = get_forecast_quality_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ForecastQualityReportResponse.model_validate(payload)


@router.get("/replenishment-review", response_model=ReplenishmentDecisionReviewResponse)
async def get_replenishment_review(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> ReplenishmentDecisionReviewResponse:
    try:
        payload = get_replenishment_decision_review(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ReplenishmentDecisionReviewResponse.model_validate(payload)


@router.get("/supplier-procurement-pack", response_model=SupplierProcurementPackResponse)
async def get_supplier_procurement_review(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> SupplierProcurementPackResponse:
    try:
        payload = get_supplier_procurement_pack(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SupplierProcurementPackResponse.model_validate(payload)


@router.get("/returns-profit-leakage", response_model=ReturnsProfitLeakageReportResponse)
async def get_returns_profit_leakage(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> ReturnsProfitLeakageReportResponse:
    try:
        payload = get_returns_profit_leakage_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ReturnsProfitLeakageReportResponse.model_validate(payload)


@router.get(
    "/promotion-pricing-effectiveness",
    response_model=PromotionPricingEffectivenessReportResponse,
)
async def get_promotion_pricing_effectiveness(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> PromotionPricingEffectivenessReportResponse:
    try:
        payload = get_promotion_pricing_effectiveness_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PromotionPricingEffectivenessReportResponse.model_validate(payload)


@router.get(
    "/customer-cohort-retention",
    response_model=CustomerCohortRetentionReviewResponse,
)
async def get_customer_cohort_retention(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> CustomerCohortRetentionReviewResponse:
    try:
        payload = get_customer_cohort_retention_review(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CustomerCohortRetentionReviewResponse.model_validate(payload)


@router.get(
    "/anomaly-investigation",
    response_model=AnomalyInvestigationReportResponse,
)
async def get_anomaly_investigation(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> AnomalyInvestigationReportResponse:
    try:
        payload = get_anomaly_investigation_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AnomalyInvestigationReportResponse.model_validate(payload)


@router.get(
    "/fulfillment-control-tower",
    response_model=FulfillmentControlTowerReportResponse,
)
async def get_fulfillment_control_tower(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> FulfillmentControlTowerReportResponse:
    try:
        payload = get_fulfillment_control_tower_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FulfillmentControlTowerReportResponse.model_validate(payload)


@router.get(
    "/ai-governance-trust",
    response_model=AiGovernanceTrustReportResponse,
)
async def get_ai_governance_trust(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=200),
) -> AiGovernanceTrustReportResponse:
    try:
        payload = get_ai_governance_trust_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AiGovernanceTrustReportResponse.model_validate(payload)


@router.get(
    "/data-quality-pipeline-reliability",
    response_model=DataQualityPipelineReliabilityReportResponse,
)
async def get_data_quality_pipeline_reliability(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=200),
) -> DataQualityPipelineReliabilityReportResponse:
    try:
        payload = get_data_quality_pipeline_reliability_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DataQualityPipelineReliabilityReportResponse.model_validate(payload)


@router.get(
    "/scenario-simulation",
    response_model=ScenarioSimulationReportResponse,
)
async def get_scenario_simulation(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
) -> ScenarioSimulationReportResponse:
    try:
        payload = get_scenario_simulation_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ScenarioSimulationReportResponse.model_validate(payload)


@router.get(
    "/alert-to-action-playbook",
    response_model=AlertToActionPlaybookReportResponse,
)
async def get_alert_to_action_playbook(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=200),
) -> AlertToActionPlaybookReportResponse:
    try:
        payload = get_alert_to_action_playbook_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AlertToActionPlaybookReportResponse.model_validate(payload)


@router.get(
    "/cross-module-decision-intelligence",
    response_model=CrossModuleDecisionIntelligenceReportResponse,
)
async def get_cross_module_decision_intelligence(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=25, ge=1, le=300),
) -> CrossModuleDecisionIntelligenceReportResponse:
    try:
        payload = get_cross_module_decision_intelligence_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CrossModuleDecisionIntelligenceReportResponse.model_validate(payload)


@router.get(
    "/portfolio-opportunity-matrix",
    response_model=PortfolioOpportunityMatrixReportResponse,
)
async def get_portfolio_opportunity_matrix(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=12, ge=1, le=200),
) -> PortfolioOpportunityMatrixReportResponse:
    try:
        payload = get_portfolio_opportunity_matrix_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PortfolioOpportunityMatrixReportResponse.model_validate(payload)


@router.get(
    "/board-pack",
    response_model=BoardStylePdfPackResponse,
)
async def get_board_pack(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
) -> BoardStylePdfPackResponse:
    try:
        payload = get_board_style_pdf_pack(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return BoardStylePdfPackResponse.model_validate(payload)


@router.get(
    "/profitability-margin-waterfall",
    response_model=ProfitabilityMarginWaterfallReportResponse,
)
async def get_profitability_margin_waterfall(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=12, ge=1, le=200),
) -> ProfitabilityMarginWaterfallReportResponse:
    try:
        payload = get_profitability_margin_waterfall_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ProfitabilityMarginWaterfallReportResponse.model_validate(payload)


@router.get(
    "/abc-xyz-inventory-policy",
    response_model=AbcXyzInventoryPolicyReportResponse,
)
async def get_abc_xyz_inventory_policy(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=12, ge=1, le=200),
) -> AbcXyzInventoryPolicyReportResponse:
    try:
        payload = get_abc_xyz_inventory_policy_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AbcXyzInventoryPolicyReportResponse.model_validate(payload)


@router.get(
    "/basket-cross-sell-opportunities",
    response_model=BasketCrossSellOpportunityReportResponse,
)
async def get_basket_cross_sell_opportunities(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=12, ge=1, le=200),
) -> BasketCrossSellOpportunityReportResponse:
    try:
        payload = get_basket_cross_sell_opportunity_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return BasketCrossSellOpportunityReportResponse.model_validate(payload)


@router.get(
    "/customer-churn-recovery",
    response_model=CustomerChurnRecoveryReportResponse,
)
async def get_customer_churn_recovery(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=15, ge=1, le=200),
) -> CustomerChurnRecoveryReportResponse:
    try:
        payload = get_customer_churn_recovery_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CustomerChurnRecoveryReportResponse.model_validate(payload)


@router.get(
    "/payment-revenue-assurance",
    response_model=PaymentRevenueAssuranceReportResponse,
)
async def get_payment_revenue_assurance(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=15, ge=1, le=200),
) -> PaymentRevenueAssuranceReportResponse:
    try:
        payload = get_payment_revenue_assurance_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PaymentRevenueAssuranceReportResponse.model_validate(payload)


@router.get(
    "/seasonality-calendar-readiness",
    response_model=SeasonalityCalendarReadinessReportResponse,
)
async def get_seasonality_calendar_readiness(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=12, ge=1, le=200),
) -> SeasonalityCalendarReadinessReportResponse:
    try:
        payload = get_seasonality_calendar_readiness_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SeasonalityCalendarReadinessReportResponse.model_validate(payload)


@router.get(
    "/assortment-rationalization",
    response_model=AssortmentRationalizationReportResponse,
)
async def get_assortment_rationalization(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=15, ge=1, le=200),
) -> AssortmentRationalizationReportResponse:
    try:
        payload = get_assortment_rationalization_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AssortmentRationalizationReportResponse.model_validate(payload)


@router.get(
    "/customer-value-segmentation",
    response_model=CustomerValueSegmentationReportResponse,
)
async def get_customer_value_segmentation(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=15, ge=1, le=200),
) -> CustomerValueSegmentationReportResponse:
    try:
        payload = get_customer_value_segmentation_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CustomerValueSegmentationReportResponse.model_validate(payload)


@router.get(
    "/operating-executive-scorecard",
    response_model=OperatingExecutiveScorecardReportResponse,
)
async def get_operating_scorecard(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
) -> OperatingExecutiveScorecardReportResponse:
    try:
        payload = get_operating_executive_scorecard(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return OperatingExecutiveScorecardReportResponse.model_validate(payload)


@router.get(
    "/internal-benchmarking",
    response_model=InternalBenchmarkingReportResponse,
)
async def get_internal_benchmarking(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=10, ge=1, le=200),
) -> InternalBenchmarkingReportResponse:
    try:
        payload = get_internal_benchmarking_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return InternalBenchmarkingReportResponse.model_validate(payload)


@router.get(
    "/markdown-clearance-optimization",
    response_model=MarkdownClearanceOptimizationReportResponse,
)
async def get_markdown_clearance_optimization(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=12, ge=1, le=200),
) -> MarkdownClearanceOptimizationReportResponse:
    try:
        payload = get_markdown_clearance_optimization_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return MarkdownClearanceOptimizationReportResponse.model_validate(payload)


@router.get(
    "/demand-supply-risk-matrix",
    response_model=DemandSupplyRiskMatrixReportResponse,
)
async def get_demand_supply_risk_matrix(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=15, ge=1, le=200),
) -> DemandSupplyRiskMatrixReportResponse:
    try:
        payload = get_demand_supply_risk_matrix_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DemandSupplyRiskMatrixReportResponse.model_validate(payload)


@router.get(
    "/customer-journey-friction",
    response_model=CustomerJourneyFrictionReportResponse,
)
async def get_customer_journey_friction(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=15, ge=1, le=200),
) -> CustomerJourneyFrictionReportResponse:
    try:
        payload = get_customer_journey_friction_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CustomerJourneyFrictionReportResponse.model_validate(payload)


@router.get(
    "/cash-conversion-risk",
    response_model=CashConversionRiskReportResponse,
)
async def get_cash_conversion_risk(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/business_review_reporting"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=300),
) -> CashConversionRiskReportResponse:
    try:
        payload = get_cash_conversion_risk_report(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return CashConversionRiskReportResponse.model_validate(payload)
