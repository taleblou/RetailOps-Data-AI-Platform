# Project:      RetailOps Data & AI Platform
# Module:       tests.setup
# File:         conftest.py
# Path:         tests/setup/conftest.py
#
# Summary:      Shared fixtures for setup tests.
# Purpose:      Keeps settings cache isolated across setup-related test cases.
# Scope:        test
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
#   - Key APIs: clear_settings_cache
#   - Dependencies: __future__, pytest, config.settings
#   - Constraints: Fixture is autouse for setup test isolation.
#   - Compatibility: Python 3.12+ with pytest and repository test dependencies.

from __future__ import annotations

import pytest

from config.settings import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
