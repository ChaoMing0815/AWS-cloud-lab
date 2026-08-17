import pytest
from fastapi.testclient import TestClient

from app.adapters.memory_room_repository import MemoryRoomRepository
from app.main import create_app


class ReadinessRepository(MemoryRoomRepository):
    def __init__(self, readiness) -> None:
        super().__init__()
        self.readiness = readiness

    def is_ready(self) -> bool:
        if isinstance(self.readiness, Exception):
            raise self.readiness
        return self.readiness


class CountingStoryteller:
    def __init__(self) -> None:
        self.calls = 0

    def resolve_round(self, _room) -> str:
        self.calls += 1
        return "測試敘事"

    def resolve_ending(self, _room) -> str:
        self.calls += 1
        return "測試結局"


def configure_production(monkeypatch) -> None:
    monkeypatch.setenv("CO_STORY_ENV", "production")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://app:secret@db.example.test/co_story?sslmode=verify-full&sslrootcert=/run/certs/rds-ca.pem",
    )
    monkeypatch.setenv("CO_STORY_COOKIE_SECURE", "true")
    monkeypatch.setenv("CO_STORY_ALLOWED_HOSTS", "app.example.test")
    monkeypatch.setenv("CO_STORY_ALLOWED_ORIGINS", "https://app.example.test")


def production_app(monkeypatch, repository=None, storyteller=None):
    configure_production(monkeypatch)
    return create_app(
        room_repository=repository or ReadinessRepository(True),
        storyteller=storyteller or CountingStoryteller(),
    )


def test_live_and_ready_are_public_and_do_not_invoke_storyteller() -> None:
    storyteller = CountingStoryteller()
    app = create_app(
        room_repository=ReadinessRepository(True),
        storyteller=storyteller,
    )
    with TestClient(app) as client:
        live = client.get("/api/v1/live")
        ready = client.get("/api/v1/ready")

    assert live.status_code == 200
    assert live.json() == {"status": "ok", "service": "co-story-api"}
    assert ready.status_code == 200
    assert ready.json() == {"status": "ok", "service": "co-story-api"}
    assert storyteller.calls == 0


@pytest.mark.parametrize("readiness", [False, RuntimeError("database password unavailable")])
def test_ready_returns_generic_503_when_repository_is_not_ready(readiness) -> None:
    app = create_app(
        room_repository=ReadinessRepository(readiness),
        storyteller=CountingStoryteller(),
    )
    with TestClient(app) as client:
        response = client.get("/api/v1/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "service": "co-story-api"}
    assert "database password unavailable" not in response.text


def test_production_rejects_a_host_not_in_its_allowlist(monkeypatch) -> None:
    app = production_app(monkeypatch)
    with TestClient(app, base_url="https://app.example.test") as client:
        response = client.get("/api/v1/live", headers={"Host": "attacker.example.test"})

    assert response.status_code == 400


@pytest.mark.parametrize("origin", [None, "https://attacker.example.test"])
def test_production_rejects_unsafe_api_request_without_exact_allowed_origin(monkeypatch, origin) -> None:
    app = production_app(monkeypatch)
    headers = {"Idempotency-Key": "origin-release-gate"}
    if origin is not None:
        headers["Origin"] = origin
    with TestClient(app, base_url="https://app.example.test") as client:
        response = client.post("/api/v1/rooms", json={"nickname": "房主"}, headers=headers)

    assert response.status_code == 403


def test_production_allows_exact_origin_for_unsafe_api_request(monkeypatch) -> None:
    app = production_app(monkeypatch)
    with TestClient(app, base_url="https://app.example.test") as client:
        response = client.post(
            "/api/v1/rooms",
            json={"nickname": "房主"},
            headers={
                "Origin": "https://app.example.test",
                "Idempotency-Key": "allowed-origin-release-gate",
            },
        )

    assert response.status_code == 201


def test_production_live_allows_missing_origin_and_sets_security_headers(monkeypatch) -> None:
    app = production_app(monkeypatch)
    with TestClient(app, base_url="https://app.example.test") as client:
        response = client.get("/api/v1/live")

    assert response.status_code == 200
    assert response.headers["strict-transport-security"] == "max-age=31536000; includeSubDomains"
    assert "default-src 'self'" in response.headers["content-security-policy"]
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "same-origin"


def test_development_does_not_send_hsts() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert "strict-transport-security" not in response.headers
