from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]
TEMPLATE = ROOT / "infra/cloudformation/tier2-worker-foundation.yaml"


def _template() -> dict:
    assert TEMPLATE.is_file(), "Tier 2 Worker foundation template 尚未建立"
    return yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))


def _resources_of_type(template: dict, resource_type: str) -> dict:
    return {
        name: resource
        for name, resource in template["Resources"].items()
        if resource["Type"] == resource_type
    }


def _statements(policy_document: dict) -> list[dict]:
    return policy_document["Statement"]


def _actions(statement: dict) -> set[str]:
    value = statement["Action"]
    return {value} if isinstance(value, str) else set(value)


def test_foundation_has_one_nat_one_private_subnet_and_exactly_two_workers() -> None:
    template = _template()
    resources = template["Resources"]

    assert len(_resources_of_type(template, "AWS::EC2::NatGateway")) == 1
    assert len(_resources_of_type(template, "AWS::EC2::EIP")) == 1
    assert len(_resources_of_type(template, "AWS::EC2::Subnet")) == 1
    assert len(_resources_of_type(template, "AWS::AutoScaling::AutoScalingGroup")) == 1
    assert len(_resources_of_type(template, "AWS::EC2::LaunchTemplate")) == 1

    subnet = resources["PrivateWorkerSubnet"]["Properties"]
    assert subnet["MapPublicIpOnLaunch"] is False
    assert subnet["CidrBlock"] == {"Ref": "PrivateWorkerSubnetCidr"}

    route = resources["PrivateWorkerDefaultRoute"]["Properties"]
    assert route["DestinationCidrBlock"] == "0.0.0.0/0"
    assert route["NatGatewayId"] == {"Ref": "WorkerNatGateway"}

    group = resources["WorkerAutoScalingGroup"]["Properties"]
    assert resources["WorkerAutoScalingGroup"]["DependsOn"] == [
        "PrivateWorkerDefaultRoute",
        "PrivateWorkerRouteTableAssociation",
    ]
    assert group["MinSize"] == "2"
    assert group["MaxSize"] == "2"
    assert group["DesiredCapacity"] == "2"
    assert group["VPCZoneIdentifier"] == [{"Ref": "PrivateWorkerSubnet"}]
    assert group["HealthCheckType"] == "EC2"

    launch_data = resources["WorkerLaunchTemplate"]["Properties"]["LaunchTemplateData"]
    interface = launch_data["NetworkInterfaces"][0]
    assert interface["AssociatePublicIpAddress"] is False
    assert interface["Groups"] == [{"Ref": "WorkerSecurityGroup"}]
    assert "KeyName" not in launch_data
    assert launch_data["MetadataOptions"] == {
        "HttpEndpoint": "enabled",
        "HttpTokens": "required",
        "HttpPutResponseHopLimit": 1,
        "InstanceMetadataTags": "disabled",
    }


def test_worker_network_has_no_ingress_and_db_only_accepts_worker_sg() -> None:
    template = _template()
    resources = template["Resources"]
    worker_sg = resources["WorkerSecurityGroup"]["Properties"]

    assert "SecurityGroupIngress" not in worker_sg
    assert worker_sg["SecurityGroupEgress"] == [
        {
            "Description": "Suppress the AWS default allow-all egress rule",
            "IpProtocol": "-1",
            "CidrIp": "127.0.0.1/32",
        }
    ]
    assert resources["WorkerHttpsEgress"]["Properties"] == {
        "GroupId": {"Ref": "WorkerSecurityGroup"},
        "IpProtocol": "tcp",
        "FromPort": 443,
        "ToPort": 443,
        "CidrIp": "0.0.0.0/0",
    }
    assert resources["WorkerToDbEgress"]["Properties"]["DestinationSecurityGroupId"] == {
        "Ref": "DbSecurityGroupId"
    }
    assert resources["DbFromWorkerIngress"]["Properties"] == {
        "GroupId": {"Ref": "DbSecurityGroupId"},
        "IpProtocol": "tcp",
        "FromPort": 5432,
        "ToPort": 5432,
        "SourceSecurityGroupId": {"Ref": "WorkerSecurityGroup"},
    }


