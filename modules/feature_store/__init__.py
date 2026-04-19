# Project:      RetailOps Data & AI Platform
# Module:       modules.feature_store
# File:         __init__.py
# Path:         modules/feature_store/__init__.py
#
# Summary:      Defines the modules.feature_store package surface and package-level exports.
# Purpose:      Marks modules.feature_store as a Python package and centralizes its package-level imports.
# Scope:        internal
# Status:       internal
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
#   - Key APIs: None; module-level constants and imports only.
#   - Dependencies: __future__, router, service
#   - Constraints: Package exports should stay lightweight and avoid introducing import cycles.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

from .router import router
from .service import build_feature_store_artifact

__all__ = ["router", "build_feature_store_artifact"]
