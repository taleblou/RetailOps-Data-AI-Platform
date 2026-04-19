# Project:      RetailOps Data & AI Platform
# Module:       tests.packaging
# File:         test_compose_profiles.py
# Path:         tests/packaging/test_compose_profiles.py
#
# Summary:      Validates Compose overlays and profile sample integrity.
# Purpose:      Prevents deployment-profile regressions in packaging assets.
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
#   - Key APIs: test_compose_files_are_valid_yaml, test_compose_validator_script_passes.
#   - Dependencies: subprocess, sys, pathlib, yaml.
#   - Constraints: Assumes repository root is the current working directory during pytest.
#   - Compatibility: Python 3.11+ with pytest and PyYAML.

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


def test_compose_files_are_valid_yaml() -> None:
    for path in sorted(Path("compose").glob("*.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict), f"Expected mapping in {path}"
        services = payload.get("services")
        assert isinstance(services, dict) and services, f"No services defined in {path}"


def test_compose_validator_script_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_compose_profiles.py"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "passed validation" in result.stdout
