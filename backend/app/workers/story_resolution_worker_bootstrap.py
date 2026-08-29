from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Callable
from urllib.parse import quote, urlencode


_REGION_PATTERN = re.compile(r"^[a-z]{2}(?:-gov)?-[a-z]+-\d$")
_SECRET_ARN_PATTERN = re.compile(
    r"^arn:aws:secretsmanager:(?P<region>[a-z0-9-]+):\d{12}:secret:[A-Za-z0-9/_+=.@-]+$"
)


class WorkerBootstrapError(RuntimeError):
    """A sanitized, operator-safe Worker startup failure."""


def _validate_configuration(
    *, region: str, secret_arn: str, endpoint: str, ca_path: Path
) -> None:
    if not _REGION_PATTERN.fullmatch(region):
        raise WorkerBootstrapError("aws_region_invalid")

    secret_match = _SECRET_ARN_PATTERN.fullmatch(secret_arn)
    if secret_match is None or secret_match.group("region") != region:
        raise WorkerBootstrapError("runtime_secret_arn_invalid")

    endpoint_pattern = re.compile(
        rf"^[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.{re.escape(region)}\.rds\.amazonaws\.com$"
    )
    if endpoint_pattern.fullmatch(endpoint) is None:
        raise WorkerBootstrapError("database_endpoint_invalid")

    if ca_path.is_symlink() or not ca_path.is_file():
        raise WorkerBootstrapError("rds_ca_invalid")


def load_database_url(
    client,
    *,
    region: str,
    secret_arn: str,
    endpoint: str,
    ca_path: str | Path,
) -> str:
    ca = Path(ca_path)
    _validate_configuration(
        region=region,
        secret_arn=secret_arn,
        endpoint=endpoint,
        ca_path=ca,
    )

    try:
        response = client.get_secret_value(SecretId=secret_arn)
    except Exception:
        raise WorkerBootstrapError("runtime_secret_unavailable") from None

    try:
        payload = json.loads(response["SecretString"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise WorkerBootstrapError("runtime_secret_invalid") from None

    if (
        not isinstance(payload, dict)
        or set(payload) != {"username", "password"}
        or payload.get("username") != "co_story_app"
        or not isinstance(payload.get("password"), str)
        or not payload["password"]
    ):
        raise WorkerBootstrapError("runtime_secret_invalid")

    username = quote(payload["username"], safe="")
    password = quote(payload["password"], safe="")
    query = urlencode({"sslmode": "verify-full", "sslrootcert": str(ca)})
    return f"postgresql://{username}:{password}@{endpoint}:5432/co_story?{query}"


def _create_secrets_client(region: str):
    import boto3

    return boto3.client("secretsmanager", region_name=region)


def main(
    *,
    create_client: Callable[[str], object] | None = None,
    run_worker: Callable[[], int] | None = None,
) -> int:
    create_client = create_client or _create_secrets_client

    try:
        region = os.environ.get("CO_STORY_AWS_REGION", "")
        client = create_client(region)
        database_url = load_database_url(
            client,
            region=region,
            secret_arn=os.environ.get("CO_STORY_RUNTIME_SECRET_ARN", ""),
            endpoint=os.environ.get("CO_STORY_DB_ENDPOINT", ""),
            ca_path=os.environ.get("CO_STORY_RDS_CA_PATH", ""),
        )
    except WorkerBootstrapError as exc:
        print(f"worker_bootstrap=stopped:{exc}")
        return 2
    except Exception:
        print("worker_bootstrap=stopped:runtime_secret_unavailable")
        return 2

    previous_database_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = database_url
    if run_worker is None:
        from app.workers.story_resolution_worker import main as run_worker

    try:
        return run_worker()
    finally:
        if previous_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous_database_url


if __name__ == "__main__":
    raise SystemExit(main())
