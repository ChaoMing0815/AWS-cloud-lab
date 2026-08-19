from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]
TEMPLATE = ROOT / "infra/cloudformation/tier0-compute.yaml"


def _template() -> dict:
    assert TEMPLATE.is_file(), "Tier 0 EC2＋SSM CloudFormation template 尚未建立"
    return yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))


def test_compute_template_contains_only_instance_and_ssm_role_resources() -> None:
    template = _template()
    resource_types = {
        resource["Type"] for resource in template["Resources"].values()
    }

    assert template["AWSTemplateFormatVersion"] == "2010-09-09"
    assert resource_types == {
        "AWS::IAM::Role",
        "AWS::IAM::InstanceProfile",
        "AWS::EC2::Instance",
    }
    assert "AWS::EC2::KeyPair" not in resource_types
    assert "AWS::EC2::EIP" not in resource_types
    assert "AWS::EC2::SecurityGroup" not in resource_types


def test_app_role_trusts_only_ec2_and_grants_only_ssm_core() -> None:
    role = _template()["Resources"]["AppRole"]["Properties"]
    trust = role["AssumeRolePolicyDocument"]["Statement"]

    assert role["RoleName"] == "AWSFinalProjectAppRole"
    assert role["PermissionsBoundary"] == {
        "Fn::Sub": "arn:${AWS::Partition}:iam::aws:policy/PowerUserAccess"
    }
    assert trust == [
        {
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }
    ]
    assert role["ManagedPolicyArns"] == [
        {
            "Fn::Sub": (
                "arn:${AWS::Partition}:iam::aws:policy/"
                "AmazonSSMManagedInstanceCore"
            )
        }
    ]


def test_bedrock_runtime_parameters_pin_model_and_numeric_guardrail_version() -> None:
    parameters = _template()["Parameters"]

    assert parameters["BedrockModelId"] == {
        "Type": "String",
        "Default": "amazon.nova-lite-v1:0",
        "AllowedValues": ["amazon.nova-lite-v1:0"],
    }
    assert parameters["BedrockGuardrailId"] == {
        "Type": "String",
        "AllowedPattern": "^[a-z0-9]+$",
    }
    assert parameters["BedrockGuardrailVersion"] == {
        "Type": "String",
        "Default": "1",
        "AllowedValues": ["1"],
    }


def test_app_role_allows_only_pinned_bedrock_runtime_with_guardrail_v1() -> None:
    role = _template()["Resources"]["AppRole"]["Properties"]
    model_arn = {
        "Fn::Sub": (
            "arn:${AWS::Partition}:bedrock:${AWS::Region}::foundation-model/"
            "${BedrockModelId}"
        )
    }
    guardrail_arn = {
        "Fn::Sub": (
            "arn:${AWS::Partition}:bedrock:${AWS::Region}:${AWS::AccountId}:"
            "guardrail/${BedrockGuardrailId}"
        )
    }
    versioned_guardrail_arn = {
        "Fn::Sub": (
            "arn:${AWS::Partition}:bedrock:${AWS::Region}:${AWS::AccountId}:"
            "guardrail/${BedrockGuardrailId}:${BedrockGuardrailVersion}"
        )
    }
    profile_regions = [
        "ap-south-1",
        "ap-northeast-3",
        "ap-northeast-2",
        "ap-southeast-1",
        "ap-southeast-2",
        "ap-northeast-1",
    ]
    profile_arns = [
        {
            "Fn::Sub": (
                f"arn:${{AWS::Partition}}:bedrock:{region}:"
                "${AWS::AccountId}:guardrail-profile/apac.guardrail.v1:0"
            )
        }
        for region in profile_regions
    ]

    assert role["Policies"] == [
        {
            "PolicyName": "CoStoryTier0BedrockRuntime",
            "PolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AllowPinnedNovaLiteWithGuardrailV1",
                        "Effect": "Allow",
                        "Action": "bedrock:InvokeModel",
                        "Resource": model_arn,
                        "Condition": {
                            "StringEquals": {
                                "bedrock:GuardrailIdentifier": (
                                    versioned_guardrail_arn
                                )
                            }
                        },
                    },
                    {
                        "Sid": "DenyNovaLiteWithoutGuardrailV1",
                        "Effect": "Deny",
                        "Action": "bedrock:InvokeModel",
                        "Resource": model_arn,
                        "Condition": {
                            "StringNotEquals": {
                                "bedrock:GuardrailIdentifier": (
                                    versioned_guardrail_arn
                                )
                            }
                        },
                    },
                    {
                        "Sid": "ApplyPinnedGuardrailAcrossApacProfile",
                        "Effect": "Allow",
                        "Action": "bedrock:ApplyGuardrail",
                        "Resource": [guardrail_arn, *profile_arns],
                    },
                ],
            },
        }
    ]


def test_instance_uses_bounded_amazon_linux_arm64_compute() -> None:
    template = _template()
    parameters = template["Parameters"]
    instance = template["Resources"]["AppInstance"]["Properties"]

    assert parameters["LatestAmiId"] == {
        "Type": "AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>",
        "Default": (
            "/aws/service/ami-amazon-linux-latest/"
            "al2023-ami-kernel-default-arm64"
        ),
    }
    assert instance["ImageId"] == {"Ref": "LatestAmiId"}
    assert instance["InstanceType"] == "t4g.micro"
    assert instance["CreditSpecification"] == {"CPUCredits": "standard"}
    assert instance["Monitoring"] is False


def test_instance_has_no_ssh_or_bootstrap_secret_surface() -> None:
    instance = _template()["Resources"]["AppInstance"]["Properties"]

    assert "KeyName" not in instance
    assert "UserData" not in instance
    assert instance["IamInstanceProfile"] == {"Ref": "AppInstanceProfile"}
    assert instance["NetworkInterfaces"] == [
        {
            "AssociatePublicIpAddress": True,
            "DeviceIndex": "0",
            "GroupSet": [{"Ref": "AppSecurityGroupId"}],
            "SubnetId": {"Ref": "PublicAppSubnetId"},
        }
    ]


def test_instance_requires_imdsv2_and_encrypted_deletable_root_volume() -> None:
    instance = _template()["Resources"]["AppInstance"]["Properties"]

    assert instance["MetadataOptions"] == {
        "HttpEndpoint": "enabled",
        "HttpTokens": "required",
        "HttpPutResponseHopLimit": 1,
        "InstanceMetadataTags": "disabled",
    }
    assert instance["BlockDeviceMappings"] == [
        {
            "DeviceName": "/dev/xvda",
            "Ebs": {
                "DeleteOnTermination": True,
                "Encrypted": True,
                "VolumeSize": 8,
                "VolumeType": "gp3",
            },
        }
    ]
