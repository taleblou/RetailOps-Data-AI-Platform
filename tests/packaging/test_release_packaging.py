# Project:      RetailOps Data & AI Platform
# Module:       tests.packaging
# File:         test_release_packaging.py
# Path:         tests/packaging/test_release_packaging.py
#
# Summary:      Contains automated tests for the packaging workflows and behaviors.
# Purpose:      Validates packaging behavior and protects the repository against regressions.
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
#   - Key APIs: test_packaging_required_scripts_and_docs_exist, test_packaging_scripts_have_valid_bash_syntax, test_packaging_quickstarts_reference_expected_profiles
#   - Dependencies: __future__, subprocess, pathlib
#   - Constraints: Assumes repository fixtures, deterministic sample data, and isolated test execution.
#   - Compatibility: Python 3.11+ with pytest and repository test dependencies.

from __future__ import annotations

import subprocess
from pathlib import Path


def test_packaging_required_scripts_and_docs_exist() -> None:
    required_paths = [
        Path("scripts/install.sh"),
        Path("scripts/upgrade.sh"),
        Path("scripts/backup.sh"),
        Path("scripts/restore.sh"),
        Path("scripts/load_demo_data.sh"),
        Path("scripts/health.sh"),
        Path("scripts/validate_compose_profiles.py"),
        Path("docs/quickstart/lite.md"),
        Path("docs/quickstart/standard.md"),
        Path("docs/quickstart/pro.md"),
        Path("config/samples/lite.env"),
        Path("config/samples/standard.env"),
        Path("config/samples/pro.env"),
        Path("docs/release_notes_packaging.md"),
        Path("docs/history/release_packaging_gap_report.md"),
        Path("docs/history/release_packaging_audit.md"),
    ]
    missing = [str(path) for path in required_paths if not path.exists()]
    assert not missing, f"Missing required release packaging files: {missing}"


def test_packaging_scripts_have_valid_bash_syntax() -> None:
    for script in [
        Path("scripts/common.sh"),
        Path("scripts/install.sh"),
        Path("scripts/upgrade.sh"),
        Path("scripts/backup.sh"),
        Path("scripts/restore.sh"),
        Path("scripts/load_demo_data.sh"),
        Path("scripts/health.sh"),
    ]:
        result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


def test_packaging_quickstarts_reference_expected_profiles() -> None:
    assert "Lite profile" in Path("docs/quickstart/lite.md").read_text(encoding="utf-8")
    assert "Standard profile" in Path("docs/quickstart/standard.md").read_text(encoding="utf-8")
    assert "Pro profile" in Path("docs/quickstart/pro.md").read_text(encoding="utf-8")
