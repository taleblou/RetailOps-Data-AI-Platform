# Project:      RetailOps Data & AI Platform
# Module:       modules.cdc
# File:         __init__.py
# Path:         modules/cdc/__init__.py
#
# Summary:      Defines the modules.cdc package surface and package-level exports.
# Purpose:      Marks modules.cdc as a Python package and centralizes its package-level imports.
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
from .service import build_cdc_artifact

__all__ = ["router", "build_cdc_artifact"]
