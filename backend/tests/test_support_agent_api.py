import json

from fastapi.testclient import TestClient

from app.main import create_app


RULES_PATH = "/api/v1/support/rules:lookup"
REPORTS_PATH = "/api/v1/support/reports:draft"
INVALID_REQUEST = {
    "error": {"code": "REQUEST_VALIDATION_FAILED", "message": "請檢查輸入內容。"}
}


def _create_player_session(client: TestClient, key: str = "support-room") -> dict:
    response = client.post(
        "/api/v1/rooms",
        json={"nickname": "房主"},
        headers={"Idempotency-Key": key},
    )
    assert response.status_code == 201
    return response.json()


def _serialized(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False).casefold()


def test_rules_lookup_is_anonymous_and_returns_only_grounded_citations() -> None:
    with TestClient(create_app()) as client:
        response = client.post(RULES_PATH, json={"message": "星火可以怎麼使用？"})

    assert response.status_code == 200
    assert response.json() == {
        "status": "supported",
        "answer": "角色初始有 1 點星火、上限 3；看見原始骰子後，每次行動最多消耗 1 點讓最終總值 +1。最終結果仍為失敗時獲得 1 點，星火不能轉讓、共享或追溯使用。",
        "citations": [
            {
                "ruleId": "spark-usage",
                "title": "星火的使用與取得",
                "sourceSection": "正式 MVP Spec §10 星火",
                "sourceVersion": "mvp-spec-2026-08-27",
            }
        ],
    }


def test_rules_lookup_has_fixed_unsupported_response_and_cannot_switch_to_write() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            RULES_PATH,
            json={"message": "問題回報：交易裝備的按鈕壞了。"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "unsupported",
        "answer": "目前版本的規則資料沒有足夠證據回答這個問題。",
        "citations": [],
    }
    assert app.state.support_report_repository.count == 0


def test_rules_lookup_rejects_unknown_fields_and_normalized_length_boundaries() -> None:
    with TestClient(create_app()) as client:
        exact = client.post(RULES_PATH, json={"message": " 星 " + "火" * 498})
        empty = client.post(RULES_PATH, json={"message": " \n\t "})
        too_long = client.post(RULES_PATH, json={"message": "星" * 501})
        forged = client.post(
            RULES_PATH,
            json={"message": "星火怎麼用？", "route": "draft_problem_report"},
        )

    assert exact.status_code == 200
    for response in (empty, too_long, forged):
        assert response.status_code == 422
        assert response.json() == INVALID_REQUEST


def test_rules_lookup_rejects_oversized_json_before_support_side_effects() -> None:
    app = create_app()
    body = json.dumps({"message": "星火", "padding": "x" * 1100})
    with TestClient(app) as client:
        response = client.post(
            RULES_PATH,
            content=body,
            headers={"Content-Type": "application/json"},
        )

    assert response.status_code == 422
    assert response.json() == INVALID_REQUEST
    assert app.state.support_rule_knowledge_base.lookup_count == 0


def test_report_draft_requires_current_player_session_and_player_csrf() -> None:
    app = create_app()
    with TestClient(app) as anonymous:
        missing_session = anonymous.post(
            REPORTS_PATH,
            json={"description": "問題回報：畫面沒有更新。"},
            headers={"X-CSRF-Token": "not-a-real-token"},
        )

    with TestClient(app) as client:
        room = _create_player_session(client)
        missing_csrf = client.post(
            REPORTS_PATH,
            json={"description": "問題回報：畫面沒有更新。"},
        )
        wrong_csrf = client.post(
            REPORTS_PATH,
            json={"description": "問題回報：畫面沒有更新。"},
            headers={"X-CSRF-Token": "wrong-player-csrf"},
        )
        client.cookies.delete("co_story_player")
        host_only = client.post(
            REPORTS_PATH,
            json={"description": "問題回報：畫面沒有更新。"},
            headers={"X-CSRF-Token": room["session"]["hostCsrfToken"]},
        )

    assert missing_session.status_code == 401
    assert missing_session.json() == {
        "error": {
            "code": "SESSION_NOT_FOUND",
            "message": "目前的遊戲工作階段已失效。",
        }
    }
    for response in (missing_csrf, wrong_csrf):
        assert response.status_code == 403
        assert response.json() == {
            "error": {"code": "CSRF_FAILED", "message": "CSRF 驗證失敗。"}
        }
    assert host_only.status_code == 401
    assert host_only.json() == {
        "error": {
            "code": "PLAYER_SESSION_REQUIRED",
            "message": "需要有效的玩家工作階段。",
        }
    }
    assert app.state.support_report_repository.count == 0


