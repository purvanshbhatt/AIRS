"""
Network topology — builder unit tests and /api/v1/network/topology contract.

Covers:
  * demo org → real recorded findings drive the map (servers + internet exposure)
  * real org with nothing connected → empty graph with a plain-language hint
  * foreign org → 404 (no data leak across tenants)
  * builder over a handful of synthetic events (merging, statuses, edges)
  * network snapshots (networks, subnets, gateways, VPNs, security groups,
    devices, observed traffic, peerings), device resolution and ordering
  * VPN status rules, inferred /24 networks, Wazuh and Splunk handlers
  * the ``live`` block and the network counters in ``summary``
  * demo organizations get the scripted sample network layout
  * a pushed ``network.snapshot`` is stored unchanged and drawn
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.core.auth import User, get_optional_user
from app.models.organization import Organization
from app.services.network_topology import (
    EDGE_KINDS,
    INTERNET_NODE_ID,
    NODE_TYPES,
    ZONES,
    TopologyBuilder,
    build_topology,
    build_topology_for_org,
    parse_arn,
    zone_for_hint,
)


# ---------------------------------------------------------------------------
# Builder (pure, synthetic events)
# ---------------------------------------------------------------------------

def _ev(event_type, source, payload, ts=None):
    return {
        "event_type": event_type,
        "source_system": source,
        "source_event_id": f"{event_type}-{id(payload)}",
        "payload": payload,
        "timestamp": ts or datetime.now(timezone.utc).isoformat(),
    }


SG_ARN = "arn:aws:ec2:us-east-1:123456789012:security-group/sg-0abc"
INSTANCE_ARN = "arn:aws:ec2:us-east-1:123456789012:instance/i-0web"
BUCKET_ARN = "arn:aws:s3:::acme-records"


def _synthetic_events():
    now = datetime.now(timezone.utc)
    return [
        _ev("aws.securityhub.finding", "aws_security_hub", {
            "title": "Security groups should not allow unrestricted access to ports with high risk",
            "description": "Fails if a rule allows ingress from '0.0.0.0/0' to risky ports.",
            "severity_label": "critical",
            "resources": [SG_ARN],
        }),
        _ev("aws.securityhub.finding", "aws_security_hub", {
            "title": "EC2 instance queried a known command and control domain",
            "severity_label": "high",
            "resources": [INSTANCE_ARN],
        }),
        _ev("aws.securityhub.finding", "aws_security_hub", {
            "title": "S3 Block Public Access was disabled",
            "severity_label": "low",
            "resources": [BUCKET_ARN],
        }),
        _ev("aws.inventory.snapshot", "aws", {
            "resources": [
                {"kind": "ec2_instance", "instance_id": "i-0web", "name": "acme-web-server", "role": "web-server", "state": "running", "instance_type": "t3.micro"},
                {"kind": "ec2_instance", "instance_id": "i-0bak", "name": "acme-backup-server", "role": "backup-server", "state": "running"},
                {"kind": "ec2_instance", "instance_id": "i-0desk", "name": "acme-front-desk-workstation", "role": "front-desk-workstation", "state": "running"},
                {"kind": "rds_instance", "identifier": "acme-db", "name": "acme-db", "engine": "postgres"},
            ],
        }),
        _ev("microsoft.telemetry", "microsoft", {
            "entra_users": [
                {"user_id": "u-1", "user_principal_name": "owner@acme.test", "mfa_enforced": True, "account_enabled": True, "last_sign_in": now.isoformat()},
                {"user_id": "u-2", "user_principal_name": "old@acme.test", "mfa_enforced": False, "account_enabled": True, "last_sign_in": (now - timedelta(days=60)).isoformat()},
            ],
            "intune_devices": [
                {"device_id": "d-1", "device_name": "RECEPTION-PC", "compliance_state": "noncompliant", "bitlocker_status": "not_encrypted"},
            ],
            "defender_alerts": [
                {"alert_id": "a-1", "title": "Suspicious PowerShell", "severity": "high", "device_id": "d-1"},
            ],
        }),
        _ev("veeam.backup_job", "veeam", {
            "system_name": "acme-db",
            "last_successful_backup": (now - timedelta(hours=30)).isoformat(),
            "backup_type": "full",
        }),
    ]


class TestTopologyBuilder:
    def test_empty_inputs_yield_empty_graph(self):
        topo = build_topology("org-x")
        assert topo["nodes"] == []
        assert topo["edges"] == []
        assert topo["summary"]["empty"] is True
        assert topo["summary"]["hint"] == "connect a system"
        assert "generated_at" in topo

    def test_synthetic_events_build_expected_nodes_and_edges(self):
        topo = build_topology("org-x", events=_synthetic_events())
        nodes = {n["id"]: n for n in topo["nodes"]}
        edges = {(e["source"], e["target"], e["kind"]) for e in topo["edges"]}

        # Internet exposure from an open security group.
        assert INTERNET_NODE_ID in nodes
        assert (INTERNET_NODE_ID, "aws:sg:sg-0abc", "exposed_to_internet") in edges
        assert nodes["aws:sg:sg-0abc"]["status"] == "attention"

        # Finding on a bare ARN merged with the inventory record (name wins).
        web = nodes["aws:instance:i-0web"]
        assert web["label"] == "acme-web-server"
        assert web["status"] == "attention"            # high severity finding
        assert web["type"] == "server" and web["zone"] == "servers"
        assert any("command and control" in i["title"] for i in web["meta"]["issues"])

        # Zone hints from role tags.
        assert nodes["aws:instance:i-0bak"]["zone"] == "backups"
        assert nodes["aws:instance:i-0desk"]["zone"] == "workstations"
        assert nodes["aws:instance:i-0desk"]["type"] == "workstation"
        assert nodes["aws:db:acme-db"]["type"] == "database"
        assert nodes["aws:db:acme-db"]["zone"] == "data"

        # Low severity finding → warning, not attention.
        assert nodes["aws:bucket:acme-records"]["status"] == "warning"

        # Identities + authenticates edges; MFA gap flagged.
        assert nodes["ms:user:u-2"]["status"] == "attention"
        assert nodes["ms:user:u-1"]["status"] == "healthy"
        assert ("connector:microsoft", "ms:user:u-1", "authenticates") in edges

        # Device with a Defender alert is attention; monitored by Microsoft.
        assert nodes["ms:device:d-1"]["status"] == "attention"
        assert nodes["ms:device:d-1"]["zone"] == "workstations"
        assert ("connector:microsoft", "ms:device:d-1", "monitors") in edges

        # Backup job attaches to the existing database node by name and flags staleness.
        assert ("connector:veeam", "aws:db:acme-db", "backs_up") in edges
        assert any("24 hours" in i["title"] for i in nodes["aws:db:acme-db"]["meta"]["issues"])

        # Connectors appear as virtual nodes when none are registered.
        connector_ids = {n["id"] for n in topo["nodes"] if n["type"] == "connector"}
        assert {"connector:aws_security_hub", "connector:microsoft", "connector:veeam"} <= connector_ids

        summary = topo["summary"]
        assert summary["empty"] is False
        assert summary["internet_exposed"] == 1
        assert summary["by_type"]["server"] >= 1
        assert summary["attention"] >= 3

    def test_registered_connector_is_used_instead_of_virtual_node(self):
        connector = {
            "id": "c-1", "connector_type": "aws_security_hub", "display_name": "Prod AWS",
            "status": "active", "health_status": "healthy", "last_sync_at": datetime.now(timezone.utc),
        }
        topo = build_topology("org-x", connectors=[connector], events=_synthetic_events()[:1])
        ids = {n["id"] for n in topo["nodes"]}
        assert "connector:c-1" in ids
        assert "connector:aws_security_hub" not in ids
        assert ("connector:c-1", "aws:sg:sg-0abc") in {(e["source"], e["target"]) for e in topo["edges"]}

    def test_host_assets_become_nodes(self):
        asset = {"id": "a-1", "hostname": "ehr-db-01", "asset_type": "CLOUD_SERVICE", "cloud_provider": "AWS",
                 "operating_system": "Linux", "ip_address": "10.0.0.5", "last_seen": datetime.now(timezone.utc)}
        topo = build_topology("org-x", assets=[asset])
        node = next(n for n in topo["nodes"] if n["id"] == "asset:a-1")
        assert node["type"] == "database"
        assert node["zone"] == "data"
        assert node["meta"]["ip_address"] == "10.0.0.5"
        assert any(e["kind"] == "monitors" and e["target"] == "asset:a-1" for e in topo["edges"])

    def test_malformed_event_is_skipped(self):
        topo = build_topology("org-x", events=[{"event_type": "aws.securityhub.finding", "payload": "{not json"}])
        assert topo["summary"]["empty"] is True

    def test_helpers(self):
        assert parse_arn(SG_ARN)["resource_type"] == "security-group"
        assert parse_arn(BUCKET_ARN)["resource_id"] == "acme-records"
        assert parse_arn("nope") is None
        assert zone_for_hint("partner-laptop") == "workstations"
        assert zone_for_hint("nightly-backup") == "backups"
        assert zone_for_hint("rds-primary") == "data"
        assert zone_for_hint("app") == "servers"


# ---------------------------------------------------------------------------
# Network snapshots
# ---------------------------------------------------------------------------

def _graph(topo):
    nodes = {n["id"]: n for n in topo["nodes"]}
    edges = {(e["source"], e["target"], e["kind"]) for e in topo["edges"]}
    return nodes, edges


def _edge(topo, source, target, kind):
    return next(e for e in topo["edges"] if (e["source"], e["target"], e["kind"]) == (source, target, kind))


def _inventory_event(ts=None):
    return _ev("aws.inventory.snapshot", "aws", {"resources": [
        {"kind": "ec2_instance", "instance_id": "i-0app", "name": "clinic-app-server", "role": "app-server", "state": "running"},
    ]}, ts)


def _intune_event():
    return _ev("microsoft.telemetry", "microsoft", {"intune_devices": [
        {"device_id": "d-9", "device_name": "FRONT-DESK-PC", "compliance_state": "compliant"},
    ]})


def _full_snapshot(**overrides):
    payload = {
        "provider": "unifi",
        "networks": [
            {"id": "lan", "name": "Office LAN", "cidr": "192.168.10.0/24", "kind": "office_lan", "location": "HQ"},
            {"id": "guest", "name": "Guest Wi-Fi", "cidr": "192.168.50.0/24", "kind": "wifi"},
            {"id": "vpc-1", "name": "clinic-vpc", "cidr": "10.0.0.0/16", "kind": "vpc", "provider": "aws"},
            {"id": "vpc-2", "name": "shared-vpc", "cidr": "10.1.0.0/16", "provider": "aws"},
        ],
        "subnets": [
            {"id": "subnet-a", "name": "private-a", "cidr": "10.0.1.0/24", "network_id": "vpc-1",
             "public": False, "availability_zone": "us-east-1a", "provider": "aws"},
        ],
        "gateways": [
            {"id": "fw", "name": "Office firewall", "kind": "firewall", "network_id": "lan",
             "network_ids": ["guest"], "public_ip": "203.0.113.10", "to_internet": True},
            {"id": "igw-1", "kind": "internet_gateway", "network_id": "vpc-1", "provider": "aws"},
            {"id": "nat-private", "kind": "nat_gateway", "network_id": "vpc-1", "to_internet": False, "provider": "aws"},
            {"id": "vgw-1", "kind": "vpn_gateway", "network_id": "vpc-1", "provider": "aws"},
        ],
        "vpns": [
            {"id": "vpn-1", "name": "Office to AWS", "kind": "site_to_site", "state": "available",
             "gateway_id": "vgw-1", "network_id": "vpc-1", "remote_gateway_id": "fw", "provider": "aws",
             "tunnels": [{"status": "UP", "outside_ip": "203.0.113.21"}, {"status": "DOWN", "outside_ip": "203.0.113.22"}]},
            {"id": "cvpn-1", "name": "Remote staff", "kind": "client", "state": "available",
             "network_id": "vpc-1", "active_connections": 1, "provider": "aws"},
        ],
        "security_groups": [
            {"id": "sg-web", "name": "web", "network_id": "vpc-1", "open_ports": ["tcp/22", "tcp/443"], "provider": "aws"},
            {"id": "sg-db", "name": "db", "network_id": "vpc-1", "open_ports": [], "provider": "aws"},
        ],
        "devices": [
            {"id": "app", "name": "clinic-app-server", "instance_id": "i-0app", "network_id": "vpc-1",
             "subnet_id": "subnet-a", "security_group_ids": ["sg-web"], "ip": "10.0.1.20", "provider": "aws"},
            {"id": "desk", "name": "front-desk-pc", "ip": "192.168.10.23", "network_id": "lan"},
            {"id": "nas", "name": "office-nas-01", "kind": "server", "ip": "192.168.10.5", "network_id": "lan",
             "os": "TrueNAS", "last_seen": "2026-11-09T10:00:00+00:00"},
            {"id": "laptop", "name": "REMOTE-LAPTOP-1", "kind": "laptop", "via_vpn_id": "cvpn-1"},
        ],
        "links": [
            {"source": "desk", "target": "app", "kind": "talks_to", "label": "tcp/443"},
            {"source": "app", "target": "net:device:unifi:nas", "kind": "talks_to", "label": "tcp/22"},
            {"source": "ghost", "target": "app", "kind": "talks_to"},
        ],
        "peerings": [
            {"id": "pcx-1", "a_network_id": "vpc-1", "b_network_id": "vpc-2", "state": "active"},
            {"id": "pcx-2", "a_network_id": "vpc-1", "b_network_id": "vpc-gone", "state": "deleted"},
        ],
    }
    payload.update(overrides)
    return payload


class TestNetworkSnapshot:
    def test_vocabulary_covers_the_infrastructure_layer(self):
        assert {"network", "subnet", "vpn", "gateway"} <= set(NODE_TYPES)
        assert "network" in ZONES
        assert {"member_of", "part_of", "vpn_tunnel", "routes_to", "protects", "talks_to"} <= set(EDGE_KINDS)

    def test_snapshot_builds_every_node_and_edge_kind(self):
        topo = build_topology("org-x", events=[
            _inventory_event(), _intune_event(), _ev("network.snapshot", "webhook", _full_snapshot()),
        ])
        nodes, edges = _graph(topo)

        # Networks (per-item provider overrides the snapshot's).
        lan = nodes["net:unifi:lan"]
        assert (lan["type"], lan["zone"], lan["label"]) == ("network", "network", "Office LAN")
        assert lan["meta"]["cidr"] == "192.168.10.0/24"
        assert lan["meta"]["network_kind"] == "office_lan"
        assert lan["meta"]["location"] == "HQ"
        assert nodes["net:unifi:guest"]["meta"]["network_kind"] == "wifi"
        assert nodes["net:aws:vpc-1"]["meta"]["network_kind"] == "vpc"
        assert nodes["net:aws:vpc-2"]["meta"]["network_kind"] == "vpc"      # AWS network without a kind

        # Subnet.
        subnet = nodes["subnet:aws:subnet-a"]
        assert (subnet["type"], subnet["zone"]) == ("subnet", "network")
        assert subnet["meta"]["cidr"] == "10.0.1.0/24"
        assert subnet["meta"]["network_id"] == "vpc-1"
        assert subnet["meta"]["public"] is False
        assert subnet["meta"]["availability_zone"] == "us-east-1a"
        assert ("subnet:aws:subnet-a", "net:aws:vpc-1", "part_of") in edges

        # Gateways.
        firewall = nodes["gw:unifi:fw"]
        assert (firewall["type"], firewall["zone"]) == ("gateway", "network")
        assert firewall["meta"]["gateway_kind"] == "firewall"
        assert firewall["meta"]["public_ip"] == "203.0.113.10"
        assert ("net:unifi:lan", "gw:unifi:fw", "routes_to") in edges
        assert ("net:unifi:guest", "gw:unifi:fw", "routes_to") in edges
        assert ("gw:unifi:fw", INTERNET_NODE_ID, "routes_to") in edges          # to_internet: true
        assert ("gw:aws:igw-1", INTERNET_NODE_ID, "routes_to") in edges         # by kind
        assert ("gw:aws:nat-private", INTERNET_NODE_ID, "routes_to") not in edges  # explicit false wins
        assert ("gw:aws:vgw-1", INTERNET_NODE_ID, "routes_to") not in edges
        assert nodes["gw:aws:vgw-1"]["meta"]["gateway_kind"] == "vpn_gateway"

        # VPNs: each end goes to the gateway when one is named, else the network.
        vpn = nodes["vpn:aws:vpn-1"]
        assert (vpn["type"], vpn["zone"]) == ("vpn", "network")
        assert vpn["meta"]["vpn_kind"] == "site_to_site"
        assert (vpn["meta"]["tunnels_up"], vpn["meta"]["tunnels_total"]) == (1, 2)
        assert ("vpn:aws:vpn-1", "gw:aws:vgw-1", "vpn_tunnel") in edges
        assert ("vpn:aws:vpn-1", "gw:unifi:fw", "vpn_tunnel") in edges
        assert ("vpn:aws:vpn-1", "net:aws:vpc-1", "vpn_tunnel") not in edges
        assert _edge(topo, "vpn:aws:vpn-1", "gw:unifi:fw", "vpn_tunnel")["label"] == "1 of 2 tunnels up"
        client = nodes["vpn:aws:cvpn-1"]
        assert client["meta"]["vpn_kind"] == "client"
        assert client["meta"]["active_connections"] == 1
        assert "tunnels_total" not in client["meta"]
        assert ("vpn:aws:cvpn-1", "net:aws:vpc-1", "vpn_tunnel") in edges
        assert ("net:device:unifi:laptop", "vpn:aws:cvpn-1", "vpn_tunnel") in edges   # remote device -> client VPN

        # Security groups: AWS ids are kept; open ports expose the group.
        web = nodes["aws:sg:sg-web"]
        assert (web["type"], web["label"]) == ("security_group", "web")
        assert web["meta"]["open_ports"] == ["tcp/22", "tcp/443"]
        assert web["meta"]["internet_exposed"] is True
        assert web["meta"]["network_id"] == "vpc-1"
        assert (INTERNET_NODE_ID, "aws:sg:sg-web", "exposed_to_internet") in edges
        assert (INTERNET_NODE_ID, "aws:sg:sg-db", "exposed_to_internet") not in edges
        assert "open_ports" not in nodes["aws:sg:sg-db"]["meta"]
        assert ("aws:sg:sg-web", "aws:instance:i-0app", "protects") in edges

        # Devices on networks.
        assert ("aws:instance:i-0app", "subnet:aws:subnet-a", "member_of") in edges   # subnet wins over network
        assert ("aws:instance:i-0app", "net:aws:vpc-1", "member_of") not in edges
        assert ("ms:device:d-9", "net:unifi:lan", "member_of") in edges
        assert ("net:device:unifi:nas", "net:unifi:lan", "member_of") in edges
        assert nodes["aws:instance:i-0app"]["meta"]["ip_address"] == "10.0.1.20"
        assert nodes["aws:instance:i-0app"]["meta"]["network_id"] == "vpc-1"
        assert nodes["aws:instance:i-0app"]["meta"]["subnet_id"] == "subnet-a"

        # Observed traffic: device ids of the snapshot, or raw node ids.
        assert ("ms:device:d-9", "aws:instance:i-0app", "talks_to") in edges
        assert _edge(topo, "ms:device:d-9", "aws:instance:i-0app", "talks_to")["label"] == "tcp/443"
        assert ("aws:instance:i-0app", "net:device:unifi:nas", "talks_to") in edges
        assert sum(1 for e in topo["edges"] if e["kind"] == "talks_to") == 2     # unknown end is dropped

        # Peering: only the live one, labelled.
        assert _edge(topo, "net:aws:vpc-1", "net:aws:vpc-2", "routes_to")["label"] == "peering"
        assert "net:aws:vpc-gone" not in nodes

        # Every edge joins two existing nodes and uses the shared vocabulary.
        for e in topo["edges"]:
            assert e["source"] in nodes and e["target"] in nodes
            assert e["kind"] in EDGE_KINDS
        for n in topo["nodes"]:
            assert n["type"] in NODE_TYPES and n["zone"] in ZONES
        assert not any(n["meta"].get("sample") for n in topo["nodes"])
        assert not any(n["meta"].get("inferred") for n in topo["nodes"])

        summary = topo["summary"]
        assert summary["networks"] == 4
        assert summary["vpns"] == 2
        assert summary["vpn_down"] == 0
        assert summary["by_type"]["gateway"] == 4

    def test_device_resolution_order(self):
        snapshot = {
            "provider": "microsoft",
            "networks": [{"id": "lan", "name": "Office LAN", "cidr": "192.168.10.0/24", "kind": "office_lan"}],
            "devices": [
                {"id": "a", "name": "renamed-in-snapshot", "instance_id": "i-0app", "network_id": "lan"},     # existing instance
                {"id": "b", "name": "new-web-server", "instance_id": "i-0new", "network_id": "lan"},            # bare instance
                {"id": "c", "name": "Front-Desk-PC", "device_id": "d-9", "network_id": "lan"},                  # existing Intune
                {"id": "d", "name": "ACCOUNTS-LAPTOP", "device_id": "d-77", "network_id": "lan"},               # bare Intune
                {"id": "e", "name": "CLINIC-APP-SERVER", "network_id": "lan"},                                  # by label
                {"id": "f", "name": "reception-laptop-2", "network_id": "lan", "os": "Windows 11"},             # new device
                {"id": "g", "name": "print-server", "network_id": "lan"},                                       # new device
                {"id": "h", "name": "billing-db-01", "network_id": "lan"},                                      # new device
            ],
        }
        topo = build_topology("org-x", events=[
            _inventory_event(), _intune_event(), _ev("network.snapshot", "webhook", snapshot),
        ])
        nodes, edges = _graph(topo)

        # instance_id -> the inventory node, whose own name is kept.
        assert nodes["aws:instance:i-0app"]["label"] == "clinic-app-server"
        # instance_id not in inventory -> bare AWS instance node.
        assert nodes["aws:instance:i-0new"]["label"] == "new-web-server"
        assert nodes["aws:instance:i-0new"]["status"] == "unknown"
        # device_id with provider microsoft -> the Intune node (matched by id, not name).
        assert nodes["ms:device:d-9"]["label"] == "FRONT-DESK-PC"
        assert nodes["ms:device:d-77"]["type"] == "workstation"
        # "e" has no ids: matched case-insensitively by label, so no new node.
        assert ("aws:instance:i-0app", "net:microsoft:lan", "member_of") in edges
        assert "net:device:microsoft:e" not in nodes
        # Unknown machines become net:device:<provider>:<id>, typed by hint.
        assert nodes["net:device:microsoft:f"]["type"] == "workstation"
        assert nodes["net:device:microsoft:f"]["zone"] == "workstations"
        assert nodes["net:device:microsoft:g"]["type"] == "server"
        assert nodes["net:device:microsoft:h"]["type"] == "database"
        assert nodes["net:device:microsoft:h"]["zone"] == "data"
        # A device reported only by a feed is monitored by that feed.
        assert ("connector:webhook", "net:device:microsoft:g", "monitors") in edges
        assert sum(1 for n in topo["nodes"] if n["type"] in ("server", "workstation", "database")) == 7

    def test_snapshot_only_device_is_bare_and_upgraded_by_later_inventory(self):
        builder = TopologyBuilder("org-x")
        builder.add_events([_ev("network.snapshot", "webhook", {
            "provider": "aws",
            "networks": [{"id": "vpc-1", "name": "clinic-vpc"}],
            "devices": [{"id": "x", "instance_id": "i-0app", "network_id": "vpc-1"}],
        })])
        assert builder.nodes["aws:instance:i-0app"]["label"] == "i-0app"
        builder.add_events([_inventory_event()])
        node = builder.nodes["aws:instance:i-0app"]
        assert node["label"] == "clinic-app-server"
        assert node["status"] == "healthy"
        topo = builder.build()
        assert ("aws:instance:i-0app", "net:aws:vpc-1", "member_of") in _graph(topo)[1]

    def test_snapshots_are_processed_after_every_other_event(self):
        # The snapshot arrives FIRST (as rows ordered newest-first often do).
        topo = build_topology("org-x", events=[
            _ev("network.snapshot", "webhook", {
                "provider": "manual",
                "networks": [{"id": "lan", "name": "Office LAN", "kind": "office_lan"}],
                "devices": [
                    {"id": "desk", "name": "front-desk-pc", "network_id": "lan"},
                    {"id": "app", "name": "clinic-app-server", "network_id": "lan"},
                ],
                "links": [{"source": "desk", "target": "app", "label": "tcp/443"}],
            }),
            _intune_event(),
            _inventory_event(),
        ])
        nodes, edges = _graph(topo)
        assert not any(node_id.startswith("net:device:") for node_id in nodes)
        assert ("ms:device:d-9", "net:manual:lan", "member_of") in edges
        assert ("aws:instance:i-0app", "net:manual:lan", "member_of") in edges
        assert ("ms:device:d-9", "aws:instance:i-0app", "talks_to") in edges

    def test_sample_flag_marks_only_nodes_the_snapshot_creates(self):
        topo = build_topology("org-x", events=[
            _inventory_event(), _intune_event(),
            _ev("network.snapshot", "webhook", _full_snapshot(sample=True)),
        ])
        nodes, _ = _graph(topo)
        created = [
            "net:unifi:lan", "net:unifi:guest", "net:aws:vpc-1", "subnet:aws:subnet-a", "gw:unifi:fw",
            "gw:aws:igw-1", "vpn:aws:vpn-1", "vpn:aws:cvpn-1", "aws:sg:sg-web", "net:device:unifi:nas",
            "net:device:unifi:laptop", INTERNET_NODE_ID,
        ]
        for node_id in created:
            assert nodes[node_id]["meta"].get("sample") is True, node_id
        # Nodes that came from real inventory / Intune are not sample data.
        assert "sample" not in nodes["aws:instance:i-0app"]["meta"]
        assert "sample" not in nodes["ms:device:d-9"]["meta"]
        assert "sample" not in nodes["connector:webhook"]["meta"]

    def test_aws_event_type_defaults_to_aws_provider_and_wrapped_payload_is_read(self):
        topo = build_topology("org-x", events=[
            _ev("aws.network.snapshot", "aws", {"networks": [{"id": "vpc-9", "cidr": "10.9.0.0/16"}]}),
            _ev("network.snapshot", "webhook", {
                "event_type": "network.snapshot",
                "data": {"networks": [{"id": "lan", "name": "Shop LAN"}]},
            }),
        ])
        nodes, edges = _graph(topo)
        assert nodes["net:aws:vpc-9"]["meta"]["network_kind"] == "vpc"
        assert nodes["net:manual:lan"]["label"] == "Shop LAN"            # no provider given -> manual
        assert nodes["net:manual:lan"]["meta"]["network_kind"] == "other"
        assert ("connector:aws", "net:aws:vpc-9", "monitors") in edges
        assert ("connector:webhook", "net:manual:lan", "monitors") in edges

    def test_only_the_newest_snapshot_of_a_feed_is_used(self):
        now = datetime.now(timezone.utc)

        def snap(statuses, extra_net=None):
            nets = [{"id": "vpc-1", "name": "clinic-vpc"}] + ([extra_net] if extra_net else [])
            return {"provider": "aws", "account_id": "1", "region": "us-east-1", "networks": nets, "vpns": [
                {"id": "vpn-1", "kind": "site_to_site", "network_id": "vpc-1",
                 "tunnels": [{"status": s} for s in statuses]},
            ]}

        older = _ev("aws.network.snapshot", "aws", snap(["DOWN", "DOWN"], {"id": "vpc-removed"}),
                    (now - timedelta(hours=2)).isoformat())
        newer = _ev("aws.network.snapshot", "aws", snap(["UP", "UP"]), now.isoformat())
        other_region = _ev("aws.network.snapshot", "aws", {
            "provider": "aws", "account_id": "1", "region": "eu-west-1", "networks": [{"id": "vpc-eu"}],
        }, (now - timedelta(hours=3)).isoformat())

        for order in ([older, newer, other_region], [newer, other_region, older]):
            topo = build_topology("org-x", events=order)
            nodes, _ = _graph(topo)
            assert nodes["vpn:aws:vpn-1"]["status"] == "healthy"        # the tunnel came back up
            assert nodes["vpn:aws:vpn-1"]["meta"]["issues"] == []
            assert "net:aws:vpc-removed" not in nodes                    # gone from the newest snapshot
            assert "net:aws:vpc-eu" in nodes                             # a different feed is kept
            source = next(s for s in topo["live"]["sources"] if s["id"] == "connector:aws")
            assert source["event_count"] == 2

    def test_empty_snapshot_adds_nothing(self):
        topo = build_topology("org-x", events=[_ev("network.snapshot", "webhook", {"provider": "manual", "networks": []})])
        assert topo["nodes"] == []
        assert topo["summary"]["empty"] is True


class TestVpnStatus:
    @staticmethod
    def _vpn(**fields):
        vpn = {"id": "vpn-1", "kind": "site_to_site", "network_id": "vpc-1"}
        vpn.update(fields)
        topo = build_topology("org-x", events=[_ev("aws.network.snapshot", "aws", {
            "networks": [{"id": "vpc-1"}], "vpns": [vpn],
        })])
        return topo, next(n for n in topo["nodes"] if n["type"] == "vpn")

    def test_all_tunnels_up_is_healthy(self):
        topo, vpn = self._vpn(tunnels=[{"status": "UP"}, {"status": "up"}])
        assert vpn["status"] == "healthy"
        assert vpn["meta"]["issues"] == []
        assert (vpn["meta"]["tunnels_up"], vpn["meta"]["tunnels_total"]) == (2, 2)
        assert topo["summary"]["vpn_down"] == 0

    def test_one_tunnel_down_is_a_warning(self):
        topo, vpn = self._vpn(tunnels=[{"status": "UP"}, {"status": "DOWN"}])
        assert vpn["status"] == "warning"
        assert vpn["meta"]["issues"] == [{"title": "One VPN tunnel is down", "severity": "medium"}]
        assert (vpn["meta"]["tunnels_up"], vpn["meta"]["tunnels_total"]) == (1, 2)
        assert topo["summary"]["vpn_down"] == 0

    def test_all_tunnels_down_needs_attention(self):
        topo, vpn = self._vpn(tunnels=[{"status": "DOWN"}, {"status": "DOWN"}])
        assert vpn["status"] == "attention"
        assert vpn["meta"]["issues"] == [{"title": "VPN is down", "severity": "high"}]
        assert (vpn["meta"]["tunnels_up"], vpn["meta"]["tunnels_total"]) == (0, 2)
        assert topo["summary"]["vpn_down"] == 1
        assert topo["summary"]["vpns"] == 1

    def test_unknown_tunnel_state_is_unknown(self):
        for fields in ({}, {"tunnels": []}, {"tunnels": [{"outside_ip": "203.0.113.9"}]}, {"state": "available"}):
            _, vpn = self._vpn(**fields)
            assert vpn["status"] == "unknown", fields
            assert vpn["meta"]["issues"] == []
            assert "tunnels_up" not in vpn["meta"]

    def test_partly_unknown_tunnels_are_not_called_healthy(self):
        _, vpn = self._vpn(tunnels=[{"status": "UP"}, {"status": None}])
        assert vpn["status"] == "unknown"
        assert vpn["meta"]["tunnels_total"] == 2
        assert "tunnels_up" not in vpn["meta"]

    def test_client_vpn_uses_the_endpoint_state(self):
        _, vpn = self._vpn(kind="client", state="available", active_connections=3)
        assert vpn["status"] == "healthy"
        assert vpn["meta"]["active_connections"] == 3
        _, vpn = self._vpn(kind="client", state="pending-associate")
        assert vpn["status"] == "unknown"

    def test_explicit_down_state_without_tunnels(self):
        topo, vpn = self._vpn(state="down")
        assert vpn["status"] == "attention"
        assert vpn["meta"]["issues"] == [{"title": "VPN is down", "severity": "high"}]
        assert topo["summary"]["vpn_down"] == 1

    def test_deleted_vpn_is_not_drawn(self):
        topo = build_topology("org-x", events=[_ev("aws.network.snapshot", "aws", {
            "networks": [{"id": "vpc-1"}], "vpns": [{"id": "vpn-old", "state": "deleted"}],
        })])
        assert topo["summary"]["vpns"] == 0


class TestInventoryPlacement:
    def _inventory(self):
        return _ev("aws.inventory.snapshot", "aws", {"resources": [
            {"kind": "ec2_instance", "instance_id": "i-0app", "name": "clinic-app-server", "state": "running",
             "private_ip": "10.0.1.20", "vpc_id": "vpc-1", "subnet_id": "subnet-a",
             "security_group_ids": ["sg-web", "sg-admin"], "availability_zone": "us-east-1a"},
            {"kind": "rds_instance", "identifier": "clinic-db", "name": "clinic-db", "engine": "postgres",
             "vpc_id": "vpc-1", "security_group_ids": ["sg-db"]},
            {"kind": "ec2_instance", "instance_id": "i-0old", "name": "legacy-box", "state": "running"},
        ]})

    def test_inventory_creates_bare_network_subnet_and_group_nodes(self):
        topo = build_topology("org-x", events=[self._inventory()])
        nodes, edges = _graph(topo)

        app = nodes["aws:instance:i-0app"]
        assert app["meta"]["network_id"] == "vpc-1"
        assert app["meta"]["subnet_id"] == "subnet-a"
        assert app["meta"]["availability_zone"] == "us-east-1a"
        assert nodes["aws:db:clinic-db"]["meta"]["network_id"] == "vpc-1"
        assert "subnet_id" not in nodes["aws:db:clinic-db"]["meta"]

        vpc = nodes["net:aws:vpc-1"]
        assert (vpc["type"], vpc["zone"], vpc["label"], vpc["status"]) == ("network", "network", "vpc-1", "unknown")
        assert vpc["meta"]["network_kind"] == "vpc"
        assert nodes["subnet:aws:subnet-a"]["type"] == "subnet"
        assert nodes["aws:sg:sg-web"]["type"] == "security_group"

        assert ("aws:instance:i-0app", "subnet:aws:subnet-a", "member_of") in edges      # subnet when present
        assert ("aws:instance:i-0app", "net:aws:vpc-1", "member_of") not in edges
        assert ("subnet:aws:subnet-a", "net:aws:vpc-1", "part_of") in edges
        assert ("aws:db:clinic-db", "net:aws:vpc-1", "member_of") in edges               # else the network
        assert ("aws:sg:sg-web", "aws:instance:i-0app", "protects") in edges
        assert ("aws:sg:sg-admin", "aws:instance:i-0app", "protects") in edges
        assert ("aws:sg:sg-db", "aws:db:clinic-db", "protects") in edges
        # A resource without placement gets no edges and no invented network.
        assert not any(e for e in edges if e[0] == "aws:instance:i-0old" and e[2] == "member_of")
        assert not any(n["meta"].get("inferred") for n in topo["nodes"])

    def test_network_snapshot_upgrades_the_bare_nodes(self):
        snapshot = _ev("aws.network.snapshot", "aws", {
            "provider": "aws",
            "networks": [{"id": "vpc-1", "name": "clinic-vpc", "cidr": "10.0.0.0/16", "kind": "vpc"}],
            "subnets": [{"id": "subnet-a", "name": "private-a", "cidr": "10.0.1.0/24", "network_id": "vpc-1", "public": False}],
            "security_groups": [{"id": "sg-web", "name": "web", "network_id": "vpc-1", "open_ports": ["tcp/22"]}],
        })
        for events in ([self._inventory(), snapshot], [snapshot, self._inventory()]):
            nodes, edges = _graph(build_topology("org-x", events=events))
            assert nodes["net:aws:vpc-1"]["label"] == "clinic-vpc"
            assert nodes["net:aws:vpc-1"]["status"] == "healthy"
            assert nodes["net:aws:vpc-1"]["meta"]["cidr"] == "10.0.0.0/16"
            assert nodes["subnet:aws:subnet-a"]["label"] == "private-a"
            assert nodes["aws:sg:sg-web"]["label"] == "web"
            assert nodes["aws:sg:sg-admin"]["label"] == "sg-admin"      # not in the snapshot: stays a placeholder
            assert (INTERNET_NODE_ID, "aws:sg:sg-web", "exposed_to_internet") in edges
            assert ("aws:sg:sg-web", "aws:instance:i-0app", "protects") in edges

    def test_finding_on_a_security_group_keeps_its_node_id(self):
        topo = build_topology("org-x", events=[
            _synthetic_events()[0],      # critical finding on sg-0abc
            _ev("aws.network.snapshot", "aws", {
                "networks": [{"id": "vpc-1"}],
                "security_groups": [{"id": "sg-0abc", "name": "launch-wizard-1", "network_id": "vpc-1", "open_ports": ["tcp/3389"]}],
            }),
        ])
        nodes, _ = _graph(topo)
        group = nodes["aws:sg:sg-0abc"]
        assert group["label"] == "launch-wizard-1"
        assert group["status"] == "attention"               # the finding's severity is kept
        assert group["meta"]["open_ports"] == ["tcp/3389"]
        assert sum(1 for n in topo["nodes"] if n["type"] == "security_group") == 1


class TestInferredNetworks:
    def test_private_address_without_a_network_lands_on_an_inferred_slash_24(self):
        topo = build_topology("org-x", events=[_ev("aws.inventory.snapshot", "aws", {"resources": [
            {"kind": "ec2_instance", "instance_id": "i-1", "name": "web-1", "private_ip": "10.0.1.20"},
            {"kind": "ec2_instance", "instance_id": "i-2", "name": "web-2", "private_ip": "10.0.1.99"},
            {"kind": "ec2_instance", "instance_id": "i-3", "name": "office-box", "private_ip": "192.168.7.4"},
            {"kind": "ec2_instance", "instance_id": "i-4", "name": "edge", "private_ip": "172.32.0.5"},     # not RFC 1918
            {"kind": "ec2_instance", "instance_id": "i-5", "name": "no-ip"},
            {"kind": "ec2_instance", "instance_id": "i-6", "name": "public-only", "private_ip": "8.8.8.8"},
            {"kind": "ec2_instance", "instance_id": "i-7", "name": "placed", "private_ip": "10.0.1.30", "vpc_id": "vpc-1"},
            {"kind": "ec2_instance", "instance_id": "i-8", "name": "v6", "private_ip": "fd00::5"},
        ]})])
        nodes, edges = _graph(topo)

        inferred = nodes["net:inferred:10.0.1.0/24"]
        assert inferred["type"] == "network" and inferred["zone"] == "network"
        assert inferred["label"] == "10.0.1.0/24"
        assert inferred["sublabel"] == "Network worked out from device addresses"
        assert inferred["meta"]["inferred"] is True
        assert inferred["meta"]["network_kind"] == "inferred"
        assert inferred["meta"]["cidr"] == "10.0.1.0/24"
        assert inferred["status"] == "unknown"

        assert ("aws:instance:i-1", "net:inferred:10.0.1.0/24", "member_of") in edges
        assert ("aws:instance:i-2", "net:inferred:10.0.1.0/24", "member_of") in edges
        assert ("aws:instance:i-3", "net:inferred:192.168.7.0/24", "member_of") in edges
        # Placed by AWS, so not inferred even though the address would fit.
        assert ("aws:instance:i-7", "net:aws:vpc-1", "member_of") in edges
        assert ("aws:instance:i-7", "net:inferred:10.0.1.0/24", "member_of") not in edges
        inferred_ids = {n["id"] for n in topo["nodes"] if n["meta"].get("inferred")}
        assert inferred_ids == {"net:inferred:10.0.1.0/24", "net:inferred:192.168.7.0/24"}
        for node_id in ("aws:instance:i-4", "aws:instance:i-5", "aws:instance:i-6", "aws:instance:i-8"):
            assert not any(e for e in edges if e[0] == node_id and e[2] == "member_of"), node_id
        assert topo["summary"]["networks"] == 3

    def test_discovered_host_asset_address_is_used(self):
        asset = {"id": "a-1", "hostname": "ehr-app-01", "asset_type": "CLOUD_SERVICE", "cloud_provider": "AWS",
                 "ip_address": "10.4.2.9"}
        nodes, edges = _graph(build_topology("org-x", assets=[asset]))
        assert ("asset:a-1", "net:inferred:10.4.2.0/24", "member_of") in edges
        assert nodes["net:inferred:10.4.2.0/24"]["meta"]["inferred"] is True

    def test_identities_and_buckets_are_never_placed(self):
        topo = build_topology("org-x", events=[_ev("microsoft.telemetry", "microsoft", {
            "entra_users": [{"user_id": "u-1", "user_principal_name": "a@b.test", "mfa_enforced": True}],
        })])
        assert topo["summary"]["networks"] == 0

    def test_building_twice_does_not_duplicate(self):
        builder = TopologyBuilder("org-x")
        builder.add_events([_ev("aws.inventory.snapshot", "aws", {"resources": [
            {"kind": "ec2_instance", "instance_id": "i-1", "name": "web-1", "private_ip": "10.0.1.20"},
        ]})])
        first, second = builder.build(), builder.build()
        assert len(first["nodes"]) == len(second["nodes"])
        assert len(first["edges"]) == len(second["edges"])


# ---------------------------------------------------------------------------
# Wazuh and Splunk
# ---------------------------------------------------------------------------

def _agent(agent_id, name, status="active", **extra):
    payload = {"agent_id": agent_id, "name": name, "status": status, "ip": "10.0.5.%d" % int(agent_id),
               "os": "Ubuntu 22.04", "version": "Wazuh v4.7.0", "group": ["default"]}
    payload.update(extra)
    return _ev("wazuh.agent_status", "wazuh", payload)


def _alert(agent_id, level, description, agent_name=None):
    return _ev("wazuh.alert", "wazuh", {
        "alert_id": f"{agent_id}-{description}", "rule_id": "5710", "rule_description": description,
        "rule_level": level, "agent_id": agent_id, "agent_name": agent_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


class TestWazuh:
    def test_agents_become_nodes_monitored_by_wazuh(self):
        keep_alive = (datetime.now(timezone.utc) - timedelta(minutes=3)).isoformat()
        topo = build_topology("org-x", events=[
            _agent("000", "wazuh-manager"),
            _agent("001", "web-01", last_keep_alive=keep_alive),
            _agent("002", "reception", status="disconnected", os="Microsoft Windows 10 Pro"),
            _agent("003", "exec-mac", status="never_connected", os="macOS 14.5", ip="any"),
            _agent("004", "staging", status="pending"),
        ])
        nodes, edges = _graph(topo)

        assert "wazuh:agent:000" not in nodes                       # the manager is not an endpoint
        web = nodes["wazuh:agent:001"]
        assert (web["type"], web["zone"], web["status"], web["label"]) == ("server", "servers", "healthy", "web-01")
        assert web["meta"]["agent_id"] == "001"
        assert web["meta"]["ip_address"] == "10.0.5.1"
        assert web["meta"]["operating_system"] == "Ubuntu 22.04"
        assert web["meta"]["agent_group"] == ["default"]
        assert web["meta"]["last_seen"] == keep_alive
        assert web["meta"]["issues"] == []
        assert ("connector:wazuh", "wazuh:agent:001", "monitors") in edges

        reception = nodes["wazuh:agent:002"]
        assert (reception["type"], reception["zone"]) == ("workstation", "workstations")   # Windows 10
        assert reception["status"] == "warning"
        assert reception["meta"]["issues"] == [{"title": "Security agent is not reporting", "severity": "medium"}]

        mac = nodes["wazuh:agent:003"]
        assert mac["type"] == "workstation"                         # macOS
        assert mac["status"] == "warning"
        assert "ip_address" not in mac["meta"]                      # "any" is not an address

        assert nodes["wazuh:agent:004"]["status"] == "unknown"
        # Agents with a private address and no reported network land on an inferred /24.
        assert ("wazuh:agent:001", "net:inferred:10.0.5.0/24", "member_of") in edges

    def test_windows_server_stays_a_server(self):
        nodes, _ = _graph(build_topology("org-x", events=[_agent("009", "dc-01", os="Microsoft Windows Server 2019")]))
        assert nodes["wazuh:agent:009"]["type"] == "server"

    def test_agent_enriches_a_same_named_node_whatever_the_order(self):
        for events in (
            [_inventory_event(), _agent("007", "CLINIC-APP-SERVER", status="disconnected")],
            [_agent("007", "CLINIC-APP-SERVER", status="disconnected"), _inventory_event()],
        ):
            topo = build_topology("org-x", events=events)
            nodes, edges = _graph(topo)
            assert "wazuh:agent:007" not in nodes
            app = nodes["aws:instance:i-0app"]
            assert app["label"] == "clinic-app-server"
            assert app["status"] == "warning"
            assert app["meta"]["agent_id"] == "007"
            assert "Wazuh" in app["meta"]["seen_by"]
            assert any(i["title"] == "Security agent is not reporting" for i in app["meta"]["issues"])
            assert ("connector:wazuh", "aws:instance:i-0app", "monitors") in edges

    def test_newest_status_of_an_agent_wins(self):
        now = datetime.now(timezone.utc)
        old = _ev("wazuh.agent_status", "wazuh", {"agent_id": "001", "name": "web-01", "status": "disconnected"},
                  (now - timedelta(hours=5)).isoformat())
        new = _ev("wazuh.agent_status", "wazuh", {"agent_id": "001", "name": "web-01", "status": "active"}, now.isoformat())
        for events in ([old, new], [new, old]):
            nodes, _ = _graph(build_topology("org-x", events=events))
            assert nodes["wazuh:agent:001"]["status"] == "healthy"
            assert nodes["wazuh:agent:001"]["meta"]["issues"] == []

    def test_alerts_mark_issues_by_rule_level(self):
        topo = build_topology("org-x", events=[
            _alert("001", 12, "Multiple authentication failures"),       # arrives before the agent
            _alert("001", 8, "New user added to the system"),
            _alert("001", 6, "Low level noise"),
            _alert("001", 3, "Informational"),
            _alert("404", 15, "Alert for an agent we never saw"),
            _alert("000", 15, "Manager alert"),
            _agent("001", "web-01"),
        ])
        nodes, _ = _graph(topo)
        web = nodes["wazuh:agent:001"]
        assert web["meta"]["issues"] == [
            {"title": "Multiple authentication failures", "severity": "high"},
            {"title": "New user added to the system", "severity": "medium"},
        ]
        assert web["status"] == "attention"
        assert len(nodes) == 3                                        # connector + agent + inferred network
        source = next(s for s in topo["live"]["sources"] if s["id"] == "connector:wazuh")
        assert source["event_count"] == 3                             # agent + the two alerts that were used

    def test_medium_alert_is_a_warning(self):
        nodes, _ = _graph(build_topology("org-x", events=[_agent("001", "web-01"), _alert("001", 7, "Rootcheck anomaly")]))
        assert nodes["wazuh:agent:001"]["status"] == "warning"

    def test_at_most_five_alert_issues_per_node(self):
        events = [_agent("001", "web-01")] + [_alert("001", 10, f"High alert {i}") for i in range(9)]
        nodes, _ = _graph(build_topology("org-x", events=events))
        assert len(nodes["wazuh:agent:001"]["meta"]["issues"]) == 5

    def test_alert_reaches_a_same_named_node_by_agent_name(self):
        nodes, _ = _graph(build_topology("org-x", events=[
            _inventory_event(), _alert("031", 11, "Rootkit detected", agent_name="clinic-app-server"),
        ]))
        assert nodes["aws:instance:i-0app"]["meta"]["issues"] == [{"title": "Rootkit detected", "severity": "high"}]


class TestSplunk:
    def test_hosts_become_nodes_and_quiet_hosts_are_flagged(self):
        now = datetime.now(timezone.utc)
        topo = build_topology("org-x", events=[
            _inventory_event(),
            _ev("splunk.host_inventory", "splunk", {"hosts": [
                {"host": "fw-edge-01", "last_seen": (now - timedelta(minutes=5)).isoformat(), "event_count": 9001},
                {"host": "old-fileserver", "last_seen": (now - timedelta(hours=30)).isoformat(), "event_count": 12},
                {"host": "epoch-host", "last_seen": int((now - timedelta(days=3)).timestamp()), "event_count": 1},
                {"host": "no-time-host"},
                {"host": "Clinic-App-Server", "last_seen": (now - timedelta(hours=40)).isoformat(), "event_count": 77},
                {"host": ""},
            ]}),
        ])
        nodes, edges = _graph(topo)

        fresh = nodes["splunk:host:fw-edge-01"]
        assert (fresh["type"], fresh["zone"], fresh["status"]) == ("server", "servers", "healthy")
        assert fresh["meta"]["log_event_count"] == 9001
        assert fresh["meta"]["issues"] == []
        assert ("connector:splunk", "splunk:host:fw-edge-01", "monitors") in edges

        quiet = nodes["splunk:host:old-fileserver"]
        assert quiet["status"] == "warning"
        assert quiet["meta"]["issues"] == [{"title": "Stopped sending logs", "severity": "medium"}]
        assert nodes["splunk:host:epoch-host"]["status"] == "warning"      # epoch seconds are understood
        assert nodes["splunk:host:no-time-host"]["status"] == "unknown"    # never claims "now"
        assert nodes["splunk:host:no-time-host"]["meta"]["issues"] == []

        # Same name as an inventory node: that node is enriched, no duplicate.
        assert "splunk:host:Clinic-App-Server" not in nodes
        app = nodes["aws:instance:i-0app"]
        assert app["status"] == "warning"
        assert any(i["title"] == "Stopped sending logs" for i in app["meta"]["issues"])
        assert ("connector:splunk", "aws:instance:i-0app", "monitors") in edges
        assert sum(1 for n in nodes if n.startswith("splunk:host:")) == 4

    def test_only_the_newest_host_inventory_is_used(self):
        now = datetime.now(timezone.utc)
        old = _ev("splunk.host_inventory", "splunk", {"hosts": [
            {"host": "retired-host", "last_seen": (now - timedelta(days=2)).isoformat()},
        ]}, (now - timedelta(days=1)).isoformat())
        new = _ev("splunk.host_inventory", "splunk", {"hosts": [
            {"host": "web-01", "last_seen": now.isoformat()},
        ]}, now.isoformat())
        nodes, _ = _graph(build_topology("org-x", events=[old, new]))
        assert "splunk:host:web-01" in nodes
        assert "splunk:host:retired-host" not in nodes


# ---------------------------------------------------------------------------
# Live block and summary
# ---------------------------------------------------------------------------

class TestLiveBlock:
    def test_empty_graph(self):
        topo = build_topology("org-x")
        assert topo["live"] == {"mode": "empty", "latest_event_at": None, "sources": []}
        summary = topo["summary"]
        assert (summary["networks"], summary["vpns"], summary["vpn_down"]) == (0, 0, 0)

    def test_sources_list_every_connector_with_event_counts(self):
        last_sync = datetime(2026, 11, 9, 12, 0, 0)          # naive, as stored by the database
        newest = datetime.now(timezone.utc)
        connectors = [
            {"id": "c-aws", "connector_type": "aws", "display_name": "Prod AWS", "status": "active",
             "health_status": "healthy", "last_sync_at": last_sync},
            {"id": "c-duo", "connector_type": "duo", "display_name": "Duo", "status": "error",
             "health_status": "down", "last_sync_at": None},
        ]
        events = [
            _ev("aws.inventory.snapshot", "aws", {"resources": [
                {"kind": "ec2_instance", "instance_id": "i-1", "name": "web-1"},
            ]}, (newest - timedelta(hours=1)).isoformat()),
            _ev("aws.network.snapshot", "aws", {"networks": [{"id": "vpc-1"}]}, newest.isoformat()),
            _ev("veeam.backup_job", "veeam", {"system_name": "web-1", "last_successful_backup": newest.isoformat()},
                (newest - timedelta(hours=2)).isoformat()),
            _ev("some.unknown.event", "aws", {"anything": True}),       # not understood: not counted
        ]
        topo = build_topology("org-x", connectors=connectors, events=events)
        live = topo["live"]

        assert live["mode"] == "live"
        assert live["latest_event_at"] == newest.isoformat()
        sources = {s["id"]: s for s in live["sources"]}
        assert set(sources) == {"connector:c-aws", "connector:c-duo", "connector:veeam"}
        assert sources["connector:c-aws"] == {
            "id": "connector:c-aws", "type": "aws", "label": "Prod AWS", "status": "healthy",
            "last_sync_at": "2026-11-09T12:00:00+00:00", "event_count": 2,
        }
        assert sources["connector:c-duo"]["status"] == "error"
        assert sources["connector:c-duo"]["last_sync_at"] is None
        assert sources["connector:c-duo"]["event_count"] == 0
        # A source without a connector row reports the time of its newest event.
        assert sources["connector:veeam"]["type"] == "veeam"
        assert sources["connector:veeam"]["event_count"] == 1
        assert sources["connector:veeam"]["last_sync_at"] == (newest - timedelta(hours=2)).isoformat()

    def test_summary_counts_networks_and_vpns(self):
        topo = build_topology("org-x", events=[_ev("network.snapshot", "webhook", {
            "provider": "manual",
            "networks": [{"id": "lan"}, {"id": "dmz"}],
            "vpns": [
                {"id": "v1", "network_id": "lan", "tunnels": [{"status": "DOWN"}]},
                {"id": "v2", "network_id": "lan", "tunnels": [{"status": "UP"}]},
                {"id": "v3", "network_id": "lan", "state": "down"},
            ],
        })])
        summary = topo["summary"]
        assert (summary["networks"], summary["vpns"], summary["vpn_down"]) == (2, 3, 2)
        assert summary["by_zone"]["network"] == 5


# ---------------------------------------------------------------------------
# Demo organizations
# ---------------------------------------------------------------------------

class TestDemoNetwork:
    def test_demo_health_org_has_the_sample_network_layout(self, db_session):
        topo = build_topology_for_org(db_session, "demo-health-org", demo=True)
        nodes, edges = _graph(topo)
        types = {n["type"] for n in topo["nodes"]}
        kinds = {e["kind"] for e in topo["edges"]}

        assert {"network", "subnet", "vpn", "gateway", "server", "workstation", "connector", "internet"} <= types
        assert {"member_of", "part_of", "vpn_tunnel", "routes_to", "talks_to", "monitors", "exposed_to_internet"} <= kinds
        for e in topo["edges"]:
            assert e["source"] in nodes and e["target"] in nodes

        assert topo["live"]["mode"] == "demo"
        assert topo["live"]["latest_event_at"]
        assert {s["type"] for s in topo["live"]["sources"]} >= {"microsoft", "veeam", "aws_security_hub", "webhook"}
        summary = topo["summary"]
        assert (summary["networks"], summary["vpns"], summary["vpn_down"]) == (3, 2, 0)

        # Scripted layout is flagged as sample data.
        for node_id in ("net:manual:office-lan", "net:manual:guest-wifi", "net:aws:vpc-metro-health",
                        "subnet:aws:subnet-metro-health-private", "subnet:aws:subnet-metro-health-public",
                        "gw:manual:office-firewall", "gw:aws:igw-metro-health",
                        "vpn:aws:vpn-metro-health-office", "vpn:aws:cvpn-metro-health-staff"):
            assert nodes[node_id]["meta"]["sample"] is True, node_id
        assert nodes["net:manual:office-lan"]["meta"]["network_kind"] == "office_lan"
        assert nodes["net:manual:guest-wifi"]["meta"]["network_kind"] == "wifi"
        assert nodes["gw:manual:office-firewall"]["meta"]["public_ip"].startswith("203.0.113.")

        # One of the two site-to-site tunnels is down: a warning, not an outage.
        s2s = nodes["vpn:aws:vpn-metro-health-office"]
        assert s2s["status"] == "warning"
        assert (s2s["meta"]["tunnels_up"], s2s["meta"]["tunnels_total"]) == (1, 2)
        assert any(i["title"] == "One VPN tunnel is down" for i in s2s["meta"]["issues"])
        assert ("vpn:aws:vpn-metro-health-office", "net:aws:vpc-metro-health", "vpn_tunnel") in edges
        assert ("vpn:aws:vpn-metro-health-office", "gw:manual:office-firewall", "vpn_tunnel") in edges
        client = nodes["vpn:aws:cvpn-metro-health-staff"]
        assert client["status"] == "healthy" and client["meta"]["active_connections"] == 2
        laptops = [e for e in topo["edges"] if e["kind"] == "vpn_tunnel" and e["target"] == client["id"]]
        assert len(laptops) == 2

        # The three recorded EC2 instances sit in the VPC subnets; they are not sample nodes.
        placed = {e["source"]: e["target"] for e in topo["edges"]
                  if e["kind"] == "member_of" and e["source"].startswith("aws:instance:")}
        assert placed == {
            "aws:instance:i-0ff2d70892e4f07b2": "subnet:aws:subnet-metro-health-private",   # EHR app server
            "aws:instance:i-05bd12cd2b0b24d9a": "subnet:aws:subnet-metro-health-private",   # backup server
            "aws:instance:i-0cc2366a2451c726e": "subnet:aws:subnet-metro-health-public",    # front desk workstation
        }
        for node_id in placed:
            assert "sample" not in nodes[node_id]["meta"]
            assert "metro-health" in nodes[node_id]["label"]

        # The scripted Intune workstation is on the office network (matched by name).
        assert nodes["ms:device:d-001"]["label"] == "FRONT-DESK-PC"
        assert ("ms:device:d-001", "net:manual:office-lan", "member_of") in edges
        assert not any(n["label"] == "FRONT-DESK-PC" and n["id"] != "ms:device:d-001" for n in topo["nodes"])

        # Observed traffic.
        assert ("ms:device:d-001", "aws:instance:i-0ff2d70892e4f07b2", "talks_to") in edges
        assert ("aws:instance:i-0ff2d70892e4f07b2", "aws:instance:i-05bd12cd2b0b24d9a", "talks_to") in edges
        assert _edge(topo, "ms:device:d-001", "aws:instance:i-0ff2d70892e4f07b2", "talks_to")["label"] == "tcp/443"
        assert not any(n["meta"].get("inferred") for n in topo["nodes"])

    def test_legal_demo_uses_its_own_names(self, db_session):
        topo = build_topology_for_org(db_session, "demo-northstar-cole", demo=True)
        nodes, edges = _graph(topo)
        assert nodes["net:aws:vpc-northstar-cole"]["label"] == "northstar-cole-vpc"
        assert nodes["net:manual:office-lan"]["label"] == "Law office network"
        assert nodes["ms:device:d-001"]["label"] == "PARTNER-LAPTOP-07"
        assert ("ms:device:d-001", "net:manual:office-lan", "member_of") in edges
        assert ("ms:device:d-001", "aws:instance:i-0d27981b53460c6eb", "talks_to") in edges     # DMS matter server
        assert ("aws:instance:i-0d27981b53460c6eb", "aws:instance:i-067020572d69e37de", "talks_to") in edges
        assert not any("metro-health" in n["id"] or "metro-health" in n["label"] for n in topo["nodes"])
        assert topo["live"]["mode"] == "demo"

    def test_network_snapshot_does_not_feed_the_readiness_evidence(self):
        from app.api.clinic.router import get_demo_telemetry
        from app.services.clinic_engine.v2.providers import ProviderRegistry

        def evidence_for(events):
            found = []
            for provider_cls in ProviderRegistry.list_all().values():
                found.extend(provider_cls.extract(events))
            return sorted((e.kind.value, e.source_connector, str(e.source_id)) for e in found)

        events = get_demo_telemetry("demo-health-org")
        snapshots = [e for e in events if e.event_type == "network.snapshot"]
        assert len(snapshots) == 1
        assert snapshots[0].payload["sample"] is True
        assert evidence_for(snapshots) == []
        assert evidence_for(events) == evidence_for([e for e in events if e.event_type != "network.snapshot"])


# ---------------------------------------------------------------------------
# Pushed snapshots (webhook)
# ---------------------------------------------------------------------------

class TestPushedSnapshot:
    ORG_ID = "test-org-123"      # provisioned by the client_with_org fixture
    SECRET = "s3cr3t-shared"

    def _register(self, db_session):
        from app.services.connector_manager import ConnectorManager

        return ConnectorManager(db_session, self.ORG_ID).register_connector(
            connector_type="webhook",
            display_name="Office firewall",
            auth_method="webhook",
            credentials={"webhook_name": "Office firewall", "webhook_secret": self.SECRET},
            config={"webhook_name": "Office firewall"},
            created_by="test",
        )

    def test_pushed_network_snapshot_is_stored_unchanged_and_drawn(self, db_session, client_with_org):
        import json

        from app.models.telemetry_event import TelemetryEvent

        connector = self._register(db_session)
        body = {
            "event_type": "network.snapshot",
            "provider": "pfsense",
            "networks": [{"id": "lan", "name": "Shop LAN", "cidr": "192.168.1.0/24", "kind": "office_lan"}],
            "gateways": [{"id": "fw", "name": "pfSense", "kind": "firewall", "network_id": "lan", "to_internet": True}],
            "vpns": [{"id": "wg0", "name": "WireGuard", "kind": "site_to_site", "network_id": "lan",
                      "tunnels": [{"status": "DOWN"}]}],
            "devices": [{"id": "till", "name": "till-01", "ip": "192.168.1.20", "network_id": "lan"}],
        }
        url = f"/api/v1/connectors/webhook/webhook?org_id={self.ORG_ID}"
        resp = client_with_org.post(url, json=body, headers={"X-Webhook-Secret": self.SECRET})
        assert resp.status_code == 200
        assert resp.json()["events_ingested"] == 1

        rows = db_session.query(TelemetryEvent).filter(TelemetryEvent.org_id == self.ORG_ID).all()
        assert len(rows) == 1
        row = rows[0]
        assert row.event_type == "network.snapshot"
        assert row.source_system == "webhook"
        stored = json.loads(row.payload) if isinstance(row.payload, str) else row.payload
        assert stored == body

        # An identical push inside the same hour is one row, not two.
        again = client_with_org.post(url, json=body, headers={"X-Webhook-Secret": self.SECRET})
        assert again.json()["events_ingested"] == 0

        topo = build_topology_for_org(db_session, self.ORG_ID)
        nodes, edges = _graph(topo)
        assert nodes["net:pfsense:lan"]["label"] == "Shop LAN"
        assert nodes["vpn:pfsense:wg0"]["status"] == "attention"
        assert ("net:device:pfsense:till", "net:pfsense:lan", "member_of") in edges
        assert ("gw:pfsense:fw", INTERNET_NODE_ID, "routes_to") in edges
        assert not any(n["meta"].get("sample") for n in topo["nodes"])
        assert topo["summary"]["vpn_down"] == 1
        assert topo["live"]["mode"] == "live"
        source = next(s for s in topo["live"]["sources"] if s["type"] == "webhook")
        assert source["id"] == f"connector:{connector.id}"
        assert source["event_count"] == 1
        assert source["last_sync_at"]

    def test_snapshot_survives_a_burst_of_newer_events(self, db_session, client_with_org):
        import json

        from app.models.telemetry_event import TelemetryEvent

        now = datetime.now(timezone.utc)
        db_session.add(TelemetryEvent(
            org_id=self.ORG_ID, event_type="network.snapshot", source_system="webhook",
            source_event_id="push-old", payload_hash="0" * 64, severity="info",
            payload=json.dumps({"provider": "manual", "networks": [{"id": "lan", "name": "Office LAN"}]}),
            created_at=now - timedelta(days=2),
        ))
        # More than the 1000-row window of newer alerts.
        db_session.add_all([
            TelemetryEvent(
                org_id=self.ORG_ID, event_type="wazuh.alert", source_system="wazuh",
                source_event_id=f"alert-{i}", payload_hash="1" * 64, severity="low",
                payload=json.dumps({"alert_id": str(i), "rule_level": 3, "agent_id": "001"}),
                created_at=now - timedelta(minutes=i % 50),
            )
            for i in range(1010)
        ])
        db_session.commit()

        nodes, _ = _graph(build_topology_for_org(db_session, self.ORG_ID))
        assert nodes["net:manual:lan"]["label"] == "Office LAN"

    def test_new_event_types_are_persisted_by_connector_ingestion(self, db_session, client_with_org):
        import asyncio

        from app.connectors.base import NormalizedEvent
        from app.models.telemetry_event import TelemetryEvent
        from app.services.connector_manager import ConnectorManager

        connector = self._register(db_session)
        now = datetime.now(timezone.utc).isoformat()
        events = [
            NormalizedEvent("aws.network.snapshot", "aws", "aws-network-1", "info",
                            {"provider": "aws", "networks": [{"id": "vpc-1"}]}, now),
            NormalizedEvent("splunk.host_inventory", "splunk", "splunk-host-inventory-1", "info",
                            {"hosts": [{"host": "web-01", "last_seen": now}]}, now),
            NormalizedEvent("network.snapshot", "webhook", "push-1", "info",
                            {"provider": "manual", "networks": [{"id": "lan"}]}, now),
        ]
        ingested = asyncio.run(ConnectorManager(db_session, self.ORG_ID)._ingest_events(connector.id, events))
        assert ingested == 3
        stored = {r.event_type for r in db_session.query(TelemetryEvent).filter(TelemetryEvent.org_id == self.ORG_ID)}
        assert stored == {"aws.network.snapshot", "splunk.host_inventory", "network.snapshot"}

        nodes, _ = _graph(build_topology_for_org(db_session, self.ORG_ID))
        assert {"net:aws:vpc-1", "net:manual:lan", "splunk:host:web-01"} <= set(nodes)


# ---------------------------------------------------------------------------
# Collectors that feed the map (Wazuh agents, Splunk hosts)
# ---------------------------------------------------------------------------

class TestMapCollectors:
    def test_wazuh_agents_carry_keep_alive_and_group(self):
        import asyncio

        from app.connectors.wazuh import WazuhConnector

        class Response:
            status_code = 200

            @staticmethod
            def json():
                return {"data": {"affected_items": [
                    {"id": "001", "name": "web-01", "status": "active", "ip": "10.0.5.1",
                     "os": {"name": "Ubuntu", "platform": "ubuntu"}, "version": "Wazuh v4.7.0",
                     "lastKeepAlive": "2026-11-09T10:00:00+00:00", "group": ["default", "servers"]},
                    {"id": "002", "name": "kiosk", "status": "never_connected", "os": {"platform": "windows"}},
                ]}}

        class Client:
            def __init__(self):
                self.calls = []

            async def get(self, url, headers=None, params=None):
                self.calls.append((url, params))
                return Response()

        connector = WazuhConnector("c-wazuh", "org-x", {"wazuh_url": "https://wazuh.test:55000"}, {})
        client = Client()
        events = asyncio.run(connector._fetch_agents(client, {}))

        selected = client.calls[0][1]["select"].split(",")
        assert {"lastKeepAlive", "os.platform", "group", "id", "name", "status", "ip", "os.name", "version"} <= set(selected)
        first, second = events
        assert first.event_type == "wazuh.agent_status"
        assert first.source_event_id == "agent-status-001"            # unchanged id
        assert first.payload["last_keep_alive"] == "2026-11-09T10:00:00+00:00"
        assert first.payload["group"] == ["default", "servers"]
        assert first.payload["os"] == "Ubuntu"
        assert second.payload["os"] == "windows"                      # platform when no name
        assert second.payload["last_keep_alive"] is None

        nodes, _ = _graph(build_topology("org-x", events=[e.to_dict() for e in events]))
        assert nodes["wazuh:agent:001"]["meta"]["last_seen"] == "2026-11-09T10:00:00+00:00"
        assert nodes["wazuh:agent:002"]["status"] == "warning"

    @staticmethod
    def _splunk(search):
        from app.connectors.splunk import SplunkConnector

        connector = SplunkConnector("c-splunk", "org-x", {"mcp_url": "https://splunk.test", "api_key": "token"}, {})

        class Client:
            def __init__(self):
                self.queries = []

            async def search(self, query, earliest_time="-24h", latest_time="now"):
                self.queries.append((query, earliest_time))
                return search(query)

        connector._client = Client()
        return connector

    def test_splunk_host_inventory_is_one_event(self):
        import asyncio
        from types import SimpleNamespace

        from app.connectors.splunk import HOST_INVENTORY_QUERY

        last = datetime(2026, 11, 9, 9, 30, tzinfo=timezone.utc)

        def search(query):
            rows = [
                SimpleNamespace(host="", raw="", parsed_fields={"host": "web-01", "lastTime": str(int(last.timestamp())), "totalCount": "1200"}),
                SimpleNamespace(host="fw-01", raw='{"host": "fw-01", "lastTime": 1700000000, "totalCount": 5}', parsed_fields={}),
                SimpleNamespace(host="web-01", raw="", parsed_fields={"host": "web-01"}),          # duplicate
                SimpleNamespace(host="silent", raw="not json", parsed_fields={}),                    # no lastTime
            ] + [SimpleNamespace(host=f"h-{i}", raw="", parsed_fields={"host": f"h-{i}"}) for i in range(300)]
            return SimpleNamespace(events=rows)

        connector = self._splunk(search)
        events = asyncio.run(connector._sync_host_inventory())

        assert connector._client.queries == [(HOST_INVENTORY_QUERY, "-7d")]
        assert HOST_INVENTORY_QUERY == "| metadata type=hosts index=* | fields host lastTime totalCount"
        assert len(events) == 1
        event = events[0]
        assert event.event_type == "splunk.host_inventory"
        assert event.source_system == "splunk"
        assert event.source_event_id.startswith("splunk-host-inventory-")
        hosts = event.payload["hosts"]
        assert len(hosts) == 200                                        # capped
        assert hosts[0] == {"host": "web-01", "last_seen": last.isoformat(), "event_count": 1200}
        assert hosts[1]["host"] == "fw-01" and hosts[1]["event_count"] == 5
        assert hosts[1]["last_seen"].startswith("2023-11-14")
        assert hosts[2] == {"host": "silent", "last_seen": None, "event_count": None}   # never "now"

        nodes, _ = _graph(build_topology("org-x", events=[event.to_dict()]))
        assert nodes["splunk:host:fw-01"]["status"] == "warning"
        assert nodes["splunk:host:silent"]["status"] == "unknown"

    def test_splunk_host_inventory_failure_is_tolerated(self):
        import asyncio
        from types import SimpleNamespace

        def refuse(query):
            raise RuntimeError("metadata search not allowed")

        assert asyncio.run(self._splunk(refuse)._sync_host_inventory()) == []
        assert asyncio.run(self._splunk(lambda q: SimpleNamespace(events=[]))._sync_host_inventory()) == []

    def test_splunk_sync_appends_host_inventory_last(self):
        import asyncio
        from types import SimpleNamespace

        from app.connectors.splunk import HOST_INVENTORY_QUERY

        def search(query):
            if query == HOST_INVENTORY_QUERY:
                return SimpleNamespace(events=[SimpleNamespace(host="web-01", raw="", parsed_fields={"host": "web-01"})])
            if "mfa_logs" in query:
                return SimpleNamespace(events=[SimpleNamespace(
                    id="e-1", time=datetime.now(timezone.utc), host="idp", sourcetype="mfa_logs",
                    source="okta", raw="{}", parsed_fields={"severity": "low"},
                )])
            return SimpleNamespace(events=[])

        events = asyncio.run(self._splunk(search).sync())
        assert [e.event_type for e in events] == ["splunk.mfa_evidence", "splunk.host_inventory"]


# ---------------------------------------------------------------------------
# API contract
# ---------------------------------------------------------------------------

OWNER = User(uid="net-owner", email="owner@example.com", name="Owner")
STRANGER = User(uid="net-stranger", email="stranger@example.com", name="Stranger")


def _as(client, user):
    async def override():
        return user
    client.app.dependency_overrides[get_optional_user] = override


@pytest.fixture
def owned_org(db_session):
    org = Organization(id="net-org-1", name="Net Org", owner_uid=OWNER.uid)
    db_session.add(org)
    db_session.commit()
    return org


class TestTopologyEndpoint:
    def test_demo_org_returns_servers_and_internet_exposure(self, client):
        resp = client.get("/api/v1/network/topology", params={"org_id": "demo-northstar-health"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["demo"] is True
        assert body["summary"]["empty"] is False
        types = {n["type"] for n in body["nodes"]}
        assert "server" in types
        assert "connector" in types
        kinds = {e["kind"] for e in body["edges"]}
        # The recorded fixture carries an open-security-group finding.
        assert "exposed_to_internet" in kinds
        assert any(n["id"] == INTERNET_NODE_ID for n in body["nodes"])
        node_ids = {n["id"] for n in body["nodes"]}
        for e in body["edges"]:
            assert e["source"] in node_ids and e["target"] in node_ids

    def test_demo_org_response_carries_live_block_and_network_counters(self, client):
        body = client.get("/api/v1/network/topology", params={"org_id": "demo-health-org"}).json()
        assert body["demo"] is True
        assert body["live"]["mode"] == "demo"
        assert body["live"]["sources"]
        assert body["summary"]["networks"] == 3
        assert body["summary"]["vpns"] == 2
        assert body["summary"]["vpn_down"] == 0
        assert {"network", "vpn", "gateway"} <= {n["type"] for n in body["nodes"]}
        assert {"member_of", "vpn_tunnel", "talks_to"} <= {e["kind"] for e in body["edges"]}

    def test_demo_legal_org_has_its_own_servers(self, client):
        health = client.get("/api/v1/network/topology", params={"org_id": "demo-northstar-health"}).json()
        legal = client.get("/api/v1/network/topology", params={"org_id": "demo-northstar-cole"}).json()
        health_labels = {n["label"] for n in health["nodes"]}
        legal_labels = {n["label"] for n in legal["nodes"]}
        assert any("metro-health" in l for l in health_labels)
        assert any("northstar-cole" in l for l in legal_labels)
        assert not any("metro-health" in l for l in legal_labels)

    def test_real_org_with_nothing_connected_is_empty(self, client, owned_org):
        _as(client, OWNER)
        resp = client.get("/api/v1/network/topology", params={"org_id": owned_org.id})
        assert resp.status_code == 200
        body = resp.json()
        assert body["demo"] is False
        assert body["nodes"] == []
        assert body["edges"] == []
        assert body["summary"]["empty"] is True
        assert body["summary"]["hint"] == "connect a system"
        assert body["live"] == {"mode": "empty", "latest_event_at": None, "sources": []}
        assert body["summary"]["networks"] == 0 and body["summary"]["vpns"] == 0 and body["summary"]["vpn_down"] == 0

    def test_foreign_org_is_not_found(self, client, owned_org):
        _as(client, STRANGER)
        resp = client.get("/api/v1/network/topology", params={"org_id": owned_org.id})
        assert resp.status_code == 404
        body = resp.json()
        code = (body.get("error") or body.get("detail") or {}).get("code")
        assert code == "ORGANIZATION_NOT_FOUND"

    def test_missing_org_id_is_rejected(self, client):
        assert client.get("/api/v1/network/topology").status_code == 422
