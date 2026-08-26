from __future__ import annotations

import json
from typing import Any

from app.application.incident_analysis import (
    IncidentAnalysisFailure,
    validate_incident_report,
)


MAX_INCIDENT_TOKENS = 600
_REPORT_TOOL_NAME = "submit_incident_report"
_SYSTEM_INSTRUCTION = (
    "Analyze only the supplied sanitized operational facts. Call "
    "submit_incident_report exactly once using Traditional Chinese. Never invent "
    "missing evidence, emit credentials, write shell commands, execute an action, or "
    "call any other tool."
)
_REPORT_TOOL = {
    "toolSpec": {
        "name": _REPORT_TOOL_NAME,
        "description": (
            "Return one bounded incident analysis for human review. This tool records "
            "a report only and does not execute the recommended action."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Short Traditional Chinese incident summary.",
                    },
                    "probable_cause": {
                        "type": "string",
                        "description": (
                            "Most probable cause supported only by supplied facts."
                        ),
                    },
                    "evidence": {
                        "type": "array",
                        "description": "One to five short evidence statements.",
                        "items": {"type": "string"},
                    },
                    "recommended_action": {
                        "type": "string",
                        "description": "One allowlisted action for human approval.",
                        "enum": [
                            "NO_ACTION",
                            "RUN_HEALTH_CHECK",
                            "RESTART_APPLICATION",
                            "CHECK_DATABASE",
                        ],
                    },
                    "requires_human_approval": {
                        "type": "boolean",
                        "description": "Must be true for every report.",
                    },
                },
                "required": [
                    "summary",
                    "probable_cause",
                    "evidence",
                    "recommended_action",
                    "requires_human_approval",
                ],
            }
        },
    }
}


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
                toolConfig={
                    "tools": [_REPORT_TOOL],
                    "toolChoice": {"tool": {"name": _REPORT_TOOL_NAME}},
                },
            )
        except Exception:
            raise IncidentAnalysisFailure("MODEL_ERROR") from None

        if not isinstance(response, dict):
            raise IncidentAnalysisFailure("SCHEMA_INVALID")
        if response.get("stopReason") == "guardrail_intervened":
            raise IncidentAnalysisFailure("CONTENT_REJECTED")
        try:
            content = response["output"]["message"]["content"]
            if response.get("stopReason") != "tool_use" or len(content) != 1:
                raise ValueError("report_tool_content")
            block = content[0]
            if set(block) != {"toolUse"}:
                raise ValueError("report_tool_block")
            tool_use = block["toolUse"]
            if set(tool_use) != {"toolUseId", "name", "input"}:
                raise ValueError("report_tool_shape")
            if (
                not isinstance(tool_use["toolUseId"], str)
                or not tool_use["toolUseId"]
                or tool_use["name"] != _REPORT_TOOL_NAME
            ):
                raise ValueError("report_tool_identity")
            report = tool_use["input"]
        except (KeyError, IndexError, TypeError, ValueError):
            raise IncidentAnalysisFailure("SCHEMA_INVALID") from None
        return validate_incident_report(report)
