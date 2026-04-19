# Project:      RetailOps Data & AI Platform
# Module:       core.api.routes
# File:         pro_platform.py
# Path:         core/api/routes/pro_platform.py
#
# Summary:      Exposes summary, readiness, and deployment-plan endpoints
#               for the Pro platform extension stack.
# Purpose:      Gives operators a single API surface for generating,
#               validating, and planning Pro deployment bundles.
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

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from fastapi import APIRouter, HTTPException, Query

ArtifactBuilder = Callable[[Path, bool], dict[str, Any]]
DeploymentPlanner = Callable[..., dict[str, Any]]


_schema_module = cast(Any, import_module("core.api.schemas.pro_platform"))
ProPlatformSummaryResponse = cast(Any, _schema_module.ProPlatformSummaryResponse)
ProPlatformModuleReadinessResponse = cast(
    Any,
    getattr(_schema_module, "ProPlatformModuleReadinessResponse", ProPlatformSummaryResponse),
)
ProPlatformReadinessResponse = cast(
    Any,
    getattr(_schema_module, "ProPlatformReadinessResponse", ProPlatformSummaryResponse),
)
ProPlatformDeploymentPlanResponse = cast(
    Any,
    getattr(_schema_module, "ProPlatformDeploymentPlanResponse", ProPlatformSummaryResponse),
)

build_platform_deployment_plan = cast(
    DeploymentPlanner,
    cast(Any, import_module("modules.common.platform_extensions")).build_platform_deployment_plan,
)


def _resolve_artifact_builder(module_path: str, builder_name: str) -> ArtifactBuilder:
    module = cast(Any, import_module(module_path))
    candidate = getattr(module, builder_name, None)
    if not callable(candidate):
        raise RuntimeError(f"Expected callable '{builder_name}' in module '{module_path}'.")
    return cast(ArtifactBuilder, candidate)


build_cdc_artifact = _resolve_artifact_builder("modules.cdc.service", "build_cdc_artifact")
build_streaming_artifact = _resolve_artifact_builder(
    "modules.streaming.service",
    "build_streaming_artifact",
)
build_lakehouse_artifact = _resolve_artifact_builder(
    "modules.lakehouse.service",
    "build_lakehouse_artifact",
)
build_query_layer_artifact = _resolve_artifact_builder(
    "modules.query_layer.service",
    "build_query_layer_artifact",
)
build_metadata_artifact = _resolve_artifact_builder(
    "modules.metadata.service",
    "build_metadata_artifact",
)
build_feature_store_artifact = _resolve_artifact_builder(
    "modules.feature_store.service",
    "build_feature_store_artifact",
)
build_advanced_serving_artifact = _resolve_artifact_builder(
    "modules.advanced_serving.service",
    "build_advanced_serving_artifact",
)

router = APIRouter(prefix="/api/v1/pro-platform", tags=["pro-platform"])


def _build_modules(base_dir: Path, refresh: bool) -> dict[str, dict[str, Any]]:
    return {
        "cdc": build_cdc_artifact(base_dir / "cdc", refresh),
        "streaming": build_streaming_artifact(base_dir / "streaming", refresh),
        "lakehouse": build_lakehouse_artifact(base_dir / "lakehouse", refresh),
        "query_layer": build_query_layer_artifact(base_dir / "query_layer", refresh),
        "metadata": build_metadata_artifact(base_dir / "metadata", refresh),
        "feature_store": build_feature_store_artifact(base_dir / "feature_store", refresh),
        "advanced_serving": build_advanced_serving_artifact(
            base_dir / "advanced_serving",
            refresh,
        ),
    }


@router.get("/summary", response_model=ProPlatformSummaryResponse)
async def get_platform_extensions_summary(
    artifact_dir: str = Query(default="data/artifacts/pro_platform"),
    refresh: bool = Query(default=False),
) -> Any:
    try:
        base_dir = Path(artifact_dir)
        modules = _build_modules(base_dir, refresh)
        deployment_ready_count = sum(
            1 for payload in modules.values() if payload.get("status") == "deployment_ready"
        )
        payload = {
            "platform_surface": "extensions",
            "platform_name": "RetailOps Pro Data Platform",
            "modules": modules,
            "module_count": len(modules),
            "deployment_ready_count": deployment_ready_count,
            "artifact_root": str(base_dir.resolve()),
        }
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ProPlatformSummaryResponse.model_validate(payload)


@router.get("/readiness", response_model=ProPlatformReadinessResponse)
async def get_platform_extensions_readiness(
    artifact_dir: str = Query(default="data/artifacts/pro_platform"),
    refresh: bool = Query(default=False),
) -> Any:
    try:
        base_dir = Path(artifact_dir)
        modules = _build_modules(base_dir, refresh)
        readiness_modules = [
            ProPlatformModuleReadinessResponse.model_validate(
                {
                    "module_name": payload.get("module_name", module_name),
                    "status": payload.get("status", "needs_attention"),
                    "readiness_checks": payload.get("readiness_checks", {}),
                    "generated_files": payload.get("generated_files", {}),
                }
            )
            for module_name, payload in modules.items()
        ]
        deployment_ready_count = sum(
            1 for payload in modules.values() if payload.get("status") == "deployment_ready"
        )
        payload = {
            "platform_surface": "extensions",
            "platform_name": "RetailOps Pro Data Platform",
            "module_count": len(readiness_modules),
            "deployment_ready_count": deployment_ready_count,
            "artifact_root": str(base_dir.resolve()),
            "modules": readiness_modules,
        }
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ProPlatformReadinessResponse.model_validate(payload)


@router.get("/deployment-plan", response_model=ProPlatformDeploymentPlanResponse)
async def get_platform_extensions_deployment_plan(
    artifact_dir: str = Query(default="data/artifacts/pro_platform"),
    refresh: bool = Query(default=False),
) -> Any:
    try:
        base_dir = Path(artifact_dir)
        modules = _build_modules(base_dir, refresh)
        repo_root = Path(__file__).resolve().parents[3]
        payload = build_platform_deployment_plan(
            modules=modules,
            artifact_root=base_dir,
            repo_root=repo_root,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ProPlatformDeploymentPlanResponse.model_validate(payload)
