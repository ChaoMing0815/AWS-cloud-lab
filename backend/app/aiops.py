from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from app.adapters.bedrock_incident_advisor import (
    MAX_INCIDENT_TOKENS,
    BedrockIncidentAdvisor,
)
from app.application.incident_analysis import IncidentAnalysisFailure, IncidentAnalyzer


APPLICATION_LOG_PATH = Path("/var/log/co-story/application.jsonl")


class _ConfigurationError(Exception):
    pass


def main(argv: list[str] | None = None, *, client: Any | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze one bounded Co-Story incident window.")
    parser.add_argument("--alarm-state", required=True, choices=("OK", "ALARM"))
    parser.add_argument("--service-state", required=True, choices=("active", "inactive"))
    arguments = parser.parse_args(argv)

    try:
        region = _required_setting("CO_STORY_AWS_REGION")
        model_id = _required_setting("CO_STORY_BEDROCK_MODEL_ID")
        guardrail_id = _required_setting("CO_STORY_BEDROCK_GUARDRAIL_ID")
        guardrail_version = _required_setting("CO_STORY_BEDROCK_GUARDRAIL_VERSION")
        configured_tokens = _configured_tokens()
    except _ConfigurationError:
        _print_json({"error": {"code": "CONFIGURATION_ERROR"}})
        return 2

    if client is None:
        import boto3
        from botocore.config import Config

        client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            config=Config(
                read_timeout=30,
                connect_timeout=5,
                retries={"max_attempts": 0},
            ),
        )

    advisor = BedrockIncidentAdvisor(
        client=client,
        model_id=model_id,
        guardrail_id=guardrail_id,
        guardrail_version=guardrail_version,
        max_tokens=min(configured_tokens, MAX_INCIDENT_TOKENS),
    )
    try:
        report = IncidentAnalyzer(advisor).analyze(
            APPLICATION_LOG_PATH,
            alarm_state=arguments.alarm_state,
            service_state=arguments.service_state,
        )
    except IncidentAnalysisFailure as error:
        _print_json({"error": {"code": error.code}})
        return 3
    except (OSError, ValueError):
        _print_json({"error": {"code": "INPUT_ERROR"}})
        return 4

    _print_json(report)
    return 0


def _required_setting(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise _ConfigurationError(name)
    return value


def _configured_tokens() -> int:
    raw_value = _required_setting("CO_STORY_BEDROCK_MAX_TOKENS")
    try:
        value = int(raw_value)
    except ValueError:
        raise _ConfigurationError("CO_STORY_BEDROCK_MAX_TOKENS") from None
    if not 1 <= value <= 1200:
        raise _ConfigurationError("CO_STORY_BEDROCK_MAX_TOKENS")
    return value


def _print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    raise SystemExit(main())
