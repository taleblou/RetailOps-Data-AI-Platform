# Project:      RetailOps Data & AI Platform
# Module:       modules.metadata
# File:         __init__.py
# Path:         modules/metadata/__init__.py
#
# Summary:      Defines the modules.metadata package surface and package-level exports.
# Purpose:      Marks modules.metadata as a Python package and centralizes its package-level imports.
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
from .service import build_metadata_artifact

__all__ = ["router", "build_metadata_artifact"]
