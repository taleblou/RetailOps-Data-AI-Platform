#!/usr/bin/env python3
# Project:      RetailOps Data & AI Platform
# Module:       scripts
# File:         generate_pro_platform_bundle.py
# Path:         scripts/generate_pro_platform_bundle.py
#
# Summary:      Generates all Pro platform deployment bundles under a chosen artifact directory.
# Purpose:      Provides a single operator entry point to materialize Pro module artifacts and a combined deployment plan.
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

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from modules.advanced_serving.service import build_advanced_serving_artifact
from modules.cdc.service import build_cdc_artifact
from modules.common.platform_extensions import build_platform_deployment_plan
from modules.feature_store.service import build_feature_store_artifact
from modules.lakehouse.service import build_lakehouse_artifact
from modules.metadata.service import build_metadata_artifact
from modules.query_layer.service import build_query_layer_artifact
from modules.streaming.service import build_streaming_artifact

Builder = Callable[[Path, bool], dict[str, object]]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", default="data/artifacts/pro_platform")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()
    root = Path(args.artifact_dir)
    builders: dict[str, Builder] = {
        "cdc": build_cdc_artifact,
        "streaming": build_streaming_artifact,
        "lakehouse": build_lakehouse_artifact,
        "query_layer": build_query_layer_artifact,
        "metadata": build_metadata_artifact,
        "feature_store": build_feature_store_artifact,
        "advanced_serving": build_advanced_serving_artifact,
    }
    summary: dict[str, dict[str, object]] = {}
    for name, builder in builders.items():
        summary[name] = builder(root / name, args.refresh)
    payload = {
        "platform_surface": "extensions",
        "platform_name": "RetailOps Pro Data Platform",
        "module_count": len(summary),
        "deployment_ready_count": sum(
            1 for item in summary.values() if item.get("status") == "deployment_ready"
        ),
        "modules": summary,
    }
    summary_path = root / "platform_extensions_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    deployment_plan = build_platform_deployment_plan(
        modules=summary, artifact_root=root, repo_root=REPO_ROOT
    )
    plan_path = root / "platform_extensions_deployment_plan.json"
    plan_path.write_text(
        json.dumps(deployment_plan, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    operator_notes = root / "platform_extensions_operator_checklist.md"
    operator_notes.write_text(
        "# Pro platform operator checklist\n\n"
        + "\n".join(f"- {item}" for item in deployment_plan["operator_checklist"])
        + "\n",
        encoding="utf-8",
    )
    print(summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
