from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]
TEMPLATE = ROOT / "infra/cloudformation/tier0-rds.yaml"


def _template() -> dict:
    assert TEMPLATE.is_file(), "Tier 0 RDS CloudFormation template 尚未建立"
    return yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))


def test_tier0_rds_template_contains_only_private_database_resources() -> None:
    template = _template()
    resources = template["Resources"]

    assert template["AWSTemplateFormatVersion"] == "2010-09-09"
    assert {resource["Type"] for resource in resources.values()} == {
        "AWS::RDS::DBSubnetGroup",
        "AWS::RDS::DBInstance",
    }
    subnet_group = resources["DbSubnetGroup"]["Properties"]
    assert subnet_group["SubnetIds"] == [
        {"Ref": "PrivateDbSubnetAId"},
        {"Ref": "PrivateDbSubnetBId"},
    ]


def test_tier0_rds_template_uses_free_plan_sized_single_az_postgresql() -> None:
    database = _template()["Resources"]["Database"]["Properties"]

    assert database["Engine"] == "postgres"
    assert database["EngineVersion"] == "18.3-R2"
    assert database["EngineLifecycleSupport"] == (
        "open-source-rds-extended-support-disabled"
    )
    assert database["DBInstanceClass"] == "db.t4g.micro"
    assert database["MultiAZ"] is False
    assert database["AllocatedStorage"] == "20"
    assert database["StorageType"] == "gp2"
    assert "MaxAllocatedStorage" not in database


def test_tier0_rds_template_keeps_database_private_and_encrypted() -> None:
    database = _template()["Resources"]["Database"]["Properties"]

    assert database["PubliclyAccessible"] is False
    assert database["StorageEncrypted"] is True
    assert database["VPCSecurityGroups"] == [{"Ref": "DbSecurityGroupId"}]
    assert database["DBSubnetGroupName"] == {"Ref": "DbSubnetGroup"}
    assert database["Port"] == 5432


def test_tier0_rds_template_manages_master_secret_without_hardcoded_password() -> None:
    database = _template()["Resources"]["Database"]["Properties"]

    assert database["MasterUsername"] == "postgres"
    assert database["ManageMasterUserPassword"] is True
    assert "MasterUserPassword" not in database
    assert _template()["Outputs"]["MasterSecretArn"]["Value"] == {
        "Fn::GetAtt": ["Database", "MasterUserSecret.SecretArn"]
    }


def test_tier0_rds_template_bounds_backups_insights_and_deletion() -> None:
    database_resource = _template()["Resources"]["Database"]
    database = database_resource["Properties"]

    assert database["BackupRetentionPeriod"] == 1
    assert database["DeleteAutomatedBackups"] is True
    assert database["DeletionProtection"] is False
    assert database["AutoMinorVersionUpgrade"] is True
    assert database["EnablePerformanceInsights"] is True
    assert database["PerformanceInsightsRetentionPeriod"] == 7
    assert database["MonitoringInterval"] == 0
    assert database_resource["DeletionPolicy"] == "Delete"
    assert database_resource["UpdateReplacePolicy"] == "Delete"
