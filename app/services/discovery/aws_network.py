"""
AWS network collector.

Reads how an AWS account's network is laid out (VPCs, subnets, security
groups, gateways, VPNs, peerings) and returns it in the normalized network
snapshot shape the network map understands (``provider: "aws"``).

Rules:

  * Read-only EC2 ``Describe*`` calls only, all covered by the AWS-managed
    SecurityAudit / ViewOnlyAccess policies.
  * Every call is isolated: AccessDenied (or any other failure) on one API
    is recorded and the others still run. Denied APIs are listed in
    ``denied_apis``; other failures in ``failed_apis``.
  * The caller supplies the boto3 session built from the organization's own
    connector credentials. This module never creates a session, so it can
    never fall back to the server's ambient AWS identity.
  * Only named fields are copied out of AWS responses. In particular
    ``CustomerGatewayConfiguration`` (it carries VPN pre-shared keys) is
    never read, stored or logged. Exception text is never logged either.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.services.discovery.aws_discovery import (
    _client_error_code,
    _is_access_denied,
    _name_tag,
    _paginate,
)

logger = logging.getLogger("airs.discovery.aws_network")

MAX_ITEMS = 200
_MAX_OPEN_PORTS = 50
_MAX_PAGES = 10
_MAX_CLIENT_VPN_CONNECTION_LOOKUPS = 20

API_DESCRIBE_VPCS = "ec2:DescribeVpcs"
API_DESCRIBE_SUBNETS = "ec2:DescribeSubnets"
API_DESCRIBE_SECURITY_GROUPS = "ec2:DescribeSecurityGroups"
API_DESCRIBE_INTERNET_GATEWAYS = "ec2:DescribeInternetGateways"
API_DESCRIBE_NAT_GATEWAYS = "ec2:DescribeNatGateways"
API_DESCRIBE_VPN_GATEWAYS = "ec2:DescribeVpnGateways"
API_DESCRIBE_CUSTOMER_GATEWAYS = "ec2:DescribeCustomerGateways"
API_DESCRIBE_VPN_CONNECTIONS = "ec2:DescribeVpnConnections"
API_DESCRIBE_CLIENT_VPN_ENDPOINTS = "ec2:DescribeClientVpnEndpoints"
API_DESCRIBE_CLIENT_VPN_CONNECTIONS = "ec2:DescribeClientVpnConnections"
API_DESCRIBE_VPC_PEERING_CONNECTIONS = "ec2:DescribeVpcPeeringConnections"
API_DESCRIBE_TRANSIT_GATEWAYS = "ec2:DescribeTransitGateways"

# Every API this collector may call (all read-only).
NETWORK_APIS = (
    API_DESCRIBE_VPCS,
    API_DESCRIBE_SUBNETS,
    API_DESCRIBE_SECURITY_GROUPS,
    API_DESCRIBE_INTERNET_GATEWAYS,
    API_DESCRIBE_NAT_GATEWAYS,
    API_DESCRIBE_VPN_GATEWAYS,
    API_DESCRIBE_CUSTOMER_GATEWAYS,
    API_DESCRIBE_VPN_CONNECTIONS,
    API_DESCRIBE_CLIENT_VPN_ENDPOINTS,
    API_DESCRIBE_CLIENT_VPN_CONNECTIONS,
    API_DESCRIBE_VPC_PEERING_CONNECTIONS,
    API_DESCRIBE_TRANSIT_GATEWAYS,
)

_GONE = {"deleted", "deleting", "failed"}
_OPEN_CIDRS = {"0.0.0.0/0", "::/0"}


def _state(value: Any) -> str:
    """State string from either a plain value or a {"Code": ...} / {"Name": ...} dict."""
    if isinstance(value, dict):
        value = value.get("Code") or value.get("Name")
    return str(value or "").lower()


def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _attached_vpc(attachments: Any) -> Optional[str]:
    """First VPC a gateway is attached to (ignores detached / detaching)."""
    for attachment in attachments or []:
        if not isinstance(attachment, dict) or not attachment.get("VpcId"):
            continue
        if _state(attachment.get("State")) in ("detached", "detaching"):
            continue
        return attachment["VpcId"]
    return None


def open_ports_for(ip_permissions: Any) -> List[str]:
    """Ports a security group lets the whole internet reach.

    Returns entries such as ``"tcp/22"``, ``"tcp/8000-8100"``, ``"udp/53"``,
    ``"icmp"`` or ``"all"`` for every ingress rule whose source is
    ``0.0.0.0/0`` or ``::/0``.
    """
    ports: List[str] = []
    for rule in ip_permissions or []:
        if not isinstance(rule, dict):
            continue
        sources = [r.get("CidrIp") for r in rule.get("IpRanges") or [] if isinstance(r, dict)]
        sources += [r.get("CidrIpv6") for r in rule.get("Ipv6Ranges") or [] if isinstance(r, dict)]
        if not any(source in _OPEN_CIDRS for source in sources):
            continue
        protocol = str(rule.get("IpProtocol") or "-1").lower()
        from_port, to_port = rule.get("FromPort"), rule.get("ToPort")
        if protocol == "-1":
            entry = "all"
        elif protocol in ("icmp", "icmpv6", "1", "58"):
            entry = "icmp"
        elif from_port is None or to_port is None:
            entry = protocol
        elif (from_port, to_port) in ((0, 65535), (-1, -1)):
            entry = f"{protocol}/all"
        elif from_port == to_port:
            entry = f"{protocol}/{from_port}"
        else:
            entry = f"{protocol}/{from_port}-{to_port}"
        if entry not in ports:
            ports.append(entry)
    return ports[:_MAX_OPEN_PORTS]


def collect_aws_network(
    session: Any,
    region: Optional[str] = None,
    client_kwargs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Collect the account's network layout for one region.

    Args:
        session: boto3 session built from the organization's connector
            credentials (never the server's own identity).
        region: AWS region to read. Falls back to the session's region.
        client_kwargs: extra keyword arguments for ``session.client`` (the
            connector passes its short-timeout botocore config).

    Returns:
        The normalized network snapshot (``provider``, ``networks``,
        ``subnets``, ``gateways``, ``vpns``, ``security_groups``, ``devices``,
        ``links``, ``peerings``) plus ``region``, ``denied_apis``,
        ``failed_apis`` and ``truncated``. Each list is capped at 200.
    """
    denied: List[str] = []
    failed: List[str] = []
    snapshot: Dict[str, Any] = {
        "provider": "aws",
        "region": region,
        "networks": [],
        "subnets": [],
        "gateways": [],
        "vpns": [],
        "security_groups": [],
        "devices": [],
        "links": [],
        "peerings": [],
        "denied_apis": denied,
        "failed_apis": failed,
        "truncated": False,
    }

    def note_failure(api: str, exc: BaseException) -> None:
        if _is_access_denied(exc):
            if api not in denied:
                denied.append(api)
            return
        if api not in failed:
            failed.append(api)
        # Class name and AWS error code only: exception text stays out of logs.
        logger.info(
            "AWS network read %s failed: exception=%s aws_error=%s",
            api, type(exc).__name__, _client_error_code(exc),
        )

    try:
        kwargs = dict(client_kwargs or {})
        if region:
            kwargs["region_name"] = region
        ec2 = session.client("ec2", **kwargs)
    except Exception as exc:
        note_failure("ec2:client", exc)
        return snapshot

    cut_short: List[str] = []

    def read(api: str, method: str, result_key: str, **params: Any) -> List[Dict[str, Any]]:
        """One isolated, paginated describe call (at most ``_MAX_PAGES`` pages). Never raises."""
        pages = {"count": 0}

        def call(**call_params: Any) -> Any:
            response = getattr(ec2, method)(**call_params)
            pages["count"] += 1
            if pages["count"] >= _MAX_PAGES and isinstance(response, dict) and response.get("NextToken"):
                # Stop here: the lists are capped anyway and a sync must stay quick.
                cut_short.append(api)
                response = {key: value for key, value in response.items() if key != "NextToken"}
            return response

        try:
            items = _paginate(call, result_key, **params)
        except Exception as exc:
            note_failure(api, exc)
            return []
        return [item for item in items if isinstance(item, dict)]

    def cap(key: str, items: List[Dict[str, Any]]) -> None:
        if len(items) > MAX_ITEMS:
            snapshot["truncated"] = True
        snapshot[key] = items[:MAX_ITEMS]

    # -- VPCs -----------------------------------------------------------
    cap("networks", [
        {
            "id": vpc["VpcId"],
            "name": _name_tag(vpc) or ("Default VPC" if vpc.get("IsDefault") else vpc["VpcId"]),
            "cidr": vpc.get("CidrBlock"),
            "kind": "vpc",
            "location": region,
        }
        for vpc in read(API_DESCRIBE_VPCS, "describe_vpcs", "Vpcs")
        if vpc.get("VpcId")
    ])

    # -- Subnets --------------------------------------------------------
    cap("subnets", [
        {
            "id": subnet["SubnetId"],
            "name": _name_tag(subnet) or subnet["SubnetId"],
            "cidr": subnet.get("CidrBlock"),
            "network_id": subnet.get("VpcId"),
            # AWS's own flag: instances launched here get a public address.
            "public": bool(subnet.get("MapPublicIpOnLaunch")),
            "availability_zone": subnet.get("AvailabilityZone"),
        }
        for subnet in read(API_DESCRIBE_SUBNETS, "describe_subnets", "Subnets")
        if subnet.get("SubnetId")
    ])

    # -- Security groups --------------------------------------------------
    cap("security_groups", [
        {
            "id": group["GroupId"],
            "name": _name_tag(group) or group.get("GroupName") or group["GroupId"],
            "network_id": group.get("VpcId"),
            "open_ports": open_ports_for(group.get("IpPermissions")),
        }
        for group in read(API_DESCRIBE_SECURITY_GROUPS, "describe_security_groups", "SecurityGroups")
        if group.get("GroupId")
    ])

    # -- Gateways -------------------------------------------------------
    gateways: List[Dict[str, Any]] = []
    for igw in read(API_DESCRIBE_INTERNET_GATEWAYS, "describe_internet_gateways", "InternetGateways"):
        if not igw.get("InternetGatewayId"):
            continue
        gateways.append({
            "id": igw["InternetGatewayId"],
            "name": _name_tag(igw) or igw["InternetGatewayId"],
            "kind": "internet_gateway",
            "network_id": _attached_vpc(igw.get("Attachments")),
            "to_internet": True,
        })
    for nat in read(API_DESCRIBE_NAT_GATEWAYS, "describe_nat_gateways", "NatGateways"):
        if not nat.get("NatGatewayId") or _state(nat.get("State")) in _GONE:
            continue
        addresses = [a for a in nat.get("NatGatewayAddresses") or [] if isinstance(a, dict)]
        gateways.append({
            "id": nat["NatGatewayId"],
            "name": _name_tag(nat) or nat["NatGatewayId"],
            "kind": "nat_gateway",
            "network_id": nat.get("VpcId"),
            "public_ip": next((a.get("PublicIp") for a in addresses if a.get("PublicIp")), None),
            # A "private" NAT gateway only reaches other private networks.
            "to_internet": str(nat.get("ConnectivityType") or "public").lower() != "private",
        })
    vgw_network: Dict[str, Optional[str]] = {}
    for vgw in read(API_DESCRIBE_VPN_GATEWAYS, "describe_vpn_gateways", "VpnGateways"):
        if not vgw.get("VpnGatewayId") or _state(vgw.get("State")) in _GONE:
            continue
        vgw_network[vgw["VpnGatewayId"]] = _attached_vpc(vgw.get("VpcAttachments"))
        gateways.append({
            "id": vgw["VpnGatewayId"],
            "name": _name_tag(vgw) or vgw["VpnGatewayId"],
            "kind": "vpn_gateway",
            "network_id": vgw_network[vgw["VpnGatewayId"]],
            "to_internet": False,
        })
    for cgw in read(API_DESCRIBE_CUSTOMER_GATEWAYS, "describe_customer_gateways", "CustomerGateways"):
        if not cgw.get("CustomerGatewayId") or _state(cgw.get("State")) in _GONE:
            continue
        gateways.append({
            "id": cgw["CustomerGatewayId"],
            "name": _name_tag(cgw) or cgw.get("DeviceName") or cgw["CustomerGatewayId"],
            "kind": "customer_gateway",
            "network_id": None,
            "public_ip": cgw.get("IpAddress"),
            "to_internet": False,
        })
    # Best effort: many accounts cannot (or need not) read transit gateways.
    for tgw in read(API_DESCRIBE_TRANSIT_GATEWAYS, "describe_transit_gateways", "TransitGateways"):
        if not tgw.get("TransitGatewayId") or _state(tgw.get("State")) in _GONE:
            continue
        gateways.append({
            "id": tgw["TransitGatewayId"],
            "name": _name_tag(tgw) or tgw.get("Description") or tgw["TransitGatewayId"],
            "kind": "transit_gateway",
            "network_id": None,
            "to_internet": False,
        })
    cap("gateways", gateways)

    # -- VPNs -----------------------------------------------------------
    vpns: List[Dict[str, Any]] = []
    for vpn in read(API_DESCRIBE_VPN_CONNECTIONS, "describe_vpn_connections", "VpnConnections"):
        if not vpn.get("VpnConnectionId") or _state(vpn.get("State")) in _GONE:
            continue
        gateway_id = vpn.get("VpnGatewayId") or vpn.get("TransitGatewayId")
        vpns.append({
            "id": vpn["VpnConnectionId"],
            "name": _name_tag(vpn) or vpn["VpnConnectionId"],
            "kind": "site_to_site",
            "state": _state(vpn.get("State")),
            "network_id": vgw_network.get(vpn.get("VpnGatewayId") or ""),
            "gateway_id": gateway_id,
            "remote_gateway_id": vpn.get("CustomerGatewayId"),
            "remote_network_id": None,
            "tunnels": [
                {
                    "status": str(tunnel.get("Status") or "").upper(),
                    "outside_ip": tunnel.get("OutsideIpAddress"),
                    "last_change": _iso(tunnel.get("LastStatusChange")),
                }
                for tunnel in vpn.get("VgwTelemetry") or []
                if isinstance(tunnel, dict)
            ],
        })
    endpoints = read(API_DESCRIBE_CLIENT_VPN_ENDPOINTS, "describe_client_vpn_endpoints", "ClientVpnEndpoints")
    for position, endpoint in enumerate(endpoints):
        endpoint_id = endpoint.get("ClientVpnEndpointId")
        if not endpoint_id or _state(endpoint.get("Status")) in _GONE:
            continue
        active: Optional[int] = None
        if position < _MAX_CLIENT_VPN_CONNECTION_LOOKUPS and API_DESCRIBE_CLIENT_VPN_CONNECTIONS not in denied:
            before = len(denied) + len(failed) + len(cut_short)
            connections = read(
                API_DESCRIBE_CLIENT_VPN_CONNECTIONS,
                "describe_client_vpn_connections",
                "Connections",
                ClientVpnEndpointId=endpoint_id,
            )
            # Only report a count that is complete: no error and no cut-off.
            if len(denied) + len(failed) + len(cut_short) == before:
                active = sum(1 for c in connections if _state(c.get("Status")) == "active")
        vpns.append({
            "id": endpoint_id,
            "name": _name_tag(endpoint) or endpoint.get("Description") or endpoint_id,
            "kind": "client",
            "state": _state(endpoint.get("Status")),
            "network_id": endpoint.get("VpcId"),
            "gateway_id": None,
            "remote_gateway_id": None,
            "remote_network_id": None,
            "tunnels": [],
            "active_connections": active,
        })
    cap("vpns", vpns)

    # -- Peerings -------------------------------------------------------
    peerings: List[Dict[str, Any]] = []
    for peering in read(
        API_DESCRIBE_VPC_PEERING_CONNECTIONS, "describe_vpc_peering_connections", "VpcPeeringConnections"
    ):
        requester = peering.get("RequesterVpcInfo") if isinstance(peering.get("RequesterVpcInfo"), dict) else {}
        accepter = peering.get("AccepterVpcInfo") if isinstance(peering.get("AccepterVpcInfo"), dict) else {}
        if not (peering.get("VpcPeeringConnectionId") and requester.get("VpcId") and accepter.get("VpcId")):
            continue
        peerings.append({
            "id": peering["VpcPeeringConnectionId"],
            "a_network_id": requester["VpcId"],
            "b_network_id": accepter["VpcId"],
            "state": _state(peering.get("Status")),
        })
    cap("peerings", peerings)

    if cut_short:
        snapshot["truncated"] = True
    return snapshot