def test_story_queue_and_dlq_are_encrypted_bounded_and_tls_only() -> None:
    template = _template()
    resources = template["Resources"]
    queues = _resources_of_type(template, "AWS::SQS::Queue")

    assert set(queues) == {"StoryQueue", "StoryDeadLetterQueue"}
    main = resources["StoryQueue"]["Properties"]
    dead = resources["StoryDeadLetterQueue"]["Properties"]
    assert main["SqsManagedSseEnabled"] is True
    assert dead["SqsManagedSseEnabled"] is True
    assert main["VisibilityTimeout"] == 180
    assert main["ReceiveMessageWaitTimeSeconds"] == 20
    assert main["RedrivePolicy"] == {
        "deadLetterTargetArn": {"Fn::GetAtt": ["StoryDeadLetterQueue", "Arn"]},
        "maxReceiveCount": 3,
    }
    assert dead["MessageRetentionPeriod"] == 1209600

    queue_policy = resources["StoryQueueTlsPolicy"]["Properties"]
    assert queue_policy["Queues"] == [
        {"Ref": "StoryQueue"},
        {"Ref": "StoryDeadLetterQueue"},
    ]
    deny = queue_policy["PolicyDocument"]["Statement"]
    assert deny == [
        {
            "Sid": "DenyInsecureTransport",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "sqs:*",
            "Resource": [
                {"Fn::GetAtt": ["StoryQueue", "Arn"]},
                {"Fn::GetAtt": ["StoryDeadLetterQueue", "Arn"]},
            ],
            "Condition": {"Bool": {"aws:SecureTransport": "false"}},
        }
    ]


def test_web_and_worker_roles_have_separate_least_privilege_queue_access() -> None:
    template = _template()
    resources = template["Resources"]

    producer = resources["WebStoryQueueProducerPolicy"]["Properties"]
    assert producer["Roles"] == [{"Ref": "AppRoleName"}]
    producer_statements = _statements(producer["PolicyDocument"])
    assert len(producer_statements) == 1
    assert _actions(producer_statements[0]) == {
        "sqs:GetQueueAttributes",
        "sqs:GetQueueUrl",
        "sqs:SendMessage",
    }
    assert producer_statements[0]["Resource"] == {
        "Fn::GetAtt": ["StoryQueue", "Arn"]
    }

    role = resources["WorkerRole"]["Properties"]
    assert role["RoleName"] == "AWSFinalProjectTier2WorkerRole"
    assert role["PermissionsBoundary"] == {
        "Fn::Sub": "arn:${AWS::Partition}:iam::aws:policy/PowerUserAccess"
    }
    assert role["ManagedPolicyArns"] == [
        {
            "Fn::Sub": "arn:${AWS::Partition}:iam::aws:policy/AmazonSSMManagedInstanceCore"
        }
    ]
    assert role["AssumeRolePolicyDocument"]["Statement"] == [
        {
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }
    ]

    statements = [
        statement
        for policy in role["Policies"]
        for statement in _statements(policy["PolicyDocument"])
    ]
    all_actions = set().union(*(_actions(statement) for statement in statements))
    assert {
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:ChangeMessageVisibility",
        "sqs:GetQueueAttributes",
    }.issubset(all_actions)
    assert "sqs:SendMessage" not in all_actions
    assert "iam:PassRole" not in all_actions
    assert "secretsmanager:GetSecretValue" in all_actions
    assert "bedrock:InvokeModel" in all_actions
    assert "ecr:GetAuthorizationToken" in all_actions

    for statement in statements:
        if statement["Resource"] == "*":
            assert _actions(statement) == {"ecr:GetAuthorizationToken"}


def test_worker_log_policy_uses_the_log_group_arn_without_an_extra_wildcard() -> None:
    resources = _template()["Resources"]
    worker_policies = {
        policy["PolicyName"]: policy["PolicyDocument"]
        for policy in resources["WorkerRole"]["Properties"]["Policies"]
    }

    log_statements = _statements(worker_policies["CoStoryTier2WorkerLogs"])
    assert log_statements == [
        {
            "Sid": "WriteOnlyWorkerLogGroup",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:DescribeLogStreams",
                "logs:PutLogEvents",
            ],
            "Resource": {"Fn::Sub": "${WorkerLogGroup.Arn}"},
        }
    ]


def test_foundation_is_bounded_and_exports_only_deployment_identifiers() -> None:
    template = _template()
    resources = template["Resources"]
    disallowed_types = {
        "AWS::ElasticLoadBalancingV2::LoadBalancer",
        "AWS::ECS::Cluster",
        "AWS::EKS::Cluster",
        "AWS::Lambda::Function",
        "AWS::RDS::DBInstance",
        "AWS::KMS::Key",
    }

    assert not {
        resource["Type"] for resource in resources.values()
    }.intersection(disallowed_types)
    assert len(_resources_of_type(template, "AWS::Logs::LogGroup")) == 1
    assert len(_resources_of_type(template, "AWS::CloudWatch::Alarm")) == 1
    assert resources["WorkerLogGroup"]["Properties"]["RetentionInDays"] == 7
    assert resources["StoryDeadLetterAlarm"]["Properties"]["Threshold"] == 1
    assert resources["StoryDeadLetterAlarm"]["Properties"]["TreatMissingData"] == "notBreaching"

    assert set(template["Outputs"]) == {
        "PrivateWorkerSubnetId",
        "WorkerSecurityGroupId",
        "WorkerAutoScalingGroupName",
        "WorkerRoleName",
        "StoryQueueArn",
        "StoryQueueUrl",
        "StoryDeadLetterQueueArn",
        "WorkerLogGroupName",
    }
