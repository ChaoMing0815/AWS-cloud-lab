import importlib
import json

import pytest

from app.application.ports import StorytellerFailure
from app.domain.models import Room, World


MAX_BEDROCK_TOKENS = 1200


class FakeBedrockClient:
    def __init__(self, outcome: object) -> None:
        self.outcome = outcome
        self.calls: list[dict] = []

    def converse(self, **request):
        self.calls.append(request)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


class FakeBedrockError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.response = {"Error": {"Code": code, "Message": message}}


def bedrock_storyteller_class():
    """Keep the Red phase readable when the adapter module has not been created."""
    try:
        module = importlib.import_module("app.adapters.bedrock_storyteller")
    except ModuleNotFoundError as error:
        pytest.fail(
            "BedrockStoryteller adapter is required at app.adapters.bedrock_storyteller "
            f"(missing: {error.name})"
        )
    return module.BedrockStoryteller


def adapter(client: FakeBedrockClient, **overrides):
    settings = {
        "client": client,
        "model_id": "anthropic.claude-test-v1",
        "guardrail_id": "gr-story-safety",
        "guardrail_version": "7",
        "max_tokens": MAX_BEDROCK_TOKENS,
    }
    settings.update(overrides)
    return bedrock_storyteller_class()(
        **settings,
    )


def converse_response(text: str, **response_fields) -> dict:
    return {
        "output": {"message": {"content": [{"text": text}]}},
        **response_fields,
    }


def expected_world_payload(**overrides) -> dict:
    return {
        "title": "夜班盤點迷蹤",
        "premise": "凌晨盤點資料突然消失，夜班夥伴必須在店長抵達前找回被改寫的正確紀錄，同時查明是誰在監視器關閉時動過共用電腦。",
        "objective": "找回正確盤點紀錄並完成報表。",
        "opening_scene": "凌晨兩點，收銀機突然重開機，所有交班紀錄也變成一片空白。",
        "core_obstacle": "備份硬碟被鎖在倉庫深處，密碼只留下一半線索。",
        "tone": "mystery",
        "custom_tone": None,
        "suggested_round_limit": 6,
        **overrides,
    }


def expected_world(**overrides) -> World:
    payload = expected_world_payload(**overrides)
    return World(
        name=payload["title"],
        story_title=payload["title"],
        premise=payload["premise"],
        objective=payload["objective"],
        opening_scene=payload["opening_scene"],
        core_obstacle=payload["core_obstacle"],
        tone=payload["tone"],
        custom_tone=payload["custom_tone"],
    )


def resolution_room() -> Room:
    return Room(
        id="room-1",
        room_code="BEDRK1",
        status="RESOLVING",
        version=3,
        round_number=2,
        world=World(
            name="夜班盤點迷蹤",
            story_title="夜班盤點迷蹤",
            premise="凌晨盤點資料突然消失，夜班夥伴必須在店長抵達前找回被改寫的正確紀錄，同時查明是誰在監視器關閉時動過共用電腦。",
            objective="找回正確盤點紀錄並完成報表。",
        ),
        progress_points=2,
        danger_points=1,
        ending_result="PARTIAL_SUCCESS",
        ending_cost="SIGNIFICANT",
    )


def test_generate_world_uses_injected_converse_client_with_bounded_tokens_guardrail_and_safe_prompt() -> None:
    client = FakeBedrockClient(converse_response(json.dumps(expected_world_payload())))

    generated = adapter(client).generate_world(
        keywords=[" 夜班 ", "便利商店", "盤點\x00"],
        tone="mystery",
        custom_tone=None,
        supplemental_request="  請保留玩家可編輯空間。\x00 ",
    )

    assert generated == expected_world()
    assert len(client.calls) == 1
    request = client.calls[0]
    assert request["modelId"] == "anthropic.claude-test-v1"
    assert request["inferenceConfig"]["maxTokens"] == MAX_BEDROCK_TOKENS
    assert request["guardrailConfig"] == {
        "guardrailIdentifier": "gr-story-safety",
        "guardrailVersion": "7",
    }
    assert request["system"]
    assert request["messages"][0]["role"] == "user"
    prompt = request["messages"][0]["content"][0]["text"]
    assert "\x00" not in prompt
    assert " 夜班 " not in prompt


