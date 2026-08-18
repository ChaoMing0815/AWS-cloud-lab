from __future__ import annotations

import json
from typing import Any

from app.application.ports import Storyteller, StorytellerFailure
from app.domain.models import Room, World


MAX_TOKENS = 1200
MAX_NARRATIVE_LENGTH = 1200
_TONES = {
    "light_comedy",
    "workplace_satire",
    "slice_of_life",
    "mystery",
    "adventure",
    "sci_fi",
    "dark_fairy_tale",
    "custom",
}
_WORLD_SYSTEM = (
    "Return exactly one valid JSON object in Traditional Chinese. "
    "Do not add a preamble and Do not use Markdown code fences. "
    "The required fields and constraints are: title must contain 1-40 characters; "
    "premise must contain 50-500 characters; objective must contain 10-200 characters; "
    "opening_scene must contain 20-400 characters; core_obstacle must contain 10-200 "
    "characters; tone must exactly equal the requested tone; custom_tone must exactly "
    "equal the requested custom tone, or null when the requested tone is not custom; "
    "suggested_round_limit must be the integer 4, 6, or 8. "
    "Do not add any other fields or change canonical game state."
)
_NARRATIVE_SYSTEM = "Return only bounded narrative text; never change canonical game results."


class BedrockStoryteller(Storyteller):
    """Storyteller adapter over an injected Bedrock Runtime-compatible client."""

    def __init__(
        self,
        client: Any,
        model_id: str,
        guardrail_id: str,
        guardrail_version: str,
        max_tokens: int = MAX_TOKENS,
    ) -> None:
        if isinstance(max_tokens, bool) or not 1 <= max_tokens <= MAX_TOKENS:
            raise ValueError("max_tokens")
        self._client = client
        self._model_id = model_id
        self._guardrail_id = guardrail_id
        self._guardrail_version = guardrail_version
        self._max_tokens = max_tokens

    def generate_world(
        self,
        keywords: list[str],
        tone: str,
        custom_tone: str | None,
        supplemental_request: str | None,
    ) -> World:
        prompt = {
            "task": "generate_world_draft",
            "keywords": [_sanitize(value) for value in keywords],
            "tone": _sanitize(tone),
            "custom_tone": _sanitize(custom_tone) if custom_tone else None,
            "supplemental_request": _sanitize(supplemental_request)
            if supplemental_request
            else None,
        }
        text = self._converse(prompt, _WORLD_SYSTEM, maximum_length=None)
        return _world_from_draft(text, tone, custom_tone)

    def resolve_round(self, room: Room) -> str:
        current_results = [
            result for result in room.dice_results if result.round_number == room.round_number
        ]
        return self._converse(
            {
                "task": "resolve_round_narrative",
                "round_number": room.round_number,
                "world_title": room.world.story_title,
                "progress_points": room.progress_points,
                "danger_points": room.danger_points,
                "actions": [
                    {
                        "player_id": player.id,
                        "name": _sanitize(player.name),
                        "action": _sanitize(player.action),
                        "approach": _sanitize(player.action_approach),
                    }
                    for player in room.players
                ],
                "results": [
                    {
                        "player_id": result.player_id,
                        "result": result.result,
                        "progress_delta": result.progress_delta,
                        "danger_delta": result.danger_delta,
                    }
                    for result in current_results
                ],
            },
            _NARRATIVE_SYSTEM,
        )

    def resolve_ending(self, room: Room) -> str:
        return self._converse(
            {
                "task": "resolve_ending_narrative",
                "world_title": room.world.story_title,
                "ending_result": room.ending_result,
                "ending_cost": room.ending_cost,
            },
            _NARRATIVE_SYSTEM,
        )

    def _converse(
        self,
        prompt: dict[str, Any],
        system_instruction: str,
        maximum_length: int | None = MAX_NARRATIVE_LENGTH,
    ) -> str:
        try:
            response = self._client.converse(
                modelId=self._model_id,
                system=[{"text": system_instruction}],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "guardContent": {
                                    "text": {
                                        "text": json.dumps(prompt, ensure_ascii=False),
                                        "qualifiers": ["query"],
                                    }
                                }
                            }
                        ],
                    }
                ],
                inferenceConfig={"maxTokens": self._max_tokens, "temperature": 0},
                guardrailConfig={
                    "guardrailIdentifier": self._guardrail_id,
                    "guardrailVersion": self._guardrail_version,
                },
            )
        except Exception as error:
            raise StorytellerFailure(_failure_code(error)) from None

        if not isinstance(response, dict):
            raise StorytellerFailure("SCHEMA_INVALID")
        if response.get("stopReason") == "guardrail_intervened":
            raise StorytellerFailure("CONTENT_REJECTED")
        try:
            text = response["output"]["message"]["content"][0]["text"]
        except (KeyError, IndexError, TypeError):
            raise StorytellerFailure("SCHEMA_INVALID") from None
        if not isinstance(text, str):
            raise StorytellerFailure("SCHEMA_INVALID")
        text = _sanitize(text)
        if not text or (maximum_length is not None and len(text) > maximum_length):
            raise StorytellerFailure("SCHEMA_INVALID")
        return text


