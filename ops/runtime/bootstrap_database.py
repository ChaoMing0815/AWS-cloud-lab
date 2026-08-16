#!/usr/bin/env python3
"""Create the bounded application DB role and write its protected runtime DSN."""

import grp
import json
import os
import pwd
import re
import tempfile
from pathlib import Path
from urllib.parse import quote, urlencode, urlunsplit

import psycopg
from psycopg import sql


APP_USERNAME = "co_story_app"
DATABASE_NAME = "co_story"
_ENDPOINT = re.compile(r"^[A-Za-z0-9.-]+$")


def _secret(client, arn: str, expected_username: str | None = None) -> tuple[str, str]:
    response = client.get_secret_value(SecretId=arn)
    try:
        payload = json.loads(response["SecretString"])
        username = payload["username"]
        password = payload["password"]
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("database secret is incomplete") from error
    if not isinstance(username, str) or not username:
        raise ValueError("database secret username is invalid")
    if not isinstance(password, str) or not password:
        raise ValueError("database secret password is invalid")
    if expected_username is not None and username != expected_username:
        raise ValueError("application database username is unexpected")
    return username, password


def read_database_secrets(
    client,
    master_secret_arn: str,
    application_secret_arn: str,
) -> tuple[tuple[str, str], tuple[str, str]]:
    master = _secret(client, master_secret_arn)
    application = _secret(client, application_secret_arn, APP_USERNAME)
    return master, application


def database_url(
    username: str,
    password: str,
    endpoint: str,
    port: int,
    ca_path: str,
) -> str:
    if not _ENDPOINT.fullmatch(endpoint) or port != 5432:
        raise ValueError("database endpoint is invalid")
    if not ca_path.startswith("/") or "\n" in ca_path or "\r" in ca_path:
        raise ValueError("RDS CA path is invalid")
    userinfo = f"{quote(username, safe='')}:{quote(password, safe='')}"
    query = urlencode({"sslmode": "verify-full", "sslrootcert": ca_path})
    return urlunsplit(
        (
            "postgresql",
            f"{userinfo}@{endpoint}:{port}",
            f"/{DATABASE_NAME}",
            query,
            "",
        )
    )


def provision_application_role(connection, password: str) -> None:
    attributes = connection.execute(
        "SELECT rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, "
        "rolreplication, rolbypassrls FROM pg_roles WHERE rolname = %s",
        (APP_USERNAME,),
    ).fetchone()
    if attributes:
        can_login, superuser, create_db, create_role, replication, bypass_rls = (
            attributes
        )
        if not can_login or any(
            (superuser, create_db, create_role, replication, bypass_rls)
        ):
            raise RuntimeError("application database role has unsafe attributes")
        connection.execute(
            sql.SQL("ALTER ROLE {} WITH ").format(sql.Identifier(APP_USERNAME))
            + sql.SQL("PASSWORD {}").format(sql.Literal(password))
        )
    else:
        role_options = sql.SQL(
            "LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE "
            "NOREPLICATION NOBYPASSRLS"
        ).format(sql.Literal(password))
        connection.execute(
            sql.SQL("CREATE ROLE {} WITH ").format(sql.Identifier(APP_USERNAME))
            + role_options
        )
    connection.execute(
        sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
            sql.Identifier(DATABASE_NAME),
            sql.Identifier(APP_USERNAME),
        )
    )
    connection.execute(
        sql.SQL("GRANT USAGE, CREATE ON SCHEMA public TO {}").format(
            sql.Identifier(APP_USERNAME)
        )
    )


def write_database_environment(
    path: Path,
    database_dsn: str,
    owner_uid: int,
    group_gid: int,
) -> None:
    if "\n" in database_dsn or "\r" in database_dsn:
        raise ValueError("database URL contains a line break")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            os.fchmod(temporary.fileno(), 0o640)
            os.fchown(temporary.fileno(), owner_uid, group_gid)
            temporary.write(f"DATABASE_URL={database_dsn}\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def _required_environment(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def main() -> int:
    import boto3

    region = _required_environment("CO_STORY_AWS_REGION")
    endpoint = _required_environment("CO_STORY_DB_ENDPOINT")
    port = int(_required_environment("CO_STORY_DB_PORT"))
    master_arn = _required_environment("CO_STORY_MASTER_SECRET_ARN")
    application_arn = _required_environment("CO_STORY_APP_DB_SECRET_ARN")
    ca_path = _required_environment("CO_STORY_RDS_CA_PATH")
    target = Path(
        os.environ.get("CO_STORY_DATABASE_ENV_PATH", "/etc/co-story/database.env")
    )

    secrets = boto3.client("secretsmanager", region_name=region)
    master, application = read_database_secrets(secrets, master_arn, application_arn)
    master_dsn = database_url(*master, endpoint, port, ca_path)
    application_dsn = database_url(*application, endpoint, port, ca_path)
    with psycopg.connect(master_dsn) as connection:
        provision_application_role(connection, application[1])

    write_database_environment(
        target,
        application_dsn,
        owner_uid=pwd.getpwnam("root").pw_uid,
        group_gid=grp.getgrnam("co-story").gr_gid,
    )
    print("database bootstrap complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