@pytest.mark.parametrize("invalid_max_tokens", [0, -1, MAX_BEDROCK_TOKENS + 1])
def test_constructor_rejects_token_limits_outside_the_fixed_cost_boundary(invalid_max_tokens: int) -> None:
    client = FakeBedrockClient(converse_response(json.dumps(expected_world_payload())))

    with pytest.raises(ValueError):
        adapter(client, max_tokens=invalid_max_tokens)


def test_generate_world_maps_world_draft_title_and_ignores_unknown_fields() -> None:
    payload = expected_world_payload()
    payload["unknown_model_field"] = {"progress_delta": 99, "danger_delta": -99}
    client = FakeBedrockClient(converse_response(json.dumps(payload)))

    generated = adapter(client).generate_world(
        keywords=["夜班", "便利商店", "盤點"],
        tone="mystery",
        custom_tone=None,
        supplemental_request=None,
    )

    assert generated == expected_world()
    assert not hasattr(generated, "suggested_round_limit")
    assert not hasattr(generated, "unknown_model_field")


def test_generate_world_accepts_a_consistent_custom_tone() -> None:
    payload = expected_world_payload(tone="custom", custom_tone="冷調寫實")
    client = FakeBedrockClient(converse_response(json.dumps(payload)))

    generated = adapter(client).generate_world(
        keywords=["夜班", "便利商店", "盤點"],
        tone="custom",
        custom_tone="冷調寫實",
        supplemental_request=None,
    )

    assert generated == expected_world(tone="custom", custom_tone="冷調寫實")


@pytest.mark.parametrize(
    "text",
    [
        "not json",
        json.dumps({"title": "缺少必要欄位"}),
        json.dumps(expected_world_payload(tone="light_comedy")),
        json.dumps(expected_world_payload(title="")),
        json.dumps(expected_world_payload(title="標" * 41)),
        json.dumps(expected_world_payload(premise="短" * 49)),
        json.dumps(expected_world_payload(premise="長" * 501)),
        json.dumps(expected_world_payload(objective="短" * 9)),
        json.dumps(expected_world_payload(objective="長" * 201)),
        json.dumps(expected_world_payload(opening_scene="短" * 19)),
        json.dumps(expected_world_payload(opening_scene="長" * 401)),
        json.dumps(expected_world_payload(core_obstacle="短" * 9)),
        json.dumps(expected_world_payload(core_obstacle="長" * 201)),
        json.dumps(expected_world_payload(tone="custom", custom_tone=None)),
        json.dumps(expected_world_payload(tone="custom", custom_tone="長" * 41)),
        json.dumps(expected_world_payload(tone="mystery", custom_tone="不應保留")),
        json.dumps(expected_world_payload(suggested_round_limit=3)),
        json.dumps(expected_world_payload(suggested_round_limit=5)),
        json.dumps(expected_world_payload(suggested_round_limit=9)),
    ],
    ids=[
        "not-json",
        "missing-fields",
        "tone-mismatch",
        "title-underlength",
        "title-overlength",
        "premise-underlength",
        "premise-overlength",
        "objective-underlength",
        "objective-overlength",
        "opening-underlength",
        "opening-overlength",
        "obstacle-underlength",
        "obstacle-overlength",
        "custom-tone-missing",
        "custom-tone-overlength",
        "non-custom-tone-value",
        "suggested-round-limit-under",
        "suggested-round-limit-between",
        "suggested-round-limit-over",
    ],
)
def test_invalid_world_draft_output_is_a_safe_schema_failure(text: str) -> None:
    client = FakeBedrockClient(converse_response(text))

    with pytest.raises(StorytellerFailure) as captured:
        adapter(client).generate_world(
            keywords=["夜班", "便利商店", "盤點"],
            tone="mystery",
            custom_tone=None,
            supplemental_request=None,
        )

    assert captured.value.code == "SCHEMA_INVALID"
    assert str(captured.value) == "SCHEMA_INVALID"
    assert text not in str(captured.value)


