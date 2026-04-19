# Project:      RetailOps Data & AI Platform
# Module:       core.worker
# File:         main.py
# Path:         core/worker/main.py
#
# Summary:      Provides the command-line entry point for the modular worker engine.
# Purpose:      Lets operators enqueue jobs, inspect worker state, drain the queue, or run the worker as a polling service.
# Scope:        tool
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
#   - Key APIs: main().
#   - Dependencies: argparse, json, time, pathlib, core.worker.service.
#   - Constraints: JSON payloads passed on the CLI must be valid objects.
#   - Compatibility: Python 3.11+ standard runtime.

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from core.worker.service import (
    WorkerRuntime,
    enqueue_job,
    get_worker_summary,
    run_next_job,
    run_until_empty,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RetailOps modular worker service")
    parser.add_argument("--queue-path", default="data/artifacts/worker/queue.json")
    parser.add_argument("--run-dir", default="data/artifacts/worker/runs")
    subparsers = parser.add_subparsers(dest="command", required=True)
    enqueue_parser = subparsers.add_parser("enqueue")
    enqueue_parser.add_argument("job_type")
    enqueue_parser.add_argument("--payload", default="{}")
    enqueue_parser.add_argument("--priority", type=int, default=100)
    enqueue_parser.add_argument("--max-attempts", type=int, default=3)
    drain_parser = subparsers.add_parser("drain")
    drain_parser.add_argument("--max-jobs", type=int, default=None)
    subparsers.add_parser("run-once")
    subparsers.add_parser("summary")
    daemon_parser = subparsers.add_parser("daemon")
    daemon_parser.add_argument("--poll-seconds", type=int, default=30)
    daemon_parser.add_argument("--max-loops", type=int, default=None)
    return parser


def _runtime_from_args(args: argparse.Namespace) -> WorkerRuntime:
    return WorkerRuntime(queue_path=Path(args.queue_path), run_dir=Path(args.run_dir))


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    runtime = _runtime_from_args(args)
    if args.command == "enqueue":
        payload = json.loads(args.payload)
        if not isinstance(payload, dict):
            raise ValueError("Worker enqueue payload must be a JSON object.")
        job = enqueue_job(
            runtime,
            job_type=args.job_type,
            payload=payload,
            priority=args.priority,
            max_attempts=args.max_attempts,
        )
        print(json.dumps(job.to_dict(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "run-once":
        result = run_next_job(runtime)
        print(
            json.dumps(
                result.to_dict() if result else {"status": "idle"}, ensure_ascii=False, indent=2
            )
        )
        return 0
    if args.command == "drain":
        results = [item.to_dict() for item in run_until_empty(runtime, max_jobs=args.max_jobs)]
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0
    if args.command == "summary":
        print(json.dumps(get_worker_summary(runtime), ensure_ascii=False, indent=2))
        return 0
    loops = 0
    while True:
        result = run_next_job(runtime)
        print(json.dumps(result.to_dict() if result else {"status": "idle"}, ensure_ascii=False))
        loops += 1
        if args.max_loops is not None and loops >= args.max_loops:
            return 0
        time.sleep(max(args.poll_seconds, 1))


if __name__ == "__main__":
    raise SystemExit(main())
