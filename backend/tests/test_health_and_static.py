from fastapi.testclient import TestClient

from app.main import create_app


def test_health_reports_mock_storyteller() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "co-story-api",
        "storyteller": "mock",
    }


def test_fastapi_serves_same_origin_frontend() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "共演計劃" in response.text
    assert 'src="src/composition/bootstrap.js"' in response.text


def test_fastapi_serves_app_shell_for_demo_route() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/demo")

    assert response.status_code == 200
    assert 'id="landingPage"' in response.text
    assert 'id="gamePage"' in response.text
