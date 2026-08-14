import json
from pathlib import Path


ROOT = Path(__file__).parents[2]
TEMPLATE = ROOT / "infra/cloudformation/iam-bootstrap.json"


def _template() -> dict:
    assert TEMPLATE.is_file(), "IAM bootstrap CloudFormation template 尚未建立"
    return json.loads(TEMPLATE.read_text(encoding="utf-8"))


def _statements(resource_name: str) -> list[dict]:
    resource = _template()["Resources"][resource_name]
    assert resource["Type"] == "AWS::IAM::ManagedPolicy"
    return resource["Properties"]["PolicyDocument"]["Statement"]


def _actions(statement: dict) -> set[str]:
    actions = statement["Action"]
    return {actions} if isinstance(actions, str) else set(actions)


def test_account_protection_blocks_only_high_risk_account_and_purchase_actions() -> None:
    template = _template()
    resource = template["Resources"]["AccountProtectionPolicy"]
    properties = resource["Properties"]

    assert properties["Groups"] == [{"Ref": "DeveloperGroupName"}]
    statements = properties["PolicyDocument"]["Statement"]
    assert all(statement["Effect"] == "Deny" for statement in statements)
    denied = set().union(*(_actions(statement) for statement in statements))
    assert {
        "organizations:CreateOrganization",
        "organizations:InviteAccountToOrganization",
        "organizations:AcceptHandshake",
        "controltower:*",
        "sso:CreateInstance",
        "freetier:UpgradeAccountPlan",
        "aws-marketplace:Subscribe",
        "ec2:PurchaseReservedInstancesOffering",
        "rds:PurchaseReservedDBInstancesOffering",
        "savingsplans:CreateSavingsPlan",
        "iam:CreateUser",
        "iam:CreateAccessKey",
    } <= denied
    assert "billing:*" not in denied
    assert "aws-portal:ViewBilling" not in denied


def test_delegation_manages_only_project_prefixed_iam_resources() -> None:
    statements = _statements("ProjectIamDelegationPolicy")
    mutating_actions = {
        "iam:CreateRole",
        "iam:PutRolePolicy",
        "iam:CreatePolicy",
        "iam:CreateInstanceProfile",
        "iam:CreateOpenIDConnectProvider",
    }

    for statement in statements:
        actions = _actions(statement)
        if actions & mutating_actions:
            resource_text = json.dumps(statement["Resource"], sort_keys=True)
            assert "AWSFinalProject" in resource_text or "token.actions.githubusercontent.com" in resource_text
            assert statement["Resource"] != "*"

    all_actions = set().union(*(_actions(statement) for statement in statements))
    assert not {
        "iam:CreateUser",
        "iam:CreateGroup",
        "iam:AddUserToGroup",
        "iam:CreateAccessKey",
        "iam:CreateLoginProfile",
        "iam:AttachUserPolicy",
        "iam:PutUserPolicy",
    } & all_actions


def test_create_role_requires_power_user_permissions_boundary() -> None:
    statements = _statements("ProjectIamDelegationPolicy")
    create_role = next(
        statement
        for statement in statements
        if "iam:CreateRole" in _actions(statement)
    )

    assert create_role["Resource"] == {
        "Fn::Sub": "arn:${AWS::Partition}:iam::${AWS::AccountId}:role/AWSFinalProject*"
    }
    assert create_role["Condition"] == {
        "ArnEquals": {
            "iam:PermissionsBoundary": {
                "Fn::Sub": "arn:${AWS::Partition}:iam::aws:policy/PowerUserAccess"
            }
        }
    }
    assert "iam:DeleteRolePermissionsBoundary" not in _actions(create_role)


def test_pass_role_is_scoped_to_project_roles_and_expected_services() -> None:
    statements = _statements("ProjectIamDelegationPolicy")
    pass_role = next(
        statement
        for statement in statements
        if "iam:PassRole" in _actions(statement)
    )

    assert pass_role["Resource"] == {
        "Fn::Sub": "arn:${AWS::Partition}:iam::${AWS::AccountId}:role/AWSFinalProject*"
    }
    assert set(pass_role["Condition"]["StringEquals"]["iam:PassedToService"]) == {
        "ec2.amazonaws.com",
        "ecs-tasks.amazonaws.com",
        "lambda.amazonaws.com",
        "cloudformation.amazonaws.com",
    }


def test_template_never_creates_users_access_keys_or_login_profiles() -> None:
    template_text = json.dumps(_template(), sort_keys=True)
    assert "AWS::IAM::User" not in template_text
    assert "AWS::IAM::AccessKey" not in template_text
    assert "LoginProfile" not in template_text