def _world_from_draft(text: str, requested_tone: str, requested_custom_tone: str | None) -> World:
    try:
        draft = json.loads(_unwrap_json_code_fence(text))
    except (TypeError, ValueError):
        raise StorytellerFailure("SCHEMA_INVALID") from None
    if not isinstance(draft, dict):
        raise StorytellerFailure("SCHEMA_INVALID")

    try:
        title = _bounded_text(draft["title"], 1, 40)
        premise = _bounded_text(draft["premise"], 50, 500)
        objective = _bounded_text(draft["objective"], 10, 200)
        opening_scene = _bounded_text(draft["opening_scene"], 20, 400)
        core_obstacle = _bounded_text(draft["core_obstacle"], 10, 200)
        tone = draft["tone"]
        custom_tone = draft["custom_tone"]
        suggested_round_limit = draft["suggested_round_limit"]
    except (KeyError, TypeError, ValueError):
        raise StorytellerFailure("SCHEMA_INVALID") from None

    if (
        tone not in _TONES
        or tone != requested_tone
        or suggested_round_limit not in {4, 6, 8}
        or isinstance(suggested_round_limit, bool)
    ):
        raise StorytellerFailure("SCHEMA_INVALID")
    if tone == "custom":
        try:
            custom_tone = _bounded_text(custom_tone, 1, 40)
        except (TypeError, ValueError):
            raise StorytellerFailure("SCHEMA_INVALID") from None
        if custom_tone != requested_custom_tone:
            raise StorytellerFailure("SCHEMA_INVALID")
    elif custom_tone is not None:
        raise StorytellerFailure("SCHEMA_INVALID")

    return World(
        name=title,
        story_title=title,
        premise=premise,
        objective=objective,
        opening_scene=opening_scene,
        core_obstacle=core_obstacle,
        tone=tone,
        custom_tone=custom_tone,
    )


def _unwrap_json_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if len(lines) < 3 or lines[0].lower() not in {"```", "```json"} or lines[-1] != "```":
        raise ValueError("json code fence")
    return "\n".join(lines[1:-1]).strip()


def _bounded_text(value: object, minimum: int, maximum: int) -> str:
    if not isinstance(value, str):
        raise TypeError("text")
    value = _sanitize(value)
    if not minimum <= len(value) <= maximum:
        raise ValueError("text")
    return value


def _sanitize(value: str) -> str:
    return value.replace("\x00", "").strip()


def _failure_code(error: Exception) -> str:
    response = getattr(error, "response", None)
    error_details = response.get("Error", {}) if isinstance(response, dict) else {}
    raw_code = error_details.get("Code", error.__class__.__name__)
    code = str(raw_code).lower()
    if "accessdenied" in code or "access_denied" in code:
        return "AUTHORIZATION_ERROR"
    if "validation" in code or "resourcenotfound" in code or "resource_not_found" in code:
        return "INVALID_MODEL"
    if "guardrail" in code or "content" in code or "reject" in code:
        return "CONTENT_REJECTED"
    if "throttl" in code:
        return "THROTTLED"
    if "timeout" in code:
        return "TIMEOUT"
    if "unavailable" in code or "internal" in code or "service" in code:
        return "TRANSIENT_SERVICE_ERROR"
    return "TRANSIENT_SERVICE_ERROR"
