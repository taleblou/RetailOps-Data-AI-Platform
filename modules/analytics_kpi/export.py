# Project:      RetailOps Data & AI Platform
# Module:       modules.analytics_kpi
# File:         export.py
# Path:         modules/analytics_kpi/export.py
#
# Summary:      Provides implementation support for the analytics kpi workflow.
# Purpose:      Supports the analytics kpi layer inside the modular repository architecture.
# Scope:        internal
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
#   - Key APIs: rows_to_csv_text, csv_response, json_download_response
#   - Dependencies: __future__, csv, io, json, collections.abc, typing, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping, Sequence
from typing import Any

from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

type Row = Mapping[str, Any] | BaseModel


def _as_row_mapping(row: Row) -> dict[str, Any]:
    if isinstance(row, BaseModel):
        return row.model_dump()
    return dict(row)


def rows_to_csv_text(
    rows: Sequence[Row],
    *,
    headers: Sequence[str] | None = None,
) -> str:
    normalized_rows = [_as_row_mapping(row) for row in rows]
    header_names = list(headers or [])
    if not header_names and normalized_rows:
        header_names = list(normalized_rows[0].keys())

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=header_names)
    writer.writeheader()
    if header_names:
        writer.writerows(normalized_rows)
    return buffer.getvalue()


def csv_response(
    *,
    filename: str,
    rows: Sequence[Row],
    headers: Sequence[str] | None = None,
) -> StreamingResponse:
    csv_text = rows_to_csv_text(rows, headers=headers)
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


def json_download_response(*, filename: str, payload: Any) -> JSONResponse:
    return JSONResponse(
        content=json.loads(json.dumps(payload, ensure_ascii=False)),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
