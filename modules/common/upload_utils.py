# Project:      RetailOps Data & AI Platform
# Module:       modules.common
# File:         upload_utils.py
# Path:         modules/common/upload_utils.py
#
# Summary:      Provides implementation support for the common workflow.
# Purpose:      Supports the common layer inside the modular repository architecture.
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
#   - Key APIs: to_text, to_float, to_int, normalize_key, canonical_value, parse_iso_date, ...
#   - Dependencies: __future__, csv, json, datetime, pathlib, typing, ...
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any


def to_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def to_float(value: object, *, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int | float):
        return float(value)
    text = to_text(value)
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def to_int(value: object, *, default: int = 0) -> int:
    return int(round(to_float(value, default=float(default))))


def normalize_key(value: str) -> str:
    cleaned = value.replace("/", " ").replace("-", " ")
    return "_".join(cleaned.strip().lower().split())


def canonical_value(row: dict[str, str], *aliases: str) -> str:
    for alias in aliases:
        key = normalize_key(alias)
        if key in row:
            return row[key]
    return ""


def parse_iso_date(value: object) -> date | None:
    text = to_text(value)
    if not text:
        return None
    for candidate in [text, text.replace("Z", "+00:00")]:
        try:
            return datetime.fromisoformat(candidate).date()
        except ValueError:
            pass
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def days_between(start: object, end: object, *, default: float = 0.0) -> float:
    start_date = parse_iso_date(start)
    end_date = parse_iso_date(end)
    if start_date is None or end_date is None:
        return default
    return float((end_date - start_date).days)


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def read_json_or_none(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def resolve_uploaded_csv_path(upload_id: str, uploads_dir: Path) -> Path:
    metadata_path = uploads_dir / f"{upload_id}.json"
    if metadata_path.exists():
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            stored_path = to_text(payload.get("stored_path"))
            if stored_path:
                csv_path = Path(stored_path)
                if csv_path.exists():
                    return csv_path
            filename = to_text(payload.get("filename"))
            if filename:
                candidate = uploads_dir / f"{upload_id}_{filename}"
                if candidate.exists():
                    return candidate
    candidates = sorted(uploads_dir.glob(f"{upload_id}_*.csv"))
    if candidates:
        return candidates[0]
    raise FileNotFoundError(f"No uploaded CSV was found for upload_id={upload_id}.")


def iter_normalized_rows(csv_path: Path) -> Iterable[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw_row in reader:
            yield {
                normalize_key(str(key)): to_text(value)
                for key, value in raw_row.items()
                if key is not None
            }
