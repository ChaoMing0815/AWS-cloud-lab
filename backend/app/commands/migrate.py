import os
import sys

from app.adapters.postgres_migrations import apply_migrations


def main() -> int:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL is required", file=sys.stderr)
        return 2
    apply_migrations(dsn)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
