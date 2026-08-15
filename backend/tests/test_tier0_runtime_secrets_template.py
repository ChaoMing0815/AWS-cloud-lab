from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]
TEMPLATE = ROOT / "infra/cloudformation/tier0-runtime-secrets.yaml"


def _template() -> dict:
    assert TEMPLATE.is_file(), "Tier 0 runtime secret CloudFormation template 尚未建立"
    return yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))


def _mapping_keys(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            key
            for child in value.values()
            for key in _mapping_keys(child)
        }
    if isinstance(value, list):
        return {key for child in value for key in _mapping_keys(child)}
    return set()


def test_runtime_secret_template_has_one_generated_secret_and_two_bounded_policies() -> None:
    template = _template()
    resources = template["Resources"]

    assert template["AWSTemplateFormatVersion"] == "2010-09-09"
    assert {resource["Type"] for resource in resources.values()} == {
        "AWS::SecretsManager::Secret",
        "AWS::IAM::ManagedPolicy",
    }
    assert sum(
        resource["Type"] == "AWS::SecretsManager::Secret"
        for resource in resources.values()
    ) == 1
    assert sum(
        resource["Type"] == "AWS::IAM::ManagedPolicy"
        for resource in resources.values()
    ) == 2


def test_application_database_secret_is_generated_without_plaintext_or_fixed_name() -> None:
    secret_resource = _template()["Resources"]["AppDbSecret"]
    secret = secret_resource["Properties"]
    generation = secret["GenerateSecretString"]

    assert "Name" not in secret
    assert generation["SecretStringTemplate"] == '{"username":"co_story_app"}'
    assert generation["GenerateStringKey"] == "password"
    assert generation["PasswordLength"] >= 32
    assert generation["ExcludePunctuation"] is True
    assert "SecretString" not in secret
    assert secret_resource["DeletionPolicy"] == "Delete"
    assert secret_resource["UpdateReplacePolicy"] == "Delete"


def test_permanent_policy_reads_only_the_generated_application_secret() -> None:
    template = _template()
    policy = template["Resources"]["AppDbSecretReadPolicy"]["Properties"]

    assert policy["Roles"] == [{"Ref": "AppRoleName"}]
    assert policy["PolicyDocument"]["Statement"] == [
        {
            "Sid": "ReadApplicationDatabaseSecret",
            "Effect": "Allow",
            "Action": [
                "secretsmanager:DescribeSecret",
                "secretsmanager:GetSecretValue",
            ],
            "Resource": {"Ref": "AppDbSecret"},
        }
    ]


def test_bootstrap_policy_is_conditional_and_reads_only_the_rds_master_secret() -> None:
    template = _template()
    resource = template["Resources"]["MigrationBootstrapSecretReadPolicy"]
    policy = resource["Properties"]

    assert template["Parameters"]["EnableMigrationBootstrapAccess"]["AllowedValues"] == [
        "true",
        "false",
    ]
    assert resource["Condition"] == "MigrationBootstrapAccessEnabled"
    assert template["Conditions"]["MigrationBootstrapAccessEnabled"] == {
        "Fn::Equals": [
            {"Ref": "EnableMigrationBootstrapAccess"},
            "true",
        ]
    }
    assert policy["Roles"] == [{"Ref": "AppRoleName"}]
    assert policy["PolicyDocument"]["Statement"] == [
        {
            "Sid": "ReadRdsMasterSecretForMigrationBootstrap",
            "Effect": "Allow",
            "Action": [
                "secretsmanager:DescribeSecret",
                "secretsmanager:GetSecretValue",
            ],
            "Resource": {"Ref": "MasterSecretArn"},
        }
    ]


def test_template_exposes_identifiers_but_never_secret_values() -> None:
    template = _template()

    assert template["Outputs"] == {
        "AppDbSecretArn": {"Value": {"Ref": "AppDbSecret"}},
        "MigrationBootstrapAccess": {
            "Value": {"Ref": "EnableMigrationBootstrapAccess"}
        },
    }
    serialized = TEMPLATE.read_text(encoding="utf-8").lower()
    assert "SecretString" not in _mapping_keys(template)
    assert "MasterUserPassword" not in _mapping_keys(template)
    assert "resource: '*'" not in serialized
    assert 'resource: "*"' not in serialized
