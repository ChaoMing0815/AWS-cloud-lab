import importlib
import importlib.util
import json
from pathlib import Path


def _module():
    spec = importlib.util.find_spec("app.aiops")
    assert spec is not None, "Tier 1 AIOps runtime entrypoint 尚未建立"
    return importlib.import_module("app.aiops")


class FakeBedrockClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def converse(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        return {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "content": [
                        {
                            "text": json.dumps(
                                {
                                    "summary": "單筆受控 500 已恢復。",
                                    "probable_cause": "事件路徑標示為 incident simulation。",
                                    "evidence": ["服務 active，Alarm 已回到 OK"],
                                    "recommended_action": "RUN_HEALTH_CHECK",
                                    "requires_human_approval": True,
                                },
                                ensure_ascii=False,
                                separators=(",", ":"),
                            )
                        }
                    ]
                }
            },
        }


def _runtime_environment(monkeypatch) -> None:
    values = {
        "CO_STORY_AWS_REGION": "ap-northeast-1",
        "CO_STORY_BEDROCK_MODEL_ID": "model-id",
        "CO_STORY_BEDROCK_GUARDRAIL_ID": "guardrail-id",
        "CO_STORY_BEDROCK_GUARDRAIL_VERSION": "1",
        "CO_STORY_BEDROCK_MAX_TOKENS": "1200",
        "DATABASE_URL": "postgresql://never-print-this",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def test_aiops_entrypoint_reads_fixed_safe_log_and_calls_model_once(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    module = _module()
    log_path = tmp_path / "application.jsonl"
    log_path.write_text(
        json.dumps(
            {
                "request_id": "synthetic",
                "method": "GET",
                "path": "/tier1/incident-simulation",
                "status": 500,
                "latency_ms": 0,
            },
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "APPLICATION_LOG_PATH", log_path)
    _runtime_environment(monkeypatch)
    client = FakeBedrockClient()

    result = module.main(
        ["--alarm-state", "OK", "--service-state", "active"],
        client=client,
    )

    assert result == 0
    assert len(client.calls) == 1
    assert client.calls[0]["inferenceConfig"] == {"maxTokens": 600, "temperature": 0}
    output = capsys.readouterr().out
    report = json.loads(output)
    assert report["recommended_action"] == "RUN_HEALTH_CHECK"
    assert report["requires_human_approval"] is True
    assert "never-print-this" not in output
    assert "command" not in report


def test_aiops_entrypoint_fails_closed_without_runtime_configuration(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    module = _module()
    log_path = tmp_path / "application.jsonl"
    log_path.write_text("", encoding="utf-8")
    monkeypatch.setattr(module, "APPLICATION_LOG_PATH", log_path)
    for key in (
        "CO_STORY_AWS_REGION",
        "CO_STORY_BEDROCK_MODEL_ID",
        "CO_STORY_BEDROCK_GUARDRAIL_ID",
        "CO_STORY_BEDROCK_GUARDRAIL_VERSION",
        "CO_STORY_BEDROCK_MAX_TOKENS",
    ):
        monkeypatch.delenv(key, raising=False)

    result = module.main(
        ["--alarm-state", "OK", "--service-state", "active"],
        client=FakeBedrockClient(),
    )

    assert result == 2
    assert json.loads(capsys.readouterr().out) == {
        "error": {"code": "CONFIGURATION_ERROR"}
    }
