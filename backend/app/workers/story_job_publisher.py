from __future__ import annotations

import os
import sys
import threading

from app.adapters.production_storyteller_factory import (
    build_production_story_job_publisher,
)


def run_publisher(publisher, *, stop_event=None) -> str:
    stopped = stop_event or threading.Event()
    while not stopped.is_set():
        outcome = publisher.run_once()
        wait_seconds = 0 if outcome == "published" else 1
        if stopped.wait(wait_seconds):
            break
    return "stopped"


def main() -> int:
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        print("publisher_result=stopped:database_url_missing")
        return 2
    try:
        publisher = build_production_story_job_publisher(database_url)
        result = run_publisher(publisher)
    except Exception:
        print("publisher_result=stopped:publisher_bootstrap_failure")
        return 2
    print(f"publisher_result={result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
