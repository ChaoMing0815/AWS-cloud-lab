import json
from pathlib import Path


ROOT = Path(__file__).parents[2]
AGENT_CONFIG = ROOT / "ops/cloudwatch/amazon-cloudwatch-agent.json"
RUNTIME_ENV_EXAMPLE = ROOT / "ops/runtime/co-story.env.example"
SYSTEMD_UNIT = ROOT / "ops/systemd/co-story.service"
CANDIDATE_SYSTEMD_UNIT = ROOT / "ops/systemd/co-story-candidate@.service"


def test_cloudwatch_agent_collects_only_bounded_application_and_system_jsonl() -> None:
    assert AGENT_CONFIG.is_file(), "CloudWatch Agent application log config 尚未建立"
    config = json.loads(AGENT_CONFIG.read_text(encoding="utf-8"))

    collect_list = config["logs"]["logs_collected"]["files"]["collect_list"]
    assert collect_list == [
        {
            "file_path": "/var/log/co-story/application.jsonl",
            "log_group_name": "/co-story/tier1/application",
            "log_stream_name": "{instance_id}",
            "encoding": "utf-8",
            "timezone": "UTC",
        },
        {
            "file_path": "/var/log/co-story/system.jsonl",
            "log_group_name": "/co-story/tier1/system",
            "log_stream_name": "{instance_id}",
            "encoding": "utf-8",
            "timezone": "UTC",
        },
    ]
    assert config["metrics"] == {
        "namespace": "CoStory/Tier1/System",
        "append_dimensions": {"InstanceId": "${aws:InstanceId}"},
        "aggregation_dimensions": [["InstanceId"]],
        "metrics_collected": {
            "mem": {
                "measurement": ["mem_used_percent"],
                "metrics_collection_interval": 60,
            },
            "disk": {
                "measurement": ["used_percent"],
                "resources": ["/"],
                "drop_device": True,
                "drop_original_metrics": ["used_percent"],
                "metrics_collection_interval": 60,
            },
        },
    }
    assert "drop_original_metrics" not in config["metrics"]["metrics_collected"]["mem"]

    rendered = json.dumps(config, sort_keys=True).lower()
    for forbidden_source in (
        "/var/log/messages",
        "/var/log/secure",
        "auth.log",
        "nginx",
        "access.log",
        "error.log",
        "*",
    ):
        assert forbidden_source not in rendered


def test_runtime_produces_the_exact_file_collected_by_the_agent() -> None:
    environment = RUNTIME_ENV_EXAMPLE.read_text(encoding="utf-8")
    unit = SYSTEMD_UNIT.read_text(encoding="utf-8")
    candidate_unit = CANDIDATE_SYSTEMD_UNIT.read_text(encoding="utf-8")

    assert (
        "CO_STORY_APPLICATION_LOG_PATH=/var/log/co-story/application.jsonl"
        in environment
    )
    assert "LogsDirectory=co-story" in unit
    assert "LogsDirectoryMode=0750" in unit
    assert "Environment=CO_STORY_APPLICATION_LOG_PATH" not in unit
    assert "LogsDirectory=co-story" in candidate_unit
    assert "LogsDirectoryMode=0750" in candidate_unit
    assert (
        "Environment=CO_STORY_APPLICATION_LOG_PATH="
        "/var/log/co-story/candidate.jsonl" in candidate_unit
    )