def test_report_draft_derives_identity_and_returns_only_safe_local_draft_fields() -> None:
    app = create_app()
    description = "問題回報：畫面錯誤，password=FAKE_PASSWORD_MARKER"
    with TestClient(app) as client:
        room = _create_player_session(client, "support-safe-report")
        response = client.post(
            REPORTS_PATH,
            json={"description": description},
            headers={"X-CSRF-Token": room["session"]["csrfToken"]},
        )

    assert response.status_code == 201
    payload = response.json()
    assert set(payload) == {
        "reportId",
        "category",
        "summary",
        "reproductionSteps",
        "expectedBehavior",
        "actualBehavior",
        "requiresHumanConfirmation",
        "submissionStatus",
    }
    assert payload["requiresHumanConfirmation"] is True
    assert payload["submissionStatus"] == "local_draft_only"
    serialized = _serialized(payload)
    for forbidden in (
        "fake_password_marker",
        "identity",
        "idempotency",
        "fingerprint",
        "cookie",
        "csrf",
        "postgresql://",
    ):
        assert forbidden not in serialized
    assert app.state.support_report_repository.count == 1


def test_report_draft_rejects_client_identity_and_state_fields() -> None:
    app = create_app()
    forbidden_fields = {
        "playerId": "forged-player",
        "reporterIdentity": "forged-identity",
        "reporterIdentityHash": "a" * 64,
        "reportId": "draft-0000000000000000",
        "submissionStatus": "submitted",
        "requiresHumanConfirmation": False,
    }
    with TestClient(app) as client:
        room = _create_player_session(client, "support-forged-report")
        for field, value in forbidden_fields.items():
            response = client.post(
                REPORTS_PATH,
                json={"description": "問題回報：操作失敗。", field: value},
                headers={"X-CSRF-Token": room["session"]["csrfToken"]},
            )
            assert response.status_code == 422
            assert response.json() == INVALID_REQUEST

    assert app.state.support_report_repository.count == 0


def test_report_draft_normalized_boundaries_and_oversized_body_fail_closed() -> None:
    app = create_app()
    with TestClient(app) as client:
        room = _create_player_session(client, "support-report-boundary")
        headers = {"X-CSRF-Token": room["session"]["csrfToken"]}
        empty = client.post(REPORTS_PATH, json={"description": " \n "}, headers=headers)
        too_long = client.post(
            REPORTS_PATH,
            json={"description": "問" * 2001},
            headers=headers,
        )
        oversized = client.post(
            REPORTS_PATH,
            content=json.dumps({"description": "問題", "padding": "x" * 4100}),
            headers={**headers, "Content-Type": "application/json"},
        )

    for response in (empty, too_long, oversized):
        assert response.status_code == 422
        assert response.json() == INVALID_REQUEST
    assert app.state.support_report_repository.count == 0


def test_rules_and_reports_have_independent_bounded_limits_before_side_effects() -> None:
    app = create_app()
    with TestClient(app) as client:
        room = _create_player_session(client, "support-rate-limit")
        csrf = {"X-CSRF-Token": room["session"]["csrfToken"]}
        rule_responses = [
            client.post(RULES_PATH, json={"message": "星火可以怎麼使用？"})
            for _ in range(11)
        ]
        report_responses = [
            client.post(
                REPORTS_PATH,
                json={"description": f"問題回報：第 {index} 個問題。"},
                headers=csrf,
            )
            for index in range(4)
        ]

    assert [response.status_code for response in rule_responses] == [200] * 10 + [429]
    assert [response.status_code for response in report_responses] == [201] * 3 + [429]
    assert rule_responses[-1].json() == {
        "error": {
            "code": "SUPPORT_RATE_LIMITED",
            "message": "操作過於頻繁，請稍後再試。",
        }
    }
    assert report_responses[-1].json() == rule_responses[-1].json()
    assert app.state.support_rule_knowledge_base.lookup_count == 10
    assert app.state.support_report_repository.count == 3


def test_support_app_shell_is_available_without_editing_web_assets() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/support")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
