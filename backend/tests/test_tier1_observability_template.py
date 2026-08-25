import json
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]
TEMPLATE = ROOT / "infra/cloudformation/tier1-observability.yaml"


def _template() -> dict:
    assert TEMPLATE.is_file(), "Tier 1 observability CloudFormation template 尚未建立"
    return yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))


def test_template_contains_only_the_bounded_observability_resources() -> None:
    template = _template()
    resources = template["Resources"]

    assert template["AWSTemplateFormatVersion"] == "2010-09-09"
    assert set(template) == {
        "AWSTemplateFormatVersion",
        "Description",
        "Parameters",
        "Resources",
        "Outputs",
    }
    assert {resource["Type"] for resource in resources.values()} == {
        "AWS::Logs::LogGroup",
        "AWS::Logs::MetricFilter",
        "AWS::IAM::ManagedPolicy",
        "AWS::CloudWatch::Alarm",
        "AWS::CloudWatch::Dashboard",
    }
    assert len(resources) == 12


def test_application_log_group_is_fixed_short_lived_and_deletable() -> None:
    resource = _template()["Resources"]["ApplicationLogGroup"]

    assert resource["DeletionPolicy"] == "Delete"
    assert resource["UpdateReplacePolicy"] == "Delete"
    assert resource["Properties"] == {
        "LogGroupName": "/co-story/tier1/application",
        "LogGroupClass": "STANDARD",
        "RetentionInDays": 7,
        "Tags": [
            {"Key": "Name", "Value": "co-story-tier1-application"},
            {"Key": "Project", "Value": "co-story"},
            {"Key": "Tier", "Value": "1"},
        ],
    }


def test_system_log_group_is_fixed_short_lived_and_deletable() -> None:
    resource = _template()["Resources"]["SystemLogGroup"]

    assert resource["DeletionPolicy"] == "Delete"
    assert resource["UpdateReplacePolicy"] == "Delete"
    assert resource["Properties"]["LogGroupName"] == "/co-story/tier1/system"
    assert resource["Properties"]["RetentionInDays"] == 7


def test_parameters_bind_policy_to_the_existing_app_role_and_instance() -> None:
    parameters = _template()["Parameters"]

    assert parameters == {
        "AppRoleName": {
            "Type": "String",
            "Default": "AWSFinalProjectAppRole",
            "AllowedPattern": "^AWSFinalProject[A-Za-z0-9+=,.@_-]+$",
            "Description": (
                "Existing EC2 application role created by co-story-tier0-compute."
            ),
        },
        "AppInstanceId": {
            "Type": "AWS::EC2::Instance::Id",
            "Description": (
                "Existing application instance created by co-story-tier0-compute."
            ),
        },
    }


def test_app_policy_writes_only_fixed_log_streams_and_bounded_system_metrics() -> None:
    policy = _template()["Resources"]["ApplicationLogWritePolicy"]["Properties"]
    application_group_arn = {
        "Fn::Sub": (
            "arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:"
            "log-group:/co-story/tier1/application"
        )
    }
    system_group_arn = {
        "Fn::Sub": (
            "arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:"
            "log-group:/co-story/tier1/system"
        )
    }
    stream_arn = {
        "Fn::Sub": (
            "arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:"
            "log-group:/co-story/tier1/application:log-stream:${AppInstanceId}"
        )
    }

    assert set(policy) == {
        "ManagedPolicyName",
        "Description",
        "Roles",
        "PolicyDocument",
    }
    assert policy["ManagedPolicyName"] == "AWSFinalProjectTier1ApplicationLogWrite"
    assert policy["Description"] == (
        "Lets the existing Co-Story instance write only its Tier 1 application "
        "log stream."
    )
    assert policy["Roles"] == [{"Ref": "AppRoleName"}]
    statements = policy["PolicyDocument"]["Statement"]
    assert statements[:2] == [
        {
            "Sid": "DescribeApplicationLogStreams",
            "Effect": "Allow",
            "Action": "logs:DescribeLogStreams",
            "Resource": [application_group_arn, system_group_arn],
        },
        {
            "Sid": "WriteSingleInstanceApplicationLogStream",
            "Effect": "Allow",
            "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
            "Resource": stream_arn,
        },
    ]
    assert statements[2]["Action"] == ["logs:CreateLogStream", "logs:PutLogEvents"]
    assert statements[2]["Resource"] == {
        "Fn::Sub": (
            "arn:${AWS::Partition}:logs:${AWS::Region}:${AWS::AccountId}:"
            "log-group:/co-story/tier1/system:log-stream:${AppInstanceId}"
        )
    }
    assert statements[3] == {
        "Sid": "PublishBoundedSystemMetrics",
        "Effect": "Allow",
        "Action": "cloudwatch:PutMetricData",
        "Resource": "*",
        "Condition": {
            "StringEquals": {"cloudwatch:namespace": "CoStory/Tier1/System"}
        },
    }


