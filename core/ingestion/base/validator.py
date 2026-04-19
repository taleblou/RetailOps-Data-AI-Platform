# Project:      RetailOps Data & AI Platform
# Module:       core.ingestion.base
# File:         validator.py
# Path:         core/ingestion/base/validator.py
#
# Summary:      Validates inputs and invariants for the ingestion base workflow.
# Purpose:      Enforces structural and business rules before ingestion base processing continues.
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
#   - Main types: DataValidator
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, datetime, typing, core.ingestion.base.models
#   - Constraints: Internal interfaces should remain aligned with adjacent modules and repository conventions.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from datetime import datetime
from typing import Any

from core.ingestion.base.models import ValidationIssue, ValidationResult


class DataValidator:
    def validate(
        self,
        rows: list[dict[str, Any]],
        required_columns: list[str] | None = None,
        type_hints: dict[str, str] | None = None,
        unique_key_columns: list[str] | None = None,
    ) -> ValidationResult:
        required_columns = required_columns or []
        type_hints = type_hints or {}
        unique_key_columns = unique_key_columns or []
        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []
        seen_keys: set[tuple[Any, ...]] = set()

        for row_number, row in enumerate(rows, start=1):
            for column in required_columns:
                value = row.get(column)
                if value in (None, ""):
                    errors.append(
                        ValidationIssue(
                            level="error",
                            code="required_missing",
                            message=(f"Required column '{column}' is missing or empty."),
                            column=column,
                            row_number=row_number,
                            value=value,
                        )
                    )

            for column, expected_type in type_hints.items():
                value = row.get(column)
                if value in (None, ""):
                    continue
                if not self._matches_type(value, expected_type):
                    errors.append(
                        ValidationIssue(
                            level="error",
                            code="type_mismatch",
                            message=(
                                f"Column '{column}' expected type "
                                f"'{expected_type}' but got value '{value}'."
                            ),
                            column=column,
                            row_number=row_number,
                            value=value,
                        )
                    )

            if unique_key_columns:
                key = tuple(row.get(column) for column in unique_key_columns)
                if all(item not in (None, "") for item in key):
                    if key in seen_keys:
                        errors.append(
                            ValidationIssue(
                                level="error",
                                code="duplicate_key",
                                message=(
                                    f"Duplicate key detected for columns {unique_key_columns}."
                                ),
                                row_number=row_number,
                                value=dict(
                                    zip(
                                        unique_key_columns,
                                        key,
                                        strict=False,
                                    )
                                ),
                            )
                        )
                    seen_keys.add(key)
                else:
                    warnings.append(
                        ValidationIssue(
                            level="warning",
                            code="incomplete_key",
                            message=(
                                "Unique key check skipped because one or more key values are empty."
                            ),
                            row_number=row_number,
                        )
                    )

        return ValidationResult(
            valid=not errors,
            errors=errors,
            warnings=warnings,
            stats={
                "row_count": len(rows),
                "error_count": len(errors),
                "warning_count": len(warnings),
            },
        )

    @staticmethod
    def _matches_type(value: Any, expected_type: str) -> bool:
        normalized = expected_type.lower().strip()
        if normalized in {"str", "string", "text"}:
            return True
        if normalized in {"int", "integer"}:
            try:
                int(str(value))
            except (TypeError, ValueError):
                return False
            return True
        if normalized in {"float", "numeric", "decimal"}:
            try:
                float(str(value))
            except (TypeError, ValueError):
                return False
            return True
        if normalized in {"datetime", "timestamp"}:
            try:
                datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError:
                return False
            return True
        return True
