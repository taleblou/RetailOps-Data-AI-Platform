# Project:      RetailOps Data & AI Platform
# Module:       core.api.routes
# File:         sources.py
# Path:         core/api/routes/sources.py
#
# Summary:      Defines public API routes and request handling for the API routes surface.
# Purpose:      Exposes HTTP entry points for API routes workflows.
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
#   - Key APIs: router, create_source, test_source, import_source,
#     get_source_status, get_source_errors, ...
#   - Dependencies: __future__, typing, fastapi,
#     core.ingestion.base.connector, core.ingestion.base.models,
#     core.ingestion.base.raw_loader, ...
#   - Constraints: Public request and response behavior should remain
#     backward compatible with documented API flows.
#   - Compatibility: Python 3.11+ with FastAPI-compatible runtime dependencies.

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from core.ingestion.base.connector import BaseConnector
from core.ingestion.base.models import (
    ImportRequest,
    ImportResult,
    SourceCreateRequest,
    SourceErrorRecord,
    SourceRecord,
    SourceStatus,
    SourceStatusResponse,
    TestConnectionResult,
)
from core.ingestion.base.raw_loader import RawLoader
from core.ingestion.base.registry import ConnectorRegistry
from core.ingestion.base.repository import RepositoryProtocol
from core.ingestion.base.state_store import StateStore

router = APIRouter(prefix="/sources", tags=["sources"])


def _repository(request: Request) -> RepositoryProtocol:
    return request.app.state.repository


def _state_store(request: Request) -> StateStore:
    return request.app.state.state_store


def _raw_loader(request: Request) -> RawLoader:
    return request.app.state.raw_loader


def _registry(request: Request) -> ConnectorRegistry:
    return request.app.state.registry


RepositoryDep = Annotated[RepositoryProtocol, Depends(_repository)]
StateStoreDep = Annotated[StateStore, Depends(_state_store)]
RawLoaderDep = Annotated[RawLoader, Depends(_raw_loader)]
RegistryDep = Annotated[ConnectorRegistry, Depends(_registry)]


def _build_connector(
    source_id: int,
    repository: RepositoryProtocol,
    state_store: StateStore,
    raw_loader: RawLoader,
    registry: ConnectorRegistry,
) -> tuple[SourceRecord, BaseConnector]:
    source = repository.get_source(source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found.",
        )
    return source, registry.create(source, state_store, raw_loader)


@router.post("", response_model=SourceRecord, status_code=status.HTTP_201_CREATED)
def create_source(
    request: SourceCreateRequest,
    repository: RepositoryDep,
) -> SourceRecord:
    return repository.create_source(request)


@router.post("/{source_id}/test", response_model=TestConnectionResult)
def test_source(
    source_id: int,
    repository: RepositoryDep,
    state_store: StateStoreDep,
    raw_loader: RawLoaderDep,
    registry: RegistryDep,
) -> TestConnectionResult:
    source, connector = _build_connector(
        source_id,
        repository,
        state_store,
        raw_loader,
        registry,
    )
    result = connector.test_connection()
    new_status = SourceStatus.TESTED if result.ok else SourceStatus.FAILED
    repository.update_source_status(source.source_id, new_status)
    if not result.ok:
        repository.record_error(source.source_id, "connection_test", result.message)
    return result


@router.post("/{source_id}/import", response_model=ImportResult)
def import_source(
    source_id: int,
    request: ImportRequest,
    repository: RepositoryDep,
    state_store: StateStoreDep,
    raw_loader: RawLoaderDep,
    registry: RegistryDep,
) -> ImportResult:
    source, connector = _build_connector(
        source_id,
        repository,
        state_store,
        raw_loader,
        registry,
    )
    repository.update_source_status(source.source_id, SourceStatus.RUNNING)
    import_job_id = repository.create_import_job(
        source.source_id,
        source.name,
        source.type,
    )
    sync_run_id = repository.create_sync_run(
        source.name,
        request.cursor,
        request.sync_mode,
    )

    try:
        result = connector.run_import(
            import_job_id=import_job_id,
            sync_run_id=sync_run_id,
            explicit_mapping=request.mapping,
            required_columns=request.required_columns,
            type_hints=request.type_hints,
            unique_key_columns=request.unique_key_columns,
            cursor=request.cursor,
            limit=request.limit,
        )
    except Exception as exc:
        message = str(exc)
        repository.update_source_status(source.source_id, SourceStatus.FAILED)
        repository.finish_import_job(import_job_id, "failed", 0, 0, message)
        repository.finish_sync_run(sync_run_id, "failed", 0, request.cursor, message)
        repository.record_error(source.source_id, "import", message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from exc

    repository.update_source_status(source.source_id, SourceStatus.READY)
    repository.finish_import_job(
        import_job_id,
        "success",
        result.rows_extracted,
        result.rows_loaded,
    )
    repository.finish_sync_run(
        sync_run_id,
        "success",
        result.rows_loaded,
        result.state.cursor_value,
    )
    return result


@router.get("/{source_id}/status", response_model=SourceStatusResponse)
def get_source_status(
    source_id: int,
    repository: RepositoryDep,
) -> SourceStatusResponse:
    source = repository.get_source(source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found.",
        )
    return SourceStatusResponse(source=source, state=repository.get_state(source_id))


@router.get("/{source_id}/errors", response_model=list[SourceErrorRecord])
def get_source_errors(
    source_id: int,
    repository: RepositoryDep,
) -> list[SourceErrorRecord]:
    source = repository.get_source(source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found.",
        )
    return repository.list_errors(source_id)
