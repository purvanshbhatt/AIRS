"""
AWS network collector — ``collect_aws_network`` and the connector's
``aws.network.snapshot`` event.

No network and no real boto3 session: every AWS client is a stand-in whose
methods return canned EC2 responses or raise botocore ``ClientError``.

Covers:
  * normalisation of VPCs, subnets, security groups, gateways, VPNs, peerings
  * one denied (or failing) API never aborts the others
  * the 200-item cap, pagination, open-port extraction
  * VPN pre-shared key material never reaches the snapshot
  * the connector event (hourly id, account/region, None when nothing to draw)
  * EC2 / RDS inventory carries VPC, subnet and security-group ids
  * collector output drives the topology builder end to end
"""
import json
from datetime import datetime, timezone

from botocore.exceptions import ClientError

from app.connectors.aws_security_hub import AWSSecurityHubConnector
from app.services.discovery import aws_network
from app.services.discovery.aws_discovery import AWSDiscoveryService
from app.services.discovery.aws_network import MAX_ITEMS, collect_aws_network, open_ports_for
from app.services.discovery.discovery import SourceDiscoveryResult
from app.services.network_topology import INTERNET_NODE_ID, build_topology

ACCOUNT = "123456789012"
REGION = "us-east-1"
PRE_SHARED_KEY = "psk-SUPER-SECRET-do-not-leak"


def aws_error(code: str, operation: str = "Operation") -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": f"{code}: not authorized"}}, operation)


def tag(name: str):
    return [{"Key": "Name", "Value": name}]


class FakeEC2:
    """EC2 client stand-in. ``responses`` maps method name -> dict, list of
    pages, or an exception to raise. Unlisted methods return an empty result."""

    def __init__(self, responses=None):
        self.responses = dict(responses or {})
        self.calls = []

    def __getattr__(self, name):
        if not name.startswith("describe_"):
            raise AttributeError(name)

        def call(**kwargs):
            self.calls.append((name, kwargs))
            response = self.responses.get(name, {})
            if isinstance(response, BaseException):
                raise response
            if isinstance(response, list):  # paginated: one entry per page
                page = int(kwargs.get("NextToken") or 0)
                body = dict(response[page])
                if page + 1 < len(response):
                    body["NextToken"] = str(page + 1)
                return body
            if callable(response):
                return response(**kwargs)
            return response

        return call


class FakeSession:
    def __init__(self, clients):
        self._clients = clients
        self.client_calls = []

    def client(self, name, **kwargs):
        self.client_calls.append((name, kwargs))
        return self._clients[name]