def test_metric_filter_counts_only_json_request_5xx_without_dimensions() -> None:
    resource = _template()["Resources"]["Application5xxMetricFilter"]

    assert resource["DeletionPolicy"] == "Delete"
    assert resource["UpdateReplacePolicy"] == "Delete"
    assert resource["Properties"] == {
        "FilterName": "co-story-tier1-application-5xx",
        "FilterPattern": "{ ($.status >= 500) && ($.status <= 599) }",
        "LogGroupName": {"Ref": "ApplicationLogGroup"},
        "MetricTransformations": [
            {
                "DefaultValue": 0,
                "MetricName": "Application5xx",
                "MetricNamespace": "CoStory/Tier1",
                "MetricValue": "1",
                "Unit": "Count",
            }
        ],
    }


def test_alarm_triggers_on_one_5xx_in_one_minute_without_actions() -> None:
    resource = _template()["Resources"]["Application5xxAlarm"]

    assert resource["DeletionPolicy"] == "Delete"
    assert resource["UpdateReplacePolicy"] == "Delete"
    assert resource["Properties"] == {
        "ActionsEnabled": False,
        "AlarmDescription": "Co-Story application emitted at least one 5xx in one minute.",
        "AlarmName": "co-story-tier1-application-5xx",
        "ComparisonOperator": "GreaterThanOrEqualToThreshold",
        "DatapointsToAlarm": 1,
        "EvaluationPeriods": 1,
        "MetricName": "Application5xx",
        "Namespace": "CoStory/Tier1",
        "Period": 60,
        "Statistic": "Sum",
        "Threshold": 1,
        "TreatMissingData": "notBreaching",
        "Unit": "Count",
    }


def test_metric_filters_cover_latency_tokens_retry_and_fallback() -> None:
    resources = _template()["Resources"]
    expected = {
        "ApplicationLatencyMetricFilter": ("ApplicationLatencyMs", "$.latency_ms", "Milliseconds"),
        "StorytellerLatencyMetricFilter": ("StorytellerLatencyMs", "$.latency_ms", "Milliseconds"),
        "StorytellerInputTokenMetricFilter": ("StorytellerInputTokens", "$.input_tokens", "Count"),
        "StorytellerOutputTokenMetricFilter": ("StorytellerOutputTokens", "$.output_tokens", "Count"),
        "StorytellerRetryMetricFilter": ("StorytellerRetries", "$.retry_count", "Count"),
        "StorytellerFallbackMetricFilter": ("StorytellerFallbacks", "$.fallback_count", "Count"),
    }
    for logical_id, (metric_name, value, unit) in expected.items():
        props = resources[logical_id]["Properties"]
        assert props["LogGroupName"] == {"Ref": "ApplicationLogGroup"}
        transformation = props["MetricTransformations"][0]
        assert transformation["MetricName"] == metric_name
        assert transformation["MetricNamespace"] == "CoStory/Tier1"
        assert transformation["MetricValue"] == value
        assert transformation["Unit"] == unit


def test_dashboard_visualizes_application_ai_and_system_signals() -> None:
    dashboard = _template()["Resources"]["Tier1Dashboard"]["Properties"]
    assert dashboard["DashboardName"] == "co-story-tier1-observability"
    body = json.loads(dashboard["DashboardBody"]["Fn::Sub"])
    rendered = json.dumps(body)
    for signal in (
        "Application5xx",
        "ApplicationLatencyMs",
        "StorytellerLatencyMs",
        "StorytellerInputTokens",
        "StorytellerOutputTokens",
        "StorytellerRetries",
        "StorytellerFallbacks",
        "EstimatedBedrockCostUsd",
        "mem_used_percent",
        "disk_used_percent",
    ):
        assert signal in rendered


def test_template_grants_no_log_group_management_or_unrelated_services() -> None:
    template = _template()
    rendered = TEMPLATE.read_text(encoding="utf-8")

    assert "logs:CreateLogGroup" not in rendered
    assert "logs:PutRetentionPolicy" not in rendered
    assert "CloudWatchAgentServerPolicy" not in rendered
    assert rendered.count("Resource: '*'") == 1
    assert "cloudwatch:namespace" in rendered
    assert 'Resource: "*"' not in rendered
    assert all(
        not resource["Type"].startswith(("AWS::SNS::", "AWS::SSM::", "AWS::Lambda::"))
        for resource in template["Resources"].values()
    )


def test_template_outputs_fixed_observability_names() -> None:
    assert _template()["Outputs"] == {
        "ApplicationLogGroupName": {"Value": {"Ref": "ApplicationLogGroup"}},
        "SystemLogGroupName": {"Value": {"Ref": "SystemLogGroup"}},
        "DashboardName": {"Value": "co-story-tier1-observability"},
    }
