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
RUNTIME_ENV_PATH = Path("/etc/co-story/runtime.env")
_RUNTIME_KEYS = (
    "CO_STORY_AWS_REGION",
    "CO_STORY_BEDROCK_MODEL_ID",
    "CO_STORY_BEDROCK_GUARDRAIL_ID",
    "CO_STORY_BEDROCK_GUARDRAIL_VERSION",
    "CO_STORY_BEDROCK_MAX_TOKENS",
)


class _ConfigurationError(Exception):
    pass


def main(argv: list[str] | None = None, *, client: Any | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze one bounded Co-Story incident window.")
    parser.add_argument("--alarm-state", required=True, choices=("OK", "ALARM"))
    parser.add_argument("--service-state", required=True, choices=("active", "inactive"))
    arguments = parser.parse_args(argv)

    try:
        settings = _runtime_settings()
        region = settings["CO_STORY_AWS_REGION"]
        model_id = settings["CO_STORY_BEDROCK_MODEL_ID"]
        guardrail_id = settings["CO_STORY_BEDROCK_GUARDRAIL_ID"]
        guardrail_version = settings["CO_STORY_BEDROCK_GUARDRAIL_VERSION"]
        configured_tokens = _configured_tokens(settings["CO_STORY_BEDROCK_MAX_TOKENS"])
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


def _runtime_settings() -> dict[str, str]:
    settings = {
        key: os.environ[key].strip()
        for key in _RUNTIME_KEYS
        if os.environ.get(key, "").strip()
    }
    missing = set(_RUNTIME_KEYS) - set(settings)
    if missing:
        try:
            lines = RUNTIME_ENV_PATH.read_text(encoding="utf-8").splitlines()
        except OSError:
            raise _ConfigurationError("runtime_env") from None
        file_settings: dict[str, str] = {}
        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            key, separator, raw_value = line.partition("=")
            key = key.strip()
            if separator and key in _RUNTIME_KEYS:
                if key in file_settings:
                    raise _ConfigurationError(key)
                value = _unquote(raw_value.strip())
                if value:
                    file_settings[key] = value
        for key in missing:
            if key in file_settings:
                settings[key] = file_settings[key]
    if set(settings) != set(_RUNTIME_KEYS):
        raise _ConfigurationError("runtime_settings")
    return settings


def _configured_tokens(raw_value: str) -> int:
    try:
        value = int(raw_value)
    except ValueError:
        raise _ConfigurationError("CO_STORY_BEDROCK_MAX_TOKENS") from None
    if not 1 <= value <= 1200:
        raise _ConfigurationError("CO_STORY_BEDROCK_MAX_TOKENS")
    return value


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    raise SystemExit(main())
