from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]
TEMPLATE = ROOT / "infra/cloudformation/tier1-ssm-health-check.yaml"


def _template() -> dict:
    assert TEMPLATE.is_file(), "Tier 1 SSM health-check CloudFormation template 尚未建立"
    return yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))


def _document() -> dict:
    return _template()["Resources"]["HealthCheckDocument"]


def test_template_creates_only_one_rollback_safe_command_document() -> None:
    template = _template()

    assert template["AWSTemplateFormatVersion"] == "2010-09-09"
    assert set(template) == {
        "AWSTemplateFormatVersion",
        "Description",
        "Resources",
        "Outputs",
    }
    assert set(template["Resources"]) == {"HealthCheckDocument"}
    assert _document()["Type"] == "AWS::SSM::Document"
    assert _document()["DeletionPolicy"] == "Delete"
    assert _document()["UpdateReplacePolicy"] == "Delete"


def test_document_has_a_fixed_linux_command_contract_and_no_parameters() -> None:
    properties = _document()["Properties"]
    content = properties["Content"]

    assert set(properties) == {
        "Name",
        "DocumentType",
        "DocumentFormat",
        "TargetType",
        "UpdateMethod",
        "Content",
        "Tags",
    }
    assert properties["Name"] == "CoStoryHealthCheck"
    assert properties["DocumentType"] == "Command"
    assert properties["DocumentFormat"] == "YAML"
    assert properties["TargetType"] == "/AWS::EC2::Instance"
    assert properties["UpdateMethod"] == "NewVersion"
    assert properties["Tags"] == [
        {"Key": "Name", "Value": "co-story-tier1-health-check"},
        {"Key": "Project", "Value": "co-story"},
        {"Key": "Tier", "Value": "1"},
    ]
    assert content["schemaVersion"] == "2.2"
    assert content["parameters"] == {}
    assert set(content) == {
        "schemaVersion",
        "description",
        "parameters",
        "mainSteps",
    }


def test_health_check_runs_only_the_fixed_service_live_and_ready_checks() -> None:
    steps = _document()["Properties"]["Content"]["mainSteps"]

    assert steps == [
        {
            "action": "aws:runShellScript",
            "name": "CheckCoStoryHealth",
            "precondition": {"StringEquals": ["platformType", "Linux"]},
            "inputs": {
                "timeoutSeconds": "30",
                "runCommand": [
                    "#!/bin/bash",
                    "set -euo pipefail",
                    "readonly runtime_env='/etc/co-story/runtime.env'",
                    "readonly health_base_url='http://127.0.0.1:8000'",
                    'test -r "$runtime_env"',
                    (
                        'host_header="$(awk -F= \'$1 == "CO_STORY_ALLOWED_HOSTS" '
                        '{ split($2, hosts, ","); print hosts[1]; exit }\' '
                        '"$runtime_env")"'
                    ),
                    (
                        'case "$host_header" in \'\'|*[!A-Za-z0-9._:-]*) '
                        "printf 'health_check=invalid_host_configuration\\n' >&2; "
                        "exit 1 ;; esac"
                    ),
                    "systemctl is-active --quiet co-story.service",
                    (
                        'curl --fail --silent --show-error --max-time 5 '
                        '--header "Host: $host_header" "$health_base_url/live" '
                        ">/dev/null"
                    ),
                    (
                        'curl --fail --silent --show-error --max-time 5 '
                        '--header "Host: $host_header" "$health_base_url/ready" '
                        ">/dev/null"
                    ),
                    "printf 'service=active\\nlive=200\\nready=200\\n'",
                ],
            },
        }
    ]


def test_document_cannot_accept_commands_or_expose_runtime_configuration() -> None:
    rendered = TEMPLATE.read_text(encoding="utf-8")
    commands = "\n".join(
        _document()["Properties"]["Content"]["mainSteps"][0]["inputs"][
            "runCommand"
        ]
    )

    assert "{{" not in rendered
    assert "AWS-RunShellScript" not in rendered
    assert "source " not in commands
    assert "printenv" not in commands
    assert "cat /etc/co-story" not in commands
    assert "SecretString" not in rendered
    assert "SecureString" not in rendered
    assert all(
        forbidden not in commands
        for forbidden in (
            "systemctl start",
            "systemctl stop",
            "systemctl restart",
            "sudo ",
            "aws ",
            "curl http://",
            "curl https://",
            "rm ",
        )
    )


def test_template_outputs_only_the_document_name() -> None:
    assert _template()["Outputs"] == {
        "HealthCheckDocumentName": {"Value": {"Ref": "HealthCheckDocument"}}
    }
