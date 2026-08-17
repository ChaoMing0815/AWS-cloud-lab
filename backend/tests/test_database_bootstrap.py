import importlib.util
import json
import os
import stat
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import pytest


ROOT = Path(__file__).parents[2]
BOOTSTRAP = ROOT / "ops/runtime/bootstrap_database.py"


def _module():
    assert BOOTSTRAP.is_file(), "database bootstrap 工具尚未建立"
    spec = importlib.util.spec_from_file_location("bootstrap_database", BOOTSTRAP)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _SecretsClient:
    def __init__(self, values):
        self.values = values
        self.calls = []

    def get_secret_value(self, **kwargs):
        self.calls.append(kwargs)
        return {"SecretString": json.dumps(self.values[kwargs["SecretId"]])}


class _Result:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class _Connection:
    def __init__(self, role_exists=False, role_attributes=None):
        self.role_exists = role_exists
        self.role_attributes = role_attributes or (
            True,
            False,
            False,
            False,
            False,
            False,
        )
        self.statements = []
        self.raw_statements = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=None):
        self.raw_statements.append((sql, params))
        rendered = sql.as_string() if hasattr(sql, "as_string") else str(sql)
        self.statements.append((rendered, params))
        if "FROM pg_roles" in rendered:
            return _Result(self.role_attributes if self.role_exists else None)
        return _Result()


def test_secret_reader_uses_only_the_supplied_arns_and_requires_expected_users() -> None:
    module = _module()
    client = _SecretsClient(
        {
            "master-arn": {"username": "postgres", "password": "master-secret"},
            "app-arn": {"username": "co_story_app", "password": "app-secret"},
        }
    )

    master, application = module.read_database_secrets(
        client,
        master_secret_arn="master-arn",
        application_secret_arn="app-arn",
    )

    assert master == ("postgres", "master-secret")
    assert application == ("co_story_app", "app-secret")
    assert client.calls == [
        {"SecretId": "master-arn"},
        {"SecretId": "app-arn"},
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "wrong_user", "password": "secret"},
        {"username": "co_story_app", "password": ""},
        {"username": "co_story_app"},
    ],
)
def test_secret_reader_rejects_an_unexpected_or_incomplete_application_secret(payload) -> None:
    module = _module()
    client = _SecretsClient(
        {
            "master-arn": {"username": "postgres", "password": "master-secret"},
            "app-arn": payload,
        }
    )

    with pytest.raises(ValueError):
        module.read_database_secrets(client, "master-arn", "app-arn")


def test_database_url_encodes_credentials_and_requires_full_rds_ca_verification() -> None:
    module = _module()
    url = module.database_url(
        username="co_story_app",
        password="space and:/@?#%+secret",
        endpoint="db.example.test",
        port=5432,
        ca_path="/etc/pki/rds/rds-ca.pem",
    )
    parsed = urlsplit(url)

    assert parsed.scheme == "postgresql"
    assert unquote(parsed.username) == "co_story_app"
    assert unquote(parsed.password) == "space and:/@?#%+secret"
    assert parsed.hostname == "db.example.test"
    assert parsed.port == 5432
    assert parsed.path == "/co_story"
    assert parse_qs(parsed.query) == {
        "sslmode": ["verify-full"],
        "sslrootcert": ["/etc/pki/rds/rds-ca.pem"],
    }


def test_new_role_bootstrap_is_bounded_and_never_interpolates_password() -> None:
    module = _module()
    connection = _Connection(role_exists=False)
    password = "must-not-appear-in-sql"

    module.provision_application_role(connection, password)

    statements = [sql for sql, _ in connection.statements]
    assert any("FROM pg_roles" in sql for sql in statements)
    assert any("CREATE ROLE" in sql for sql in statements)
    assert any('GRANT CONNECT ON DATABASE "co_story"' in sql for sql in statements)
    assert any('GRANT USAGE, CREATE ON SCHEMA public TO "co_story_app"' in sql for sql in statements)
    password_statements = [
        query
        for query, _ in connection.raw_statements
        if "CREATE ROLE" in (query.as_string() if hasattr(query, "as_string") else str(query))
        or "ALTER ROLE" in (query.as_string() if hasattr(query, "as_string") else str(query))
    ]
    assert len(password_statements) == 1
    assert not isinstance(password_statements[0], str)
    assert "Literal(" in repr(password_statements[0])
    assert any("NOSUPERUSER" in sql for sql in statements)
    assert any("NOCREATEDB" in sql for sql in statements)
    assert any("NOCREATEROLE" in sql for sql in statements)
    assert any("NOREPLICATION" in sql for sql in statements)
    assert any("NOBYPASSRLS" in sql for sql in statements)


def test_existing_bounded_role_rotates_only_its_password() -> None:
    module = _module()
    connection = _Connection(role_exists=True)

    module.provision_application_role(connection, "rotated-secret")

    alter_role = next(
        sql for sql, _ in connection.statements if "ALTER ROLE" in sql
    )
    assert "PASSWORD" in alter_role
    assert "SUPERUSER" not in alter_role
    assert "CREATEDB" not in alter_role
    assert "CREATEROLE" not in alter_role
    assert "REPLICATION" not in alter_role
    assert "BYPASSRLS" not in alter_role


def test_existing_role_with_privilege_drift_fails_closed() -> None:
    module = _module()
    connection = _Connection(
        role_exists=True,
        role_attributes=(True, True, False, False, False, False),
    )

    with pytest.raises(RuntimeError, match="unsafe attributes"):
        module.provision_application_role(connection, "rotated-secret")

    assert not any("ALTER ROLE" in sql for sql, _ in connection.statements)


def test_database_environment_is_atomically_written_with_bounded_permissions(tmp_path) -> None:
    module = _module()
    target = tmp_path / "database.env"
    target.write_text("DATABASE_URL=stale\n", encoding="utf-8")
    url = "postgresql://co_story_app:secret@db.example.test/co_story"

    module.write_database_environment(
        target,
        url,
        owner_uid=os.getuid(),
        group_gid=os.getgid(),
    )

    assert target.read_text(encoding="utf-8") == f"DATABASE_URL={url}\n"
    assert stat.S_IMODE(target.stat().st_mode) == 0o640
    assert not list(tmp_path.glob(".database.env.*"))


@pytest.mark.parametrize("unsafe_url", ["value\nINJECTED=yes", "value\rINJECTED=yes"])
def test_database_environment_rejects_line_injection(tmp_path, unsafe_url) -> None:
    module = _module()

    with pytest.raises(ValueError):
        module.write_database_environment(
            tmp_path / "database.env",
            unsafe_url,
            owner_uid=os.getuid(),
            group_gid=os.getgid(),
        )
