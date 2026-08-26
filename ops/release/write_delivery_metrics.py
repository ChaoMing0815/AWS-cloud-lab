#!/usr/bin/env python3
"""Write sanitized, comparable Tier 3 delivery timing evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _optional_epoch(value: str) -> int | None:
    if value == "":
        return None
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("epoch must not be negative")
    return parsed


def _duration(start: int | None, end: int | None) -> int | None:
    if start is None or end is None:
        return None
    return end - start


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--status",
        choices=("success", "failure", "cancelled"),
        required=True,
    )
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--request-epoch", type=_optional_epoch, required=True)
    parser.add_argument("--approval-epoch", type=_optional_epoch, default=None)
    parser.add_argument("--deploy-start-epoch", type=_optional_epoch, default=None)
    parser.add_argument("--artifact-ready-epoch", type=_optional_epoch, default=None)
    parser.add_argument("--release-start-epoch", type=_optional_epoch, default=None)
    parser.add_argument("--completed-epoch", type=_optional_epoch, required=True)
    return parser


def main() -> int:
    parser = _parser()
    args = parser.parse_args()
    if not re.fullmatch(r"[a-f0-9]{40}", args.commit_sha):
        parser.error("commit SHA must be forty lowercase hexadecimal characters")
    if not re.fullmatch(r"[0-9]+", args.workflow_run_id):
        parser.error("workflow run ID must be numeric")

    ordered = (
        args.request_epoch,
        args.approval_epoch,
        args.deploy_start_epoch,
        args.artifact_ready_epoch,
        args.release_start_epoch,
        args.completed_epoch,
    )
    observed = [value for value in ordered if value is not None]
    if observed != sorted(observed):
        parser.error("timestamps must be monotonic")

    timestamps = {
        "request": args.request_epoch,
        "approval": args.approval_epoch,
        "deploy_start": args.deploy_start_epoch,
        "artifact_ready": args.artifact_ready_epoch,
        "release_start": args.release_start_epoch,
        "completed": args.completed_epoch,
    }
    metrics = {
        "schema_version": 1,
        "method": "automatic",
        "status": args.status,
        "verified": args.status == "success",
        "commit_sha": args.commit_sha,
        "workflow_run_id": args.workflow_run_id,
        "human_interaction_count": 2,
        "timestamps_epoch": timestamps,
        "durations_seconds": {
            "approval_wait": _duration(args.request_epoch, args.approval_epoch),
            "automation_execution": _duration(
                args.deploy_start_epoch, args.completed_epoch
            ),
            "build_and_scan": _duration(
                args.deploy_start_epoch, args.artifact_ready_epoch
            ),
            "ssm_release_attempt": _duration(
                args.release_start_epoch, args.completed_epoch
            ),
            "end_to_end": _duration(args.request_epoch, args.completed_epoch),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
