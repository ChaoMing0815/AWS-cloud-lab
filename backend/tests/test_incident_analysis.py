import importlib
import importlib.util
import json
from pathlib import Path

import pytest


def _analysis_module():
    spec = importlib.util.find_spec("app.application.incident_analysis")
    assert spec is not None, "Tier 1 incident analysis module 尚未建立"
    return importlib.import_module("app.application.incident_analysis")


def _adapter_module():
    spec = importlib.util.find_spec("app.adapters.bedrock_incident_advisor")
    assert spec is not None, "Tier 1 Bedrock incident advisor 尚未建立"
    return importlib.import_module("app.adapters.bedrock_incident_advisor")


class RecordingAdvisor:
    def __init__(self, report: dict | None = None) -> None:
        self.calls: list[dict] = []
        self.report = report or {
            "summary": "偵測到單筆受控 500，之後沒有持續錯誤。",
            "probable_cause": "這是已標記的 incident simulation event。",
            "evidence": ["單筆 /tier1/incident-simulation status 500"],
            "recommended_action": "RUN_HEALTH_CHECK",
            "requires_human_approval": True,
        }

    def advise(self, facts: dict) -> dict:
        self.calls.append(facts)
        return self.report


def _write_jsonl(path: Path, events: list[dict | str]) -> None:
    path.write_text(
        "".join(
            f"{json.dumps(event, ensure_ascii=False, separators=(',', ':'))}\n"
            if isinstance(event, dict)
            else f"{event}\n"
            for event in events
        ),
        encoding="utf-8",
    )


def test_incident_analyzer_sends_only_bounded_allowlisted_facts(tmp_path: Path) -> None:
    module = _analysis_module()
    log_path = tmp_path / "application.jsonl"
    _write_jsonl(
        log_path,
        [
            {
                "request_id": "ready-before",
                "method": "GET",
                "path": "/api/v1/ready",
                "status": 200,
                "latency_ms": 12,
            },
            {
                "request_id": "forged",
                "method": "GET",
                "path": "/private?token=never-forward",
                "status": 500,
                "latency_ms": 1,
                "secret": "never-forward-this",
            },
            "not-json raw-cookie=never-forward-this-either",
            {
                "request_id": "synthetic",
                "method": "GET",
                "path": "/tier1/incident-simulation",
                "status": 500,
                "latency_ms": 0,
            },
            {"operation": "resolve_round", "failure_code": "TIMEOUT"},
        ],
    )
    advisor = RecordingAdvisor()

    report = module.IncidentAnalyzer(advisor, max_lines=4).analyze(
        log_path,
        alarm_state="OK",
        service_state="active",
    )

    assert len(advisor.calls) == 1
    facts = advisor.calls[0]
    assert facts == {
        "alarm_state": "OK",
        "service_state": "active",
        "window": {
            "scanned_lines": 4,
            "accepted_events": 2,
            "discarded_lines": 2,
        },
        "request_summary": {
            "total": 1,
            "status_5xx": 1,
            "latest_5xx": [
                {
                    "method": "GET",
                    "path": "/tier1/incident-simulation",
                    "status": 500,
                    "latency_ms": 0,
                }
            ],
        },
        "storyteller_failures": [
            {"operation": "resolve_round", "failure_code": "TIMEOUT"}
        ],
    }
    assert "never-forward" not in json.dumps(facts, ensure_ascii=False)
    assert report["recommended_action"] == "RUN_HEALTH_CHECK"
    assert report["requires_human_approval"] is True


@pytest.mark.parametrize(
    ("alarm_state", "service_state"),
    [("UNKNOWN", "active"), ("OK", "restarting")],
)
def test_incident_analyzer_rejects_unbounded_runtime_states_before_model_call(
    tmp_path: Path,
    alarm_state: str,
    service_state: str,
) -> None:
    module = _analysis_module()
    log_path = tmp_path / "application.jsonl"
    _write_jsonl(log_path, [])
    advisor = RecordingAdvisor()

    with pytest.raises(ValueError):
        module.IncidentAnalyzer(advisor).analyze(
            log_path,
            alarm_state=alarm_state,
            service_state=service_state,
        )

    assert advisor.calls == []


def test_incident_analyzer_rejects_symlink_before_reading_or_model_call(
    tmp_path: Path,
) -> None:
    module = _analysis_module()
    real_path = tmp_path / "real.jsonl"
    _write_jsonl(real_path, [])
    link_path = tmp_path / "application.jsonl"
    link_path.symlink_to(real_path)
    advisor = RecordingAdvisor()

    with pytest.raises(ValueError, match="log_path"):
        module.IncidentAnalyzer(advisor).analyze(
            link_path,
            alarm_state="OK",
            service_state="active",
        )

    assert advisor.calls == []


def test_incident_analyzer_discards_exact_shape_events_with_unhashable_values(
    tmp_path: Path,
) -> None:
    module = _analysis_module()
    log_path = tmp_path / "application.jsonl"
    _write_jsonl(
        log_path,
        [
            {
                "request_id": "forged-request",
                "method": ["GET"],
                "path": "/api/v1/ready",
                "status": 200,
                "latency_ms": 1,
            },
            {"operation": ["resolve_round"], "failure_code": "TIMEOUT"},
        ],
    )
    advisor = RecordingAdvisor()

    module.IncidentAnalyzer(advisor).analyze(
        log_path,
        alarm_state="OK",
        service_state="active",
    )

    assert advisor.calls[0]["window"] == {
        "scanned_lines": 2,
        "accepted_events": 0,
        "discarded_lines": 2,
    }


