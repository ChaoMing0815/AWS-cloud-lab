#!/usr/bin/env python3
"""Probe fixed Co-Story health endpoints without printing response bodies."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from urllib.request import Request, urlopen


def _runtime_health_host() -> str:
    explicit_host = os.environ.get("CO_STORY_HEALTH_HOST", "").strip()
    if explicit_host:
        return explicit_host

    allowed_hosts = os.environ.get("CO_STORY_ALLOWED_HOSTS", "")
    for candidate in allowed_hosts.split(","):
        normalized = candidate.strip()
        if normalized:
            return normalized

    return "localhost"


def main(
    *,
    open_url: Callable = urlopen,
    host: str | None = None,
    port: int | None = None,
) -> int:
    health_host = host or _runtime_health_host()
    health_port = port or int(os.environ.get("CO_STORY_HEALTH_PORT", "8000"))
    for endpoint in ("live", "ready"):
        request = Request(
            f"http://127.0.0.1:{health_port}/api/v1/{endpoint}",
            headers={"Host": health_host},
        )
        try:
            with open_url(request, timeout=5):
                pass
        except Exception:
            print(f"container_health={endpoint}_failed", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    cli_host = sys.argv[1] if len(sys.argv) > 1 else None
    cli_port = int(sys.argv[2]) if len(sys.argv) > 2 else None
    raise SystemExit(main(host=cli_host, port=cli_port))
