"""
Network topology — builder unit tests and /api/v1/network/topology contract.

Covers:
  * demo org → real recorded findings drive the map (servers + internet exposure)
  * real org with nothing connected → empty graph with a plain-language hint
  * foreign org → 404 (no data leak across tenants)
  * builder over a handful of synthetic events (merging, statuses, edges)
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.core.auth import User, get_optional_user
from app.models.organization import Organization
from app.services.network_topology import INTERNET_NODE_ID, build_topology, parse_arn, zone_for_hint


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

    def test_foreign_org_is_not_found(self, client, owned_org):
        _as(client, STRANGER)
        resp = client.get("/api/v1/network/topology", params={"org_id": owned_org.id})
        assert resp.status_code == 404
        body = resp.json()
        code = (body.get("error") or body.get("detail") or {}).get("code")
        assert code == "ORGANIZATION_NOT_FOUND"

    def test_missing_org_id_is_rejected(self, client):
        assert client.get("/api/v1/network/topology").status_code == 422
