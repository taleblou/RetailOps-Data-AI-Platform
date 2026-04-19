# Project:      RetailOps Data & AI Platform
# Module:       packages.retailops_ingestion.src.retailops_ingestion
# File:         __init__.py
# Path:         packages/retailops_ingestion/src/retailops_ingestion/__init__.py
#
# Summary:      Exports ingestion package metadata for connector and source-management capabilities.
# Purpose:      Provides a minimal package entry point for ingestion distribution metadata and typed imports.
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
#   - Main types: PackageMetadata.
#   - Key APIs: PACKAGE_NAME, PACKAGE_ROLE, package_info.
#   - Dependencies: Shared standard-library metadata only.
#   - Constraints: Package exports should stay lightweight and avoid introducing import cycles or runtime-only dependencies.
#   - Compatibility: Python 3.11+ and repository-supported packaging workflows.

from __future__ import annotations

from typing import Final, TypedDict


class PackageMetadata(TypedDict):
    package_name: str
    package_role: str


PACKAGE_NAME: Final[str] = "retailops-ingestion"
PACKAGE_ROLE: Final[str] = "ingestion"


__all__ = ["PACKAGE_NAME", "PACKAGE_ROLE", "PackageMetadata", "package_info"]


def package_info() -> PackageMetadata:
    return {
        "package_name": PACKAGE_NAME,
        "package_role": PACKAGE_ROLE,
    }
