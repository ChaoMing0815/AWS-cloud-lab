from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]
TEMPLATE = ROOT / "infra/cloudformation/tier0-deployment-artifacts.yaml"


def _template() -> dict:
    assert TEMPLATE.is_file(), "Tier 0 deployment artifact template 尚未建立"
    return yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))


def test_artifact_template_contains_only_private_bucket_and_bounded_access_resources() -> None:
    template = _template()
    resources = template["Resources"]

    assert template["AWSTemplateFormatVersion"] == "2010-09-09"
    assert {resource["Type"] for resource in resources.values()} == {
        "AWS::S3::Bucket",
        "AWS::S3::BucketPolicy",
        "AWS::IAM::ManagedPolicy",
    }


def test_artifact_bucket_has_no_fixed_name_and_expires_encrypted_objects() -> None:
    resource = _template()["Resources"]["ArtifactBucket"]
    bucket = resource["Properties"]

    assert "BucketName" not in bucket
    assert bucket["BucketEncryption"] == {
        "ServerSideEncryptionConfiguration": [
            {"ServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
        ]
    }
    assert bucket["PublicAccessBlockConfiguration"] == {
        "BlockPublicAcls": True,
        "BlockPublicPolicy": True,
        "IgnorePublicAcls": True,
        "RestrictPublicBuckets": True,
    }
    assert bucket["OwnershipControls"] == {
        "Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]
    }
    assert bucket["LifecycleConfiguration"]["Rules"] == [
        {
            "Id": "ExpireReleaseArtifacts",
            "Status": "Enabled",
            "Prefix": "releases/",
            "ExpirationInDays": 7,
            "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 1},
        }
    ]
    assert resource["DeletionPolicy"] == "Delete"
    assert resource["UpdateReplacePolicy"] == "Delete"


def test_bucket_policy_denies_every_non_tls_request_to_exact_bucket_resources() -> None:
    statement = _template()["Resources"]["ArtifactBucketPolicy"]["Properties"][
        "PolicyDocument"
    ]["Statement"]

    assert statement == [
        {
            "Sid": "DenyInsecureTransport",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:*",
            "Resource": [
                {"Fn::GetAtt": ["ArtifactBucket", "Arn"]},
                {"Fn::Sub": "${ArtifactBucket.Arn}/*"},
            ],
            "Condition": {"Bool": {"aws:SecureTransport": "false"}},
        }
    ]


def test_instance_role_can_only_list_release_prefix_and_read_release_objects() -> None:
    policy = _template()["Resources"]["ArtifactReadPolicy"]["Properties"]

    assert policy["Roles"] == [{"Ref": "AppRoleName"}]
    assert policy["PolicyDocument"]["Statement"] == [
        {
            "Sid": "ListReleasePrefix",
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": {"Fn::GetAtt": ["ArtifactBucket", "Arn"]},
            "Condition": {"StringLike": {"s3:prefix": ["releases/*"]}},
        },
        {
            "Sid": "ReadReleaseArtifacts",
            "Effect": "Allow",
            "Action": "s3:GetObject",
            "Resource": {"Fn::Sub": "${ArtifactBucket.Arn}/releases/*"},
        },
    ]
    serialized = TEMPLATE.read_text(encoding="utf-8")
    assert "s3:PutObject" not in serialized
    assert "s3:DeleteObject" not in serialized
    assert "Resource: '*'" not in serialized
    assert 'Resource: "*"' not in serialized


def test_template_outputs_only_bucket_identifiers() -> None:
    assert _template()["Outputs"] == {
        "ArtifactBucketName": {"Value": {"Ref": "ArtifactBucket"}},
        "ArtifactReleasePrefix": {"Value": "releases/"},
    }
