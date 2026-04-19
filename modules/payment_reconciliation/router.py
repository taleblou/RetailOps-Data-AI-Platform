# Project:      RetailOps Data & AI Platform
# Module:       modules.payment_reconciliation
# File:         router.py
# Path:         modules/payment_reconciliation/router.py
#
# Summary:      Defines API routes for the payment reconciliation module.
# Purpose:      Exposes HTTP endpoints for payment reconciliation capabilities.
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
#   - Key APIs: router, get_payment_summary, get_payment_order
#   - Dependencies: __future__, pathlib, fastapi, schemas, service
#   - Constraints: Public request and response behavior should remain backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from .schemas import PaymentOrderResponse, PaymentReconciliationArtifactResponse
from .service import get_payment_reconciliation_artifact, get_payment_reconciliation_order

router = APIRouter(prefix="/api/v1/payment-reconciliation", tags=["payment-reconciliation"])


@router.get("/summary", response_model=PaymentReconciliationArtifactResponse)
async def get_payment_summary(
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/payment_reconciliation"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=500),
) -> PaymentReconciliationArtifactResponse:
    try:
        payload = get_payment_reconciliation_artifact(
            upload_id=upload_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
            limit=limit,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PaymentReconciliationArtifactResponse.model_validate(payload)


@router.get("/orders/{order_id}", response_model=PaymentOrderResponse)
async def get_payment_order(
    order_id: str,
    upload_id: str = Query(...),
    uploads_dir: str = Query(default="data/uploads"),
    artifact_dir: str = Query(default="data/artifacts/payment_reconciliation"),
    refresh: bool = Query(default=False),
) -> PaymentOrderResponse:
    try:
        payload = get_payment_reconciliation_order(
            upload_id=upload_id,
            order_id=order_id,
            uploads_dir=Path(uploads_dir),
            artifact_dir=Path(artifact_dir),
            refresh=refresh,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PaymentOrderResponse.model_validate(payload)
