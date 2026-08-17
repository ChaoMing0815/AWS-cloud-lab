from pathlib import Path

import yaml


ROOT = Path(__file__).parents[2]
TEMPLATE = ROOT / "infra/cloudformation/tier0-network.yaml"


def _template() -> dict:
    assert TEMPLATE.is_file(), "Tier 0 network CloudFormation template 尚未建立"
    return yaml.safe_load(TEMPLATE.read_text(encoding="utf-8"))


def _resources(template: dict) -> dict:
    return template["Resources"]


def _by_type(resources: dict, resource_type: str) -> dict:
    return {
        name: resource
        for name, resource in resources.items()
        if resource["Type"] == resource_type
    }


def test_tier0_network_template_declares_private_database_topology() -> None:
    template = _template()
    resources = _resources(template)

    assert template["AWSTemplateFormatVersion"] == "2010-09-09"
    assert resources["Vpc"]["Properties"]["EnableDnsSupport"] is True
    assert resources["Vpc"]["Properties"]["EnableDnsHostnames"] is True
    assert len(_by_type(resources, "AWS::EC2::Subnet")) == 3
    assert resources["PublicAppSubnet"]["Properties"]["MapPublicIpOnLaunch"] is True
    assert resources["PrivateDbSubnetA"]["Properties"]["MapPublicIpOnLaunch"] is False
    assert resources["PrivateDbSubnetB"]["Properties"]["MapPublicIpOnLaunch"] is False
    assert "AWS::EC2::NatGateway" not in {
        resource["Type"] for resource in resources.values()
    }


def test_tier0_network_template_routes_only_public_app_subnet_to_internet_gateway() -> None:
    resources = _resources(_template())
    routes = _by_type(resources, "AWS::EC2::Route")

    assert len(_by_type(resources, "AWS::EC2::InternetGateway")) == 1
    assert len(routes) == 1
    public_route = next(iter(routes.values()))["Properties"]
    assert public_route["DestinationCidrBlock"] == "0.0.0.0/0"
    assert "GatewayId" in public_route
    private_associations = {
        name: resource["Properties"]
        for name, resource in _by_type(resources, "AWS::EC2::SubnetRouteTableAssociation").items()
        if name.startswith("PrivateDb")
    }
    assert len(private_associations) == 2
    assert len(_by_type(resources, "AWS::EC2::RouteTable")) == 2


def test_tier0_network_template_allows_only_https_http_and_app_to_database() -> None:
    resources = _resources(_template())
    ingress = _by_type(resources, "AWS::EC2::SecurityGroupIngress")
    egress = _by_type(resources, "AWS::EC2::SecurityGroupEgress")
    app_group = resources["AppSecurityGroup"]["Properties"]
    db_group = resources["DbSecurityGroup"]["Properties"]

    localhost_sink_egress = [
        {
            "Description": "Suppress the AWS default allow-all egress rule",
            "IpProtocol": "-1",
            "CidrIp": "127.0.0.1/32",
        }
    ]
    assert app_group["SecurityGroupEgress"] == localhost_sink_egress
    assert db_group["SecurityGroupEgress"] == localhost_sink_egress
    assert {rule["Properties"]["FromPort"] for rule in ingress.values()} == {80, 443, 5432}
    assert all(rule["Properties"]["FromPort"] not in {22, 8000} for rule in ingress.values())
    db_ingress = ingress["DbFromAppIngress"]["Properties"]
    assert db_ingress["FromPort"] == db_ingress["ToPort"] == 5432
    assert "SourceSecurityGroupId" in db_ingress
    assert {rule["Properties"]["FromPort"] for rule in egress.values()} == {443, 5432}
    assert "DestinationSecurityGroupId" in egress["AppToDbEgress"]["Properties"]