@pytest.mark.parametrize(
    "report",
    [
        {
            "summary": "摘要",
            "probable_cause": "原因",
            "evidence": ["證據"],
            "recommended_action": "RUN_ARBITRARY_SHELL",
            "requires_human_approval": True,
        },
        {
            "summary": "摘要",
            "probable_cause": "原因",
            "evidence": ["證據"],
            "recommended_action": "NO_ACTION",
            "requires_human_approval": False,
        },
    ],
)
def test_incident_analyzer_rejects_unsafe_advisor_report(
    tmp_path: Path,
    report: dict,
) -> None:
    module = _analysis_module()
    log_path = tmp_path / "application.jsonl"
    _write_jsonl(log_path, [])

    with pytest.raises(module.IncidentAnalysisFailure, match="SCHEMA_INVALID"):
        module.IncidentAnalyzer(RecordingAdvisor(report)).analyze(
            log_path,
            alarm_state="OK",
            service_state="active",
        )


class FakeBedrockClient:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.calls: list[dict] = []

    def converse(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        return self.response


def _bedrock_response(report: dict) -> dict:
    return {
        "stopReason": "tool_use",
        "output": {
            "message": {
                "content": [
                    {
                        "toolUse": {
                            "toolUseId": "incident-report-1",
                            "name": "submit_incident_report",
                            "input": report,
                        }
                    }
                ]
            }
        },
    }


def test_bedrock_incident_advisor_makes_one_bounded_guarded_call() -> None:
    module = _adapter_module()
    report = RecordingAdvisor().report
    client = FakeBedrockClient(_bedrock_response(report))
    advisor = module.BedrockIncidentAdvisor(
        client=client,
        model_id="model-id",
        guardrail_id="guardrail-id",
        guardrail_version="1",
        max_tokens=600,
    )
    facts = {
        "alarm_state": "OK",
        "service_state": "active",
        "window": {"scanned_lines": 1, "accepted_events": 1, "discarded_lines": 0},
        "request_summary": {"total": 1, "status_5xx": 1, "latest_5xx": []},
        "storyteller_failures": [],
    }

    assert advisor.advise(facts) == report
    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["modelId"] == "model-id"
    assert call["inferenceConfig"] == {"maxTokens": 600, "temperature": 0}
    assert call["guardrailConfig"] == {
        "guardrailIdentifier": "guardrail-id",
        "guardrailVersion": "1",
    }
    assert call["toolConfig"]["toolChoice"] == {
        "tool": {"name": "submit_incident_report"}
    }
    tool_spec = call["toolConfig"]["tools"][0]["toolSpec"]
    assert tool_spec["name"] == "submit_incident_report"
    assert tool_spec["inputSchema"]["json"]["required"] == [
        "summary",
        "probable_cause",
        "evidence",
        "recommended_action",
        "requires_human_approval",
    ]
    prompt = call["messages"][0]["content"][0]["guardContent"]["text"]
    assert prompt["qualifiers"] == ["query"]
    assert json.loads(prompt["text"]) == facts


def test_bedrock_incident_advisor_rejects_text_even_when_it_contains_valid_json() -> None:
    analysis = _analysis_module()
    module = _adapter_module()
    report = RecordingAdvisor().report
    response = {
        "stopReason": "end_turn",
        "output": {
            "message": {
                "content": [
                    {
                        "text": json.dumps(
                            report,
                            ensure_ascii=False,
                            separators=(",", ":"),
                        )
                    }
                ]
            }
        },
    }
    advisor = module.BedrockIncidentAdvisor(
        client=FakeBedrockClient(response),
        model_id="model-id",
        guardrail_id="guardrail-id",
        guardrail_version="1",
    )

    with pytest.raises(analysis.IncidentAnalysisFailure, match="SCHEMA_INVALID"):
        advisor.advise({"alarm_state": "OK"})


@pytest.mark.parametrize(
    "content",
    [
        [
            {
                "toolUse": {
                    "toolUseId": "wrong-tool",
                    "name": "restart_application",
                    "input": RecordingAdvisor().report,
                }
            }
        ],
        [
            {
                "toolUse": {
                    "toolUseId": "report-1",
                    "name": "submit_incident_report",
                    "input": RecordingAdvisor().report,
                }
            },
            {"text": "extra output"},
        ],
    ],
)
def test_bedrock_incident_advisor_rejects_non_exact_report_tool_content(
    content: list[dict],
) -> None:
    analysis = _analysis_module()
    module = _adapter_module()
    advisor = module.BedrockIncidentAdvisor(
        client=FakeBedrockClient(
            {
                "stopReason": "tool_use",
                "output": {"message": {"content": content}},
            }
        ),
        model_id="model-id",
        guardrail_id="guardrail-id",
        guardrail_version="1",
    )

    with pytest.raises(analysis.IncidentAnalysisFailure, match="SCHEMA_INVALID"):
        advisor.advise({"alarm_state": "OK"})


@pytest.mark.parametrize(
    "report",
    [
        {
            "summary": "摘要",
            "probable_cause": "原因",
            "evidence": ["證據"],
            "recommended_action": "RESTART_EVERYTHING",
            "requires_human_approval": True,
        },
        {
            "summary": "摘要",
            "probable_cause": "原因",
            "evidence": ["證據"],
            "recommended_action": "NO_ACTION",
            "requires_human_approval": True,
            "command": "rm -rf /",
        },
    ],
)
def test_bedrock_incident_advisor_rejects_unbounded_output(report: dict) -> None:
    analysis = _analysis_module()
    module = _adapter_module()
    advisor = module.BedrockIncidentAdvisor(
        client=FakeBedrockClient(_bedrock_response(report)),
        model_id="model-id",
        guardrail_id="guardrail-id",
        guardrail_version="1",
    )

    with pytest.raises(analysis.IncidentAnalysisFailure, match="SCHEMA_INVALID"):
        advisor.advise({"alarm_state": "OK"})