@pytest.mark.parametrize(
    ("error_code", "expected_failure"),
    [
        ("ThrottlingException", "THROTTLED"),
        ("ServiceUnavailableException", "TRANSIENT_SERVICE_ERROR"),
        ("ModelTimeoutException", "TIMEOUT"),
    ],
)
def test_retryable_bedrock_errors_map_to_safe_storyteller_failures(
    error_code: str, expected_failure: str
) -> None:
    secret_prompt = "玩家的未公開故事內容"
    client = FakeBedrockClient(FakeBedrockError(error_code, f"AWS details: {secret_prompt}"))

    with pytest.raises(StorytellerFailure) as captured:
        adapter(client).generate_world(
            keywords=["夜班", "便利商店", "盤點"],
            tone="mystery",
            custom_tone=None,
            supplemental_request=secret_prompt,
        )

    assert captured.value.code == expected_failure
    assert captured.value.retryable is True
    assert str(captured.value) == expected_failure
    assert secret_prompt not in str(captured.value)


@pytest.mark.parametrize(
    ("error_code", "expected_failure"),
    [
        ("AccessDeniedException", "AUTHORIZATION_ERROR"),
        ("ValidationException", "INVALID_MODEL"),
        ("ResourceNotFoundException", "INVALID_MODEL"),
    ],
)
def test_configuration_errors_are_non_retryable_and_do_not_leak_aws_details(
    error_code: str, expected_failure: str
) -> None:
    secret_detail = "model ARN and account details must remain private"
    client = FakeBedrockClient(FakeBedrockError(error_code, secret_detail))

    with pytest.raises(StorytellerFailure) as captured:
        adapter(client).resolve_round(resolution_room())

    assert captured.value.code == expected_failure
    assert captured.value.retryable is False
    assert str(captured.value) == expected_failure
    assert secret_detail not in str(captured.value)


@pytest.mark.parametrize("error_code", ["GuardrailIntervenedException", "ContentRejectedException"])
def test_guardrail_or_content_rejection_is_non_retryable_and_does_not_leak_details(error_code: str) -> None:
    secret_response = "模型回覆全文不得外洩"
    client = FakeBedrockClient(FakeBedrockError(error_code, secret_response))

    with pytest.raises(StorytellerFailure) as captured:
        adapter(client).resolve_round(resolution_room())

    assert captured.value.code == "CONTENT_REJECTED"
    assert captured.value.retryable is False
    assert str(captured.value) == "CONTENT_REJECTED"
    assert secret_response not in str(captured.value)


def test_converse_guardrail_stop_reason_is_non_retryable_content_rejection() -> None:
    client = FakeBedrockClient(
        converse_response(
            "guardrail response must not become a story",
            stopReason="guardrail_intervened",
        )
    )

    with pytest.raises(StorytellerFailure) as captured:
        adapter(client).resolve_round(resolution_room())

    assert captured.value.code == "CONTENT_REJECTED"
    assert captured.value.retryable is False
    assert str(captured.value) == "CONTENT_REJECTED"


def test_round_and_ending_are_text_only_bounded_and_leave_canonical_room_state_unchanged() -> None:
    room = resolution_room()
    before = (room.progress_points, room.danger_points, room.ending_result, room.ending_cost)
    client = FakeBedrockClient(converse_response("固定規則已結算；故事只描述本回合後果。"))
    storyteller = adapter(client)

    round_text = storyteller.resolve_round(room)
    ending_text = storyteller.resolve_ending(room)

    assert round_text == "固定規則已結算；故事只描述本回合後果。"
    assert ending_text == "固定規則已結算；故事只描述本回合後果。"
    assert len(round_text) <= 1200
    assert len(ending_text) <= 1200
    assert (room.progress_points, room.danger_points, room.ending_result, room.ending_cost) == before
    assert len(client.calls) == 2


@pytest.mark.parametrize("method_name", ["resolve_round", "resolve_ending"])
def test_overlong_narrative_output_is_schema_failure(method_name: str) -> None:
    client = FakeBedrockClient(converse_response("x" * 1201))

    with pytest.raises(StorytellerFailure) as captured:
        getattr(adapter(client), method_name)(resolution_room())

    assert captured.value.code == "SCHEMA_INVALID"
