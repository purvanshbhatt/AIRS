"""
Scripted network layout for the explicit demo organizations.

The recorded AWS fixtures carry servers and findings but no network layout,
so the demo map gets ONE scripted ``network.snapshot`` event per industry:
an office network, a guest Wi-Fi, a cloud VPC with a private and a public
subnet, the office firewall, an internet gateway, a site-to-site VPN with
one tunnel down and a remote-access VPN with two staff laptops.

Everything here is marked ``"sample": True`` so the map can label it as
sample data. It is only ever produced by ``get_demo_telemetry`` for demo
organizations, never for a real one.

The recorded EC2 instances are placed by their real instance ids (read from
the fixture, so the two stay in sync) and the scripted Intune workstation is
placed by name. Addresses use RFC 1918 ranges and the 203.0.113.0/24
documentation range.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.services.clinic_engine.v2.schema import RawEvent
from app.services.demo.aws_demo_telemetry import _industry_for, load_recorded_fixture

_WORKSTATION_ROLE_HINTS = ("workstation", "laptop", "vdi", "desktop")

_PROFILES: Dict[str, Dict[str, Any]] = {
    "healthcare": {
        "slug": "metro-health",
        "office_name": "Clinic office network",
        "office_location": "Main clinic",
        "firewall_name": "Clinic firewall and router",
        "s2s_name": "Clinic office to AWS VPN",
        "client_vpn_name": "Remote staff VPN",
        "remote_laptops": ["DR-SMITH-HOME-LAPTOP", "NURSE-REMOTE-LAPTOP"],
        # (role of the app server the front desk talks to, role it sends data on to, port label)
        "app_role": "ehr-app-server",
        "downstream_role": "backup-server",
        "downstream_label": "tcp/22",
    },
    "legal": {
        "slug": "northstar-cole",
        "office_name": "Law office network",
        "office_location": "Northstar Cole office",
        "firewall_name": "Office firewall and router",
        "s2s_name": "Law office to AWS VPN",
        "client_vpn_name": "Remote attorney VPN",
        "remote_laptops": ["PARTNER-REED-HOME-LAPTOP", "PARALEGAL-REMOTE-LAPTOP"],
        "app_role": "dms-matter-server",
        "downstream_role": "file-server",
        "downstream_label": "tcp/445",
    },
}


def _fixture_instances(industry: str) -> List[Dict[str, Any]]:
    """EC2 instances recorded in the industry fixture: [{instance_id, name, role}]."""
    fixture = load_recorded_fixture(industry) or {}
    instances = []
    for res in fixture.get("resources") or []:
        if isinstance(res, dict) and res.get("kind") == "ec2_instance" and res.get("instance_id"):
            instances.append({
                "instance_id": res["instance_id"],
                "name": res.get("name") or res["instance_id"],
                "role": str(res.get("role") or ""),
            })
    return instances


def build_demo_network_snapshot(
    org_id: str,
    workstation_name: str,
    now: Optional[datetime] = None,
) -> RawEvent:
    """The scripted ``network.snapshot`` event for a demo organization.

    Args:
        org_id: demo organization id (decides healthcare vs legal).
        workstation_name: device name of the scripted Intune workstation, so
            the office PC lands on the office network by name.
        now: clock override for tests.
    """
    now = now or datetime.now(timezone.utc)
    industry = _industry_for(org_id)
    profile = _PROFILES[industry]
    slug = profile["slug"]

    office, wifi, vpc = "office-lan", "guest-wifi", f"vpc-{slug}"
    private_subnet, public_subnet = f"subnet-{slug}-private", f"subnet-{slug}-public"
    firewall, igw = "office-firewall", f"igw-{slug}"
    s2s_vpn, client_vpn = f"vpn-{slug}-office", f"cvpn-{slug}-staff"

    devices: List[Dict[str, Any]] = [{
        "id": "office-workstation",
        "name": workstation_name,          # matches the scripted Intune device by name
        "kind": "workstation",
        "ip": "192.168.10.23",
        "network_id": office,
        "last_seen": (now - timedelta(minutes=4)).isoformat(),
    }]
    by_role: Dict[str, str] = {}
    for instance in _fixture_instances(industry):
        role = instance["role"]
        is_workstation = any(hint in role for hint in _WORKSTATION_ROLE_HINTS)
        device_id = f"ec2-{role or instance['instance_id']}"
        by_role[role] = device_id
        devices.append({
            "id": device_id,
            "name": instance["name"],
            "instance_id": instance["instance_id"],   # resolves to the recorded EC2 node
            "network_id": vpc,
            "subnet_id": public_subnet if is_workstation else private_subnet,
            "provider": "aws",
        })
    for position, laptop in enumerate(profile["remote_laptops"], start=1):
        devices.append({
            "id": f"remote-laptop-{position}",
            "name": laptop,
            "kind": "laptop",
            "os": "Windows 11",
            "via_vpn_id": client_vpn,
            "last_seen": (now - timedelta(minutes=10 * position)).isoformat(),
        })

    links: List[Dict[str, Any]] = []
    app_device = by_role.get(profile["app_role"])
    downstream_device = by_role.get(profile["downstream_role"])
    if app_device:
        links.append({"source": "office-workstation", "target": app_device, "kind": "talks_to", "label": "tcp/443"})
        links.append({"source": "remote-laptop-1", "target": app_device, "kind": "talks_to", "label": "tcp/443"})
    if app_device and downstream_device:
        links.append({
            "source": app_device, "target": downstream_device,
            "kind": "talks_to", "label": profile["downstream_label"],
        })

    payload: Dict[str, Any] = {
        "provider": "manual",
        "sample": True,
        "networks": [
            {"id": office, "name": profile["office_name"], "cidr": "192.168.10.0/24",
             "kind": "office_lan", "location": profile["office_location"]},
            {"id": wifi, "name": "Guest Wi-Fi", "cidr": "192.168.50.0/24",
             "kind": "wifi", "location": profile["office_location"]},
            {"id": vpc, "name": f"{slug}-vpc", "cidr": "10.20.0.0/16",
             "kind": "vpc", "location": "us-east-1", "provider": "aws"},
        ],
        "subnets": [
            {"id": private_subnet, "name": f"{slug}-private-subnet", "cidr": "10.20.1.0/24",
             "network_id": vpc, "public": False, "availability_zone": "us-east-1a", "provider": "aws"},
            {"id": public_subnet, "name": f"{slug}-public-subnet", "cidr": "10.20.0.0/24",
             "network_id": vpc, "public": True, "availability_zone": "us-east-1a", "provider": "aws"},
        ],
        "gateways": [
            {"id": firewall, "name": profile["firewall_name"], "kind": "firewall",
             "network_id": office, "network_ids": [wifi], "public_ip": "203.0.113.10", "to_internet": True},
            {"id": igw, "name": f"{slug}-internet-gateway", "kind": "internet_gateway",
             "network_id": vpc, "to_internet": True, "provider": "aws"},
        ],
        "vpns": [
            {
                "id": s2s_vpn, "name": profile["s2s_name"], "kind": "site_to_site", "state": "available",
                "network_id": vpc, "remote_gateway_id": firewall, "provider": "aws",
                "tunnels": [
                    {"status": "UP", "outside_ip": "203.0.113.21",
                     "last_change": (now - timedelta(days=9)).isoformat()},
                    {"status": "DOWN", "outside_ip": "203.0.113.22",
                     "last_change": (now - timedelta(hours=3)).isoformat()},
                ],
            },
            {
                "id": client_vpn, "name": profile["client_vpn_name"], "kind": "client", "state": "available",
                "network_id": vpc, "active_connections": len(profile["remote_laptops"]), "provider": "aws",
            },
        ],
        "devices": devices,
        "links": links,
    }

    return RawEvent(
        event_type="network.snapshot",
        # A firewall / VPN tool pushes this through the webhook connector.
        source_system="webhook",
        source_event_id=f"sync-net-{int(time.time())}",
        organization_id=org_id,
        payload=payload,
        timestamp=now.isoformat(),
    )
