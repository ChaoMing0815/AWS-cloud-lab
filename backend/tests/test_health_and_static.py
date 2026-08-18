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
    assert 'href="/styles.css"' in response.text
    assert 'src="/src/composition/bootstrap.js"' in response.text
    assert response.headers["Cache-Control"] == "no-store"


def test_frontend_module_is_not_reused_across_release_updates() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/src/composition/bootstrap.js")

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"


def test_fastapi_serves_app_shell_for_demo_route() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/demo")

    assert response.status_code == 200
    assert 'id="landingPage"' in response.text
    assert 'id="gamePage"' in response.text


def test_fastapi_serves_game_rules_page_shell() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/rules")

    assert response.status_code == 200
    assert 'id="rulesPage"' in response.text
    assert "回合怎麼進行" in response.text


def test_fastapi_serves_app_shell_for_host_setup_route() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/host/setup")

    assert response.status_code == 200
    assert 'id="landingPage"' in response.text
    assert 'id="worldForm"' in response.text
    assert 'src="/runtime-config.js"' in response.text
    assert 'src="/src/composition/bootstrap.js"' in response.text


def test_fastapi_serves_app_shell_for_lobby_deep_link() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/room/ABCD23/lobby")

    assert response.status_code == 200
    assert 'id="landingPage"' in response.text
    assert 'id="gamePage"' in response.text


def test_fastapi_serves_app_shell_for_play_and_ending_deep_links() -> None:
    with TestClient(create_app()) as client:
        play = client.get("/room/ABCD23/play")
        ending = client.get("/room/ABCD23/ending")

    assert play.status_code == 200
    assert ending.status_code == 200
    assert 'id="gamePage"' in play.text
    assert 'id="endingPanel"' in ending.text


def test_unknown_frontend_route_returns_helpful_html_404() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/this-route-does-not-exist")

    assert response.status_code == 404
    assert "找不到此頁面" in response.text
    assert 'href="/"' in response.text
