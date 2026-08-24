from __future__ import annotations

import json
from typing import Any

from app.application.incident_analysis import (
    IncidentAnalysisFailure,
    validate_incident_report,
)


MAX_INCIDENT_TOKENS = 600
_SYSTEM_INSTRUCTION = (
    "Analyze only the supplied sanitized operational facts. Return exactly one JSON "
    "object in Traditional Chinese with keys summary, probable_cause, evidence, "
    "recommended_action, and requires_human_approval. evidence must contain 1-5 short "
    "strings. recommended_action must be exactly one of NO_ACTION, RUN_HEALTH_CHECK, "
    "RESTART_APPLICATION, or CHECK_DATABASE. requires_human_approval must be true. "
    "Never invent missing evidence, emit credentials, write shell commands, execute an "
    "action, or add fields."
)


class BedrockIncidentAdvisor:
    def __init__(
        self,
        client: Any,
        model_id: str,
        guardrail_id: str,
        guardrail_version: str,
        max_tokens: int = MAX_INCIDENT_TOKENS,
    ) -> None:
        if isinstance(max_tokens, bool) or not 1 <= max_tokens <= MAX_INCIDENT_TOKENS:
            raise ValueError("max_tokens")
        self._client = client
        self._model_id = model_id
        self._guardrail_id = guardrail_id
        self._guardrail_version = guardrail_version
        self._max_tokens = max_tokens

    def advise(self, facts: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client.converse(
                modelId=self._model_id,
                system=[{"text": _SYSTEM_INSTRUCTION}],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "guardContent": {
                                    "text": {
                                        "text": json.dumps(
                                            facts,
                                            ensure_ascii=False,
                                            separators=(",", ":"),
                                        ),
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
        except Exception:
            raise IncidentAnalysisFailure("MODEL_ERROR") from None

        if not isinstance(response, dict):
            raise IncidentAnalysisFailure("SCHEMA_INVALID")
        if response.get("stopReason") == "guardrail_intervened":
            raise IncidentAnalysisFailure("CONTENT_REJECTED")
        try:
            text = response["output"]["message"]["content"][0]["text"]
            report = json.loads(text)
        except (KeyError, IndexError, TypeError, ValueError):
            raise IncidentAnalysisFailure("SCHEMA_INVALID") from None
        return validate_incident_report(report)
