# Project:      RetailOps Data & AI Platform
# Module:       scripts
# File:         generate_dashboard_workspace.py
# Path:         scripts/generate_dashboard_workspace.py
#
# Summary:      Provides a repository script for the generate dashboard workspace workflow.
# Purpose:      Automates the generate dashboard workspace operational task for local development and maintenance.
# Scope:        script
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
#   - Key APIs: parse_args, main
#   - Dependencies: __future__, argparse, pathlib, modules.dashboard_hub.service
#   - Constraints: File-system paths and serialized artifact formats must remain stable for downstream consumers.
#   - Compatibility: Python 3.11+ and repository-supported runtime dependencies.

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from modules.dashboard_hub.service import publish_dashboard_workspace


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a unified RetailOps dashboard workspace artifact.",
    )
    parser.add_argument("upload_id")
    parser.add_argument("--uploads-dir", default="data/uploads")
    parser.add_argument("--artifact-root", default="data/artifacts/dashboard_hub")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--max-rows", type=int, default=8)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = publish_dashboard_workspace(
        upload_id=args.upload_id,
        uploads_dir=Path(args.uploads_dir),
        artifact_root=Path(args.artifact_root),
        refresh=args.refresh,
        max_rows=args.max_rows,
    )
    print(result["artifact_path"])
    print(result["html_artifact_path"])


if __name__ == "__main__":
    main()
