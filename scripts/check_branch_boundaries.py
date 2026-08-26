#!/usr/bin/env python3
"""Fail closed when a parallel work branch changes files outside its ownership."""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / ".agents" / "work-boundaries.json"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", required=True)
    parser.add_argument("--base")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--allow-unregistered", action="store_true")
    args = parser.parse_args()
    if not args.path and not args.base:
        parser.error("provide at least one --path or --base")
    if args.path and args.base:
        parser.error("--path and --base are mutually exclusive")
    return args


def _normalize_path(raw_path: str) -> str:
    path = PurePosixPath(raw_path.replace("\\", "/"))
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise ValueError(f"unsafe repository path: {raw_path}")
    normalized = path.as_posix()
    if normalized in {"", "."}:
        raise ValueError(f"unsafe repository path: {raw_path}")
    return normalized


def _changed_paths(base: str, head: str) -> list[str]:
    result = subprocess.run(
        ("git", "diff", "--name-only", "--diff-filter=ACMR", f"{base}...{head}"),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(result.stderr.strip() or "unable to calculate changed paths", file=sys.stderr)
        raise SystemExit(4)
    return [line for line in result.stdout.splitlines() if line]


def _matches(path: str, patterns: list[str]) -> bool:
    return any(path == pattern or fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def main() -> int:
    args = _parse_args()
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    branch_policy = policy["branches"].get(args.branch)
    if branch_policy is None:
        if args.allow_unregistered:
            print(f"branch_boundary=skipped:unregistered:{args.branch}")
            return 0
        print(f"branch_boundary=failed:unregistered branch:{args.branch}", file=sys.stderr)
        return 3

    raw_paths = args.path or _changed_paths(args.base, args.head)
    try:
        paths = sorted({_normalize_path(path) for path in raw_paths})
    except ValueError as error:
        print(f"branch_boundary=failed:{error}", file=sys.stderr)
        return 2

    protected = policy["protected_paths"]
    allowed = branch_policy["allowed_paths"]
    violations = [
        path
        for path in paths
        if _matches(path, protected) or not _matches(path, allowed)
    ]
    if violations:
        print(f"branch_boundary=failed:{args.branch}", file=sys.stderr)
        for path in violations:
            print(f"unauthorized_path={path}", file=sys.stderr)
        return 2

    print(f"branch_boundary=passed:{args.branch}:paths={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