def full_account():
    """A small office account: one VPC, two subnets, a site-to-site VPN with one
    tunnel down, a client VPN, a peering and an SSH port open to the world."""
    return {
        "describe_vpcs": {"Vpcs": [
            {"VpcId": "vpc-1", "CidrBlock": "10.0.0.0/16", "State": "available", "Tags": tag("clinic-vpc")},
            {"VpcId": "vpc-default", "CidrBlock": "172.31.0.0/16", "IsDefault": True},
        ]},
        "describe_subnets": {"Subnets": [
            {"SubnetId": "subnet-priv", "VpcId": "vpc-1", "CidrBlock": "10.0.1.0/24",
             "AvailabilityZone": "us-east-1a", "MapPublicIpOnLaunch": False, "Tags": tag("private-a")},
            {"SubnetId": "subnet-pub", "VpcId": "vpc-1", "CidrBlock": "10.0.0.0/24",
             "AvailabilityZone": "us-east-1b", "MapPublicIpOnLaunch": True},
        ]},
        "describe_security_groups": {"SecurityGroups": [
            {"GroupId": "sg-open", "GroupName": "web", "VpcId": "vpc-1", "IpPermissions": [
                {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
                {"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443, "Ipv6Ranges": [{"CidrIpv6": "::/0"}]},
                {"IpProtocol": "tcp", "FromPort": 5432, "ToPort": 5432, "IpRanges": [{"CidrIp": "10.0.0.0/16"}]},
            ]},
            {"GroupId": "sg-closed", "GroupName": "db", "VpcId": "vpc-1", "Tags": tag("database-sg"), "IpPermissions": [
                {"IpProtocol": "tcp", "FromPort": 5432, "ToPort": 5432, "IpRanges": [{"CidrIp": "10.0.1.0/24"}]},
            ]},
        ]},
        "describe_internet_gateways": {"InternetGateways": [
            {"InternetGatewayId": "igw-1", "Attachments": [{"VpcId": "vpc-1", "State": "available"}]},
        ]},
        "describe_nat_gateways": {"NatGateways": [
            {"NatGatewayId": "nat-1", "VpcId": "vpc-1", "State": "available", "ConnectivityType": "public",
             "NatGatewayAddresses": [{"PublicIp": "203.0.113.5", "PrivateIp": "10.0.0.9"}]},
            {"NatGatewayId": "nat-private", "VpcId": "vpc-1", "State": "available", "ConnectivityType": "private"},
            {"NatGatewayId": "nat-gone", "VpcId": "vpc-1", "State": "deleted"},
        ]},
        "describe_vpn_gateways": {"VpnGateways": [
            {"VpnGatewayId": "vgw-1", "State": "available",
             "VpcAttachments": [{"VpcId": "vpc-old", "State": "detached"}, {"VpcId": "vpc-1", "State": "attached"}]},
        ]},
        "describe_customer_gateways": {"CustomerGateways": [
            {"CustomerGatewayId": "cgw-1", "State": "available", "IpAddress": "203.0.113.77", "Tags": tag("office-firewall")},
        ]},
        "describe_vpn_connections": {"VpnConnections": [
            {"VpnConnectionId": "vpn-1", "State": "available", "VpnGatewayId": "vgw-1", "CustomerGatewayId": "cgw-1",
             "Tags": tag("office-to-aws"),
             "CustomerGatewayConfiguration": f"<vpn><pre_shared_key>{PRE_SHARED_KEY}</pre_shared_key></vpn>",
             "VgwTelemetry": [
                 {"OutsideIpAddress": "203.0.113.21", "Status": "UP",
                  "LastStatusChange": datetime(2026, 11, 1, 8, 0, tzinfo=timezone.utc)},
                 {"OutsideIpAddress": "203.0.113.22", "Status": "DOWN",
                  "LastStatusChange": datetime(2026, 11, 9, 7, 30, tzinfo=timezone.utc)},
             ]},
            {"VpnConnectionId": "vpn-deleted", "State": "deleted", "VpnGatewayId": "vgw-1", "CustomerGatewayId": "cgw-1"},
        ]},
        "describe_client_vpn_endpoints": {"ClientVpnEndpoints": [
            {"ClientVpnEndpointId": "cvpn-1", "Description": "Remote staff", "Status": {"Code": "available"},
             "VpcId": "vpc-1", "ClientCidrBlock": "10.8.0.0/22"},
        ]},
        "describe_client_vpn_connections": {"Connections": [
            {"ConnectionId": "c-1", "Status": {"Code": "active"}},
            {"ConnectionId": "c-2", "Status": {"Code": "active"}},
            {"ConnectionId": "c-3", "Status": {"Code": "terminated"}},
        ]},
        "describe_vpc_peering_connections": {"VpcPeeringConnections": [
            {"VpcPeeringConnectionId": "pcx-1", "Status": {"Code": "active"},
             "RequesterVpcInfo": {"VpcId": "vpc-1"}, "AccepterVpcInfo": {"VpcId": "vpc-default"}},
        ]},
        "describe_transit_gateways": {"TransitGateways": [
            {"TransitGatewayId": "tgw-1", "State": "available", "Description": "hub"},
        ]},
    }


def collect(responses):
    ec2 = FakeEC2(responses)
    session = FakeSession({"ec2": ec2})
    return collect_aws_network(session, REGION), ec2, session


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def test_full_account_is_normalised():
    snap, ec2, session = collect(full_account())

    assert snap["provider"] == "aws"
    assert snap["region"] == REGION
    assert snap["denied_apis"] == [] and snap["failed_apis"] == []
    assert snap["truncated"] is False
    assert session.client_calls == [("ec2", {"region_name": REGION})]

    networks = {n["id"]: n for n in snap["networks"]}
    assert networks["vpc-1"] == {
        "id": "vpc-1", "name": "clinic-vpc", "cidr": "10.0.0.0/16", "kind": "vpc", "location": REGION,
    }
    assert networks["vpc-default"]["name"] == "Default VPC"   # no Name tag

    subnets = {s["id"]: s for s in snap["subnets"]}
    assert subnets["subnet-priv"] == {
        "id": "subnet-priv", "name": "private-a", "cidr": "10.0.1.0/24", "network_id": "vpc-1",
        "public": False, "availability_zone": "us-east-1a",
    }
    assert subnets["subnet-pub"]["public"] is True
    assert subnets["subnet-pub"]["name"] == "subnet-pub"

    groups = {g["id"]: g for g in snap["security_groups"]}
    assert groups["sg-open"]["open_ports"] == ["tcp/22", "tcp/443"]   # the 10.0.0.0/16 rule is not public
    assert groups["sg-open"]["name"] == "web"
    assert groups["sg-closed"]["open_ports"] == []
    assert groups["sg-closed"]["name"] == "database-sg"               # Name tag wins over GroupName
    assert groups["sg-closed"]["network_id"] == "vpc-1"

    gateways = {g["id"]: g for g in snap["gateways"]}
    assert gateways["igw-1"] == {
        "id": "igw-1", "name": "igw-1", "kind": "internet_gateway", "network_id": "vpc-1", "to_internet": True,
    }
    assert gateways["nat-1"]["kind"] == "nat_gateway"
    assert gateways["nat-1"]["public_ip"] == "203.0.113.5"
    assert gateways["nat-1"]["to_internet"] is True
    assert gateways["nat-private"]["to_internet"] is False
    assert "nat-gone" not in gateways
    assert gateways["vgw-1"]["kind"] == "vpn_gateway"
    assert gateways["vgw-1"]["network_id"] == "vpc-1"                 # the detached attachment is ignored
    assert gateways["cgw-1"]["kind"] == "customer_gateway"
    assert gateways["cgw-1"]["name"] == "office-firewall"
    assert gateways["cgw-1"]["public_ip"] == "203.0.113.77"
    assert gateways["tgw-1"]["kind"] == "transit_gateway"

    vpns = {v["id"]: v for v in snap["vpns"]}
    assert "vpn-deleted" not in vpns
    s2s = vpns["vpn-1"]
    assert s2s["kind"] == "site_to_site"
    assert s2s["name"] == "office-to-aws"
    assert s2s["state"] == "available"
    assert s2s["gateway_id"] == "vgw-1"
    assert s2s["network_id"] == "vpc-1"
    assert s2s["remote_gateway_id"] == "cgw-1"
    assert [t["status"] for t in s2s["tunnels"]] == ["UP", "DOWN"]
    assert s2s["tunnels"][0]["outside_ip"] == "203.0.113.21"
    assert s2s["tunnels"][1]["last_change"].startswith("2026-11-09T07:30")
    client = vpns["cvpn-1"]
    assert client["kind"] == "client"
    assert client["name"] == "Remote staff"
    assert client["state"] == "available"
    assert client["network_id"] == "vpc-1"
    assert client["active_connections"] == 2
    assert ("describe_client_vpn_connections", {"ClientVpnEndpointId": "cvpn-1"}) in ec2.calls

    assert snap["peerings"] == [
        {"id": "pcx-1", "a_network_id": "vpc-1", "b_network_id": "vpc-default", "state": "active"},
    ]
    assert snap["devices"] == [] and snap["links"] == []


def test_vpn_pre_shared_key_never_leaves_the_collector():
    snap, _, _ = collect(full_account())
    assert PRE_SHARED_KEY not in json.dumps(snap, default=str)
    assert "CustomerGatewayConfiguration" not in json.dumps(snap, default=str)


def test_only_read_only_describe_calls_are_made():
    _, ec2, _ = collect(full_account())
    called = {name for name, _ in ec2.calls}
    assert called == {
        "describe_vpcs", "describe_subnets", "describe_security_groups", "describe_internet_gateways",
        "describe_nat_gateways", "describe_vpn_gateways", "describe_customer_gateways",
        "describe_vpn_connections", "describe_client_vpn_endpoints", "describe_client_vpn_connections",
        "describe_vpc_peering_connections", "describe_transit_gateways",
    }
    # The module is handed a session; it has no way to build one from ambient credentials.
    assert not hasattr(aws_network, "boto3")


def test_empty_account_yields_empty_lists():
    snap, _, _ = collect({})
    for key in ("networks", "subnets", "gateways", "vpns", "security_groups", "devices", "links", "peerings"):
        assert snap[key] == []
    assert snap["denied_apis"] == []


# ---------------------------------------------------------------------------
# Failure isolation
# ---------------------------------------------------------------------------

def test_denied_apis_do_not_abort_the_rest():
    responses = full_account()
    responses["describe_subnets"] = aws_error("UnauthorizedOperation", "DescribeSubnets")
    responses["describe_vpn_connections"] = aws_error("AccessDenied", "DescribeVpnConnections")
    responses["describe_transit_gateways"] = aws_error("UnauthorizedOperation", "DescribeTransitGateways")
    snap, _, _ = collect(responses)

    assert snap["denied_apis"] == [
        "ec2:DescribeSubnets", "ec2:DescribeTransitGateways", "ec2:DescribeVpnConnections",
    ]
    assert snap["failed_apis"] == []
    assert snap["subnets"] == []
    # Everything that was readable is still there.
    assert {n["id"] for n in snap["networks"]} == {"vpc-1", "vpc-default"}
    assert {g["id"] for g in snap["gateways"]} == {"igw-1", "nat-1", "nat-private", "vgw-1", "cgw-1"}
    assert [v["id"] for v in snap["vpns"]] == ["cvpn-1"]
    assert len(snap["security_groups"]) == 2
    assert len(snap["peerings"]) == 1


def test_every_api_denied_returns_an_empty_snapshot_and_the_full_list():
    responses = {name: aws_error("UnauthorizedOperation") for name in full_account()}
    snap, _, _ = collect(responses)
    assert snap["networks"] == [] and snap["vpns"] == []
    assert set(snap["denied_apis"]) == set(aws_network.NETWORK_APIS) - {
        "ec2:DescribeClientVpnConnections",   # never reached: no endpoint was listed
    }


def test_unexpected_error_is_recorded_and_does_not_abort(caplog):
    responses = full_account()
    responses["describe_nat_gateways"] = RuntimeError(f"boom {PRE_SHARED_KEY}")
    responses["describe_client_vpn_connections"] = aws_error("InvalidClientVpnEndpointId.NotFound")
    with caplog.at_level("INFO"):
        snap, _, _ = collect(responses)

    assert snap["failed_apis"] == ["ec2:DescribeNatGateways", "ec2:DescribeClientVpnConnections"]
    assert snap["denied_apis"] == []
    assert {g["id"] for g in snap["gateways"]} == {"igw-1", "vgw-1", "cgw-1", "tgw-1"}
    # The endpoint is still listed; the count we could not read stays unknown.
    client = next(v for v in snap["vpns"] if v["id"] == "cvpn-1")
    assert client["active_connections"] is None
    # Exception text is never logged.
    assert PRE_SHARED_KEY not in caplog.text


def test_session_that_cannot_build_a_client_is_tolerated():
    class BrokenSession:
        def client(self, *_args, **_kwargs):
            raise RuntimeError("no client")

    snap = collect_aws_network(BrokenSession(), REGION)
    assert snap["networks"] == [] and snap["vpns"] == []
    assert snap["failed_apis"] == ["ec2:client"]


# ---------------------------------------------------------------------------
# Caps, pagination, ports
# ---------------------------------------------------------------------------

def test_lists_are_capped_at_200():
    vpcs = [{"VpcId": f"vpc-{i}", "CidrBlock": "10.0.0.0/16"} for i in range(MAX_ITEMS + 25)]
    snap, _, _ = collect({"describe_vpcs": {"Vpcs": vpcs}})
    assert len(snap["networks"]) == MAX_ITEMS == 200
    assert snap["truncated"] is True


def test_pagination_follows_next_token():
    pages = [
        {"Subnets": [{"SubnetId": "subnet-a", "VpcId": "vpc-1"}]},
        {"Subnets": [{"SubnetId": "subnet-b", "VpcId": "vpc-1"}]},
        {"Subnets": [{"SubnetId": "subnet-c", "VpcId": "vpc-1"}]},
    ]
    snap, ec2, _ = collect({"describe_subnets": pages})
    assert [s["id"] for s in snap["subnets"]] == ["subnet-a", "subnet-b", "subnet-c"]
    assert [kw for name, kw in ec2.calls if name == "describe_subnets"] == [{}, {"NextToken": "1"}, {"NextToken": "2"}]
    assert snap["truncated"] is False


def test_pagination_stops_after_the_page_limit():
    pages = [{"Subnets": [{"SubnetId": f"subnet-{i}", "VpcId": "vpc-1"}]} for i in range(aws_network._MAX_PAGES + 5)]
    snap, ec2, _ = collect({"describe_subnets": pages})
    assert len([1 for name, _ in ec2.calls if name == "describe_subnets"]) == aws_network._MAX_PAGES
    assert len(snap["subnets"]) == aws_network._MAX_PAGES
    assert snap["truncated"] is True


def test_open_ports_for():
    assert open_ports_for(None) == []
    assert open_ports_for([
        {"IpProtocol": "-1", "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
        {"IpProtocol": "tcp", "FromPort": 8000, "ToPort": 8100, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
        {"IpProtocol": "udp", "FromPort": 53, "ToPort": 53, "Ipv6Ranges": [{"CidrIpv6": "::/0"}]},
        {"IpProtocol": "icmp", "FromPort": -1, "ToPort": -1, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
        {"IpProtocol": "tcp", "FromPort": 0, "ToPort": 65535, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
        {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "198.51.100.0/24"}]},
        {"IpProtocol": "tcp", "FromPort": 3389, "ToPort": 3389,
         "UserIdGroupPairs": [{"GroupId": "sg-other"}]},
    ]) == ["all", "tcp/8000-8100", "udp/53", "icmp", "tcp/all"]


# ---------------------------------------------------------------------------
# Connector event
# ---------------------------------------------------------------------------

def make_connector(clients):
    connector = AWSSecurityHubConnector(
        connector_id="conn-aws-network",
        org_id="org-network",
        credentials={"aws_access_key_id": "AKIAIOSFODNN7EXAMPLE", "aws_secret_access_key": "x", "aws_region": REGION},
        config={},
    )
    connector._session = FakeSession(clients)
    connector.account_id = ACCOUNT
    return connector


def test_connector_emits_one_network_snapshot_event():
    connector = make_connector({"ec2": FakeEC2(full_account())})
    event = connector._collect_network_event()

    assert event is not None
    assert event.event_type == "aws.network.snapshot"
    assert event.source_system == "aws"
    hour = datetime.now(timezone.utc).strftime("%Y%m%d%H")
    assert event.source_event_id in {
        f"aws-network-{ACCOUNT}-{REGION}-{hour}",
        # tolerate the hour rolling over between the call and the assertion
        event.source_event_id if event.source_event_id.startswith(f"aws-network-{ACCOUNT}-{REGION}-") else "",
    }
    assert event.timestamp
    payload = event.payload
    assert payload["provider"] == "aws"
    assert payload["account_id"] == ACCOUNT
    assert payload["region"] == REGION
    assert len(payload["networks"]) == 2
    assert payload["denied_apis"] == []
    json.dumps(payload)                                   # plain JSON (datetimes already converted)
    assert PRE_SHARED_KEY not in json.dumps(payload)


def test_connector_returns_none_without_networks_or_vpns():
    assert make_connector({"ec2": FakeEC2({})})._collect_network_event() is None
    # Security groups alone are not a network to draw.
    only_groups = {"describe_security_groups": full_account()["describe_security_groups"]}
    assert make_connector({"ec2": FakeEC2(only_groups)})._collect_network_event() is None
    # A VPN without a readable VPC list is still worth showing.
    only_vpn = {"describe_vpn_connections": full_account()["describe_vpn_connections"],
                "describe_vpcs": aws_error("UnauthorizedOperation")}
    event = make_connector({"ec2": FakeEC2(only_vpn)})._collect_network_event()
    assert event is not None
    assert event.payload["denied_apis"] == ["ec2:DescribeVpcs"]


def test_connector_sync_includes_the_network_event_between_inventory_and_iam():
    ec2 = FakeEC2({
        **full_account(),
        "describe_instances": {"Reservations": [{"Instances": [{
            "InstanceId": "i-0abc", "State": {"Name": "running"}, "InstanceType": "t3.micro",
            "PrivateIpAddress": "10.0.1.20", "VpcId": "vpc-1", "SubnetId": "subnet-priv",
            "SecurityGroups": [{"GroupId": "sg-open", "GroupName": "web"}],
            "Placement": {"AvailabilityZone": "us-east-1a"}, "Tags": tag("ehr-app"),
        }]}]},
    })
    connector = make_connector({"ec2": ec2, "rds": FakeEC2({}), "ssm": FakeEC2({})})
    events = connector._collect_events()
    assert [e.event_type for e in events] == ["aws.inventory.snapshot", "aws.network.snapshot"]

    resource = events[0].payload["resources"][0]
    assert resource["vpc_id"] == "vpc-1"
    assert resource["subnet_id"] == "subnet-priv"
    assert resource["security_group_ids"] == ["sg-open"]
    assert resource["availability_zone"] == "us-east-1a"


def test_inventory_carries_vpc_placement_for_ec2_and_rds():
    class FakeRDS:
        def describe_db_instances(self, **_kwargs):
            return {"DBInstances": [{
                "DBInstanceIdentifier": "clinic-db", "Engine": "postgres", "EngineVersion": "16.4",
                "DBInstanceStatus": "available", "DBInstanceClass": "db.t3.micro",
                "Endpoint": {"Address": "clinic-db.abc.us-east-1.rds.amazonaws.com"},
                "DBSubnetGroup": {"VpcId": "vpc-1"},
                "VpcSecurityGroups": [{"VpcSecurityGroupId": "sg-closed", "Status": "active"}],
            }]}

    ec2 = FakeEC2({"describe_instances": {"Reservations": [{"Instances": [{
        "InstanceId": "i-0abc", "State": {"Name": "running"}, "VpcId": "vpc-1", "SubnetId": "subnet-priv",
        "SecurityGroups": [{"GroupId": "sg-open"}, {"GroupId": "sg-closed"}],
    }]}]}})
    session = FakeSession({"ec2": ec2, "rds": FakeRDS(), "ssm": FakeEC2({})})
    service = AWSDiscoveryService(db=None, org_id="org-network", is_demo=False)
    resources = service.fetch_aws_resources(session, SourceDiscoveryResult(source="aws"))

    instance, database = resources
    assert instance["vpc_id"] == "vpc-1"
    assert instance["subnet_id"] == "subnet-priv"
    assert instance["security_group_ids"] == ["sg-open", "sg-closed"]
    assert database["vpc_id"] == "vpc-1"
    assert database["subnet_id"] is None
    assert database["security_group_ids"] == ["sg-closed"]

    mapped = [AWSSecurityHubConnector._inventory_resource(r) for r in resources]
    assert mapped[0]["kind"] == "ec2_instance"
    assert mapped[0]["vpc_id"] == "vpc-1" and mapped[0]["subnet_id"] == "subnet-priv"
    assert mapped[0]["security_group_ids"] == ["sg-open", "sg-closed"]
    assert mapped[1]["kind"] == "rds_instance"
    assert mapped[1]["vpc_id"] == "vpc-1" and mapped[1]["security_group_ids"] == ["sg-closed"]
    assert "subnet_id" not in mapped[1]


# ---------------------------------------------------------------------------
# Collector -> topology
# ---------------------------------------------------------------------------

def test_collector_output_draws_the_map():
    connector = make_connector({"ec2": FakeEC2(full_account())})
    event = connector._collect_network_event()
    inventory = {
        "event_type": "aws.inventory.snapshot", "source_system": "aws",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {"resources": [{
            "kind": "ec2_instance", "instance_id": "i-0abc", "name": "ehr-app", "state": "running",
            "private_ip": "10.0.1.20", "vpc_id": "vpc-1", "subnet_id": "subnet-priv",
            "security_group_ids": ["sg-open"],
        }]},
    }
    topo = build_topology("org-network", events=[event.to_dict(), inventory])
    nodes = {n["id"]: n for n in topo["nodes"]}
    edges = {(e["source"], e["target"], e["kind"]) for e in topo["edges"]}

    assert nodes["net:aws:vpc-1"]["label"] == "clinic-vpc"
    assert nodes["net:aws:vpc-1"]["meta"]["cidr"] == "10.0.0.0/16"
    assert nodes["subnet:aws:subnet-priv"]["label"] == "private-a"
    assert nodes["gw:aws:igw-1"]["meta"]["gateway_kind"] == "internet_gateway"
    assert nodes["aws:sg:sg-open"]["meta"]["open_ports"] == ["tcp/22", "tcp/443"]

    vpn = nodes["vpn:aws:vpn-1"]
    assert vpn["status"] == "warning"
    assert vpn["meta"]["tunnels_up"] == 1 and vpn["meta"]["tunnels_total"] == 2
    assert [i["title"] for i in vpn["meta"]["issues"]] == ["One VPN tunnel is down"]
    assert nodes["vpn:aws:cvpn-1"]["status"] == "healthy"
    assert nodes["vpn:aws:cvpn-1"]["meta"]["active_connections"] == 2

    assert ("aws:instance:i-0abc", "subnet:aws:subnet-priv", "member_of") in edges
    assert ("subnet:aws:subnet-priv", "net:aws:vpc-1", "part_of") in edges
    assert ("aws:sg:sg-open", "aws:instance:i-0abc", "protects") in edges
    assert ("net:aws:vpc-1", "gw:aws:igw-1", "routes_to") in edges
    assert ("gw:aws:igw-1", INTERNET_NODE_ID, "routes_to") in edges
    assert ("gw:aws:nat-1", INTERNET_NODE_ID, "routes_to") in edges
    assert ("gw:aws:nat-private", INTERNET_NODE_ID, "routes_to") not in edges
    assert ("vpn:aws:vpn-1", "gw:aws:vgw-1", "vpn_tunnel") in edges
    assert ("vpn:aws:vpn-1", "gw:aws:cgw-1", "vpn_tunnel") in edges
    assert ("net:aws:vpc-1", "gw:aws:vgw-1", "routes_to") in edges
    assert ("vpn:aws:cvpn-1", "net:aws:vpc-1", "vpn_tunnel") in edges
    assert ("net:aws:vpc-1", "net:aws:vpc-default", "routes_to") in edges
    assert (INTERNET_NODE_ID, "aws:sg:sg-open", "exposed_to_internet") in edges

    assert topo["summary"]["networks"] == 2
    assert topo["summary"]["vpns"] == 2
    assert topo["summary"]["vpn_down"] == 0
    # No inferred network: the instance was placed by the subnet AWS reported.
    assert not any(n["meta"].get("inferred") for n in topo["nodes"])
    source = next(s for s in topo["live"]["sources"] if s["type"] == "aws")
    assert source["event_count"] == 2
