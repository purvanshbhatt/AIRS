"""
Discovery honesty tests.

Product rule: no fabricated inventory for real organizations. Real orgs read
their registered connectors (AWS via boto3, Microsoft via Graph); a missing
connector yields zero rows and status ``not_connected``. Synthetic rows are
reserved for demo tenants.

All network access is stubbed with unittest.mock: boto3 sessions are injected
through ``session_factory`` and Graph HTTP through ``http_client_factory``.
"""
import asyncio
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("ENV", "local")

from app.models.discovered_asset import DiscoveredAsset
from app.models.discovery import EvidenceSource, HostAsset, InstalledProduct
from app.models.organization import Organization
from app.services.asset_discovery import AssetDiscoveryService
from app.services.connector_manager import ConnectorManager
from app.services.discovery.aws_discovery import AWSDiscoveryService
from app.services.discovery.aws_ssm_poller import AWSConfigPoller as SSMPoller
from app.services.discovery.direct_connectors import AWSConfigPoller, KubernetesInventoryPoller, MicrosoftGraphPoller
from app.services.discovery.discovery import DiscoveryStatus, TechnologyDiscoveryService, is_demo_org
from app.services.discovery.graph_discovery import GraphDiscoveryService
from app.services.discovery.orchestrator import TechnologyDiscoveryOrchestrator

REAL_ORG = "test-org-123"  # provisioned by client_with_org (org_mode defaults to pilot)
DEMO_ORG = "demo-org-001"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_demo_org(db_session) -> str:
    org = Organization(id=DEMO_ORG, name="Demo Clinic", owner_uid="demo-owner", org_mode="demo")
    db_session.add(org)
    db_session.commit()
    return org.id


def _register_aws(db_session, org_id=REAL_ORG):
    return ConnectorManager(db_session, org_id).register_connector(
        connector_type="aws_security_hub",
        display_name="Pilot AWS",
        auth_method="api_key",
        credentials={
            "aws_access_key_id": "AKIATEST",
            "aws_secret_access_key": "secret",
            "aws_region": "eu-west-1",
        },
        created_by="test",
    )


def _register_microsoft(db_session, org_id=REAL_ORG):
    return ConnectorManager(db_session, org_id).register_connector(
        connector_type="microsoft",
        display_name="Pilot M365",
        auth_method="oauth",
        credentials={"tenant_id": "t", "client_id": "c", "client_secret": "s"},
        created_by="test",
    )


def _access_denied(operation: str) -> ClientError:
    return ClientError(
        {"Error": {"Code": "AccessDeniedException", "Message": "not authorized"}},
        operation,
    )


def _stub_aws_session(ssm_denied: bool = False, with_ssm_apps: bool = True):
    """boto3.Session stand-in whose clients answer describe_* with fixed payloads."""
    ec2 = MagicMock(name="ec2")
    ec2.describe_instances.return_value = {
        "Reservations": [{
            "Instances": [
                {
                    "InstanceId": "i-0real000000000001",
                    "InstanceType": "t3.medium",
                    "State": {"Name": "running"},
                    "PrivateIpAddress": "10.1.2.3",
                    "PublicIpAddress": "54.1.2.3",
                    "PlatformDetails": "Linux/UNIX",
                    "LaunchTime": datetime(2026, 1, 2, tzinfo=timezone.utc),
                    "Tags": [{"Key": "Name", "Value": "pilot-app-01"}],
                },
                {
                    "InstanceId": "i-0real000000000002",
                    "InstanceType": "t3.small",
                    "State": {"Name": "stopped"},
                    "PrivateIpAddress": "10.1.2.4",
                    "Platform": "windows",
                    "PlatformDetails": "Windows",
                    "LaunchTime": datetime(2026, 1, 3, tzinfo=timezone.utc),
                },
                {
                    "InstanceId": "i-0terminated000000",
                    "State": {"Name": "terminated"},
                },
            ]
        }]
    }
    rds = MagicMock(name="rds")
    rds.describe_db_instances.return_value = {
        "DBInstances": [{
            "DBInstanceIdentifier": "pilot-postgres",
            "Engine": "postgres",
            "EngineVersion": "15.4",
            "DBInstanceClass": "db.t3.medium",
            "DBInstanceStatus": "available",
            "StorageEncrypted": True,
            "PubliclyAccessible": False,
            "MultiAZ": True,
            "Endpoint": {"Address": "pilot-postgres.abc.eu-west-1.rds.amazonaws.com"},
        }]
    }
    ssm = MagicMock(name="ssm")
    if ssm_denied:
        ssm.describe_instance_information.side_effect = _access_denied("DescribeInstanceInformation")
    else:
        ssm.describe_instance_information.return_value = {
            "InstanceInformationList": [{"InstanceId": "i-0real000000000001", "PlatformName": "Amazon Linux"}]
        }
        ssm.list_inventory_entries.return_value = {
            "Entries": [
                {"Name": "python3", "Version": "3.11.6", "Publisher": "Amazon Linux"},
                {"Name": "nginx", "Version": "1.24.0", "Publisher": "Amazon Linux"},
            ] if with_ssm_apps else []
        }
    clients = {"ec2": ec2, "rds": rds, "ssm": ssm}
    session = MagicMock(name="session")
    session.client.side_effect = lambda name, **kw: clients[name]
    return session, clients


class _StubResponse:
    def __init__(self, status_code, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = str(payload)

    def json(self):
        return self._payload


class _StubGraphClient:
    """httpx.Client stand-in: routes by URL substring."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []
        self.closed = False

    def get(self, url):
        self.calls.append(url)
        for needle, response in self.routes.items():
            if needle in url:
                return response
        return _StubResponse(404)

    def close(self):
        self.closed = True


def _graph_routes(devices_status=200, alerts_status=403):
    devices = {
        "value": [
            {"id": "dev-1", "deviceName": "RECEPTION-PC", "operatingSystem": "Windows",
             "osVersion": "10.0.22631.3155", "complianceState": "compliant",
             "isEncrypted": True, "lastSyncDateTime": "2026-11-05T10:00:00Z"},
            {"id": "dev-2", "deviceName": "DR-SMITH-MBP", "operatingSystem": "macOS",
             "osVersion": "14.5", "complianceState": "noncompliant",
             "isEncrypted": False, "lastSyncDateTime": "2026-11-04T10:00:00Z"},
        ]
    }
    return {
        "/deviceManagement/managedDevices": _StubResponse(devices_status, devices),
        "/security/alerts_v2": _StubResponse(alerts_status, {"value": []}),
    }


# ---------------------------------------------------------------------------
# (a) real org, no AWS connector -> nothing, not_connected, no mock evidence
# ---------------------------------------------------------------------------

def test_real_org_without_aws_connector_discovers_nothing(db_session, client_with_org):
    assert is_demo_org(db_session, REAL_ORG) is False
    inventory = TechnologyDiscoveryService(db_session, REAL_ORG).create_inventory("test")

    svc = AWSDiscoveryService(db_session, REAL_ORG, session_factory=MagicMock(side_effect=AssertionError("no network")))
    assert svc.discover_from_aws(inventory.id) == 0
    assert svc.last_result.status == DiscoveryStatus.NOT_CONNECTED
    assert db_session.query(HostAsset).filter(HostAsset.org_id == REAL_ORG).count() == 0
    assert db_session.query(EvidenceSource).count() == 0


def test_real_org_orchestrator_records_not_connected_everywhere(db_session, client_with_org):
    orch = TechnologyDiscoveryOrchestrator(db_session, REAL_ORG)
    assert orch.is_demo is False
    inventory = orch.run_discovery_cycle()

    assert db_session.query(HostAsset).filter(HostAsset.inventory_id == inventory.id).count() == 0
    assert orch.last_results["aws"].status == DiscoveryStatus.NOT_CONNECTED
    assert orch.last_results["ms_graph"].status == DiscoveryStatus.NOT_CONNECTED
    assert orch.last_results["wazuh"].status == DiscoveryStatus.NOT_CONNECTED
    assert "aws=not_connected" in inventory.discovery_source
    assert "ms_graph=not_connected" in inventory.discovery_source
    assert "wazuh=not_connected" in inventory.discovery_source


def test_real_org_asset_discovery_service_seeds_nothing(db_session, client_with_org):
    svc = AssetDiscoveryService(db_session, REAL_ORG)
    assert svc.discover_assets() == 0
    assert db_session.query(DiscoveredAsset).filter(DiscoveredAsset.org_id == REAL_ORG).count() == 0
    assert svc.last_results["aws"].status == DiscoveryStatus.NOT_CONNECTED
    assert svc.last_results["ms_graph"].status == DiscoveryStatus.NOT_CONNECTED


# ---------------------------------------------------------------------------
# (b) real org with AWS connector + stubbed boto3 session -> real rows
# ---------------------------------------------------------------------------

def test_real_org_with_aws_connector_creates_rows_from_stubbed_session(db_session, client_with_org):
    connector = _register_aws(db_session)
    session, clients = _stub_aws_session()
    seen = {}

    def factory(credentials, config, connector_id):
        seen["credentials"] = credentials
        seen["connector_id"] = connector_id
        return session

    inventory = TechnologyDiscoveryService(db_session, REAL_ORG).create_inventory("test")
    svc = AWSDiscoveryService(db_session, REAL_ORG, session_factory=factory)
    created = svc.discover_from_aws(inventory.id)

    # Credentials came from the registered connector, decrypted.
    assert seen["connector_id"] == connector.id
    assert seen["credentials"]["aws_region"] == "eu-west-1"
    assert seen["credentials"]["aws_access_key_id"] == "AKIATEST"

    # 2 EC2 (running + stopped, terminated skipped) + 1 RDS
    assert created == 3
    assets = {a.hostname: a for a in db_session.query(HostAsset).filter(HostAsset.inventory_id == inventory.id)}
    assert set(assets) == {"pilot-app-01", "i-0real000000000002", "pilot-postgres"}
    assert assets["pilot-app-01"].ip_address == "10.1.2.3"
    assert assets["pilot-app-01"].operating_system == "Linux/UNIX"
    assert assets["pilot-app-01"].cloud_provider == "AWS"
    assert assets["i-0real000000000002"].operating_system == "Windows"

    products = db_session.query(InstalledProduct).join(HostAsset).filter(HostAsset.inventory_id == inventory.id).all()
    by_name = {p.product_name: p for p in products}
    assert by_name["postgres"].version == "15.4"
    assert by_name["postgres"].installation_source == "aws_rds"
    assert by_name["python3"].version == "3.11.6"
    assert by_name["python3"].installation_source == "aws_systems_manager"
    assert by_name["nginx"].asset_id == assets["pilot-app-01"].id

    evidence = db_session.query(EvidenceSource).all()
    assert len(evidence) == 3
    assert {e.connector_name for e in evidence} == {"Pilot AWS"}
    assert all(e.source_type == "aws" for e in evidence)

    clients["ssm"].list_inventory_entries.assert_called_with(InstanceId="i-0real000000000001", TypeName="AWS:Application")
    assert svc.last_result.status == DiscoveryStatus.OK
    assert svc.last_result.denied_apis == []
    assert svc.last_result.detail == {"ec2_instances": 2, "rds_instances": 1, "ssm_managed_instances": 1}


def test_aws_access_denied_is_recorded_not_fabricated(db_session, client_with_org):
    _register_aws(db_session)
    session, _ = _stub_aws_session(ssm_denied=True)
    inventory = TechnologyDiscoveryService(db_session, REAL_ORG).create_inventory("test")
    svc = AWSDiscoveryService(db_session, REAL_ORG, session_factory=lambda *a: session)

    assert svc.discover_from_aws(inventory.id) == 3
    assert svc.last_result.status == DiscoveryStatus.PARTIAL
    assert svc.last_result.denied_apis == ["ssm:DescribeInstanceInformation"]
    # Only the RDS engine is attested; no SSM software was invented.
    names = {p.product_name for p in db_session.query(InstalledProduct).all()}
    assert names == {"postgres"}


def test_aws_connector_feeds_discovered_assets_table(db_session, client_with_org):
    _register_aws(db_session)
    session, _ = _stub_aws_session()
    svc = AssetDiscoveryService(db_session, REAL_ORG, session_factory=lambda *a: session)

    assert svc.discover_assets() == 3
    rows = db_session.query(DiscoveredAsset).filter(DiscoveredAsset.org_id == REAL_ORG).all()
    assert {(r.product, r.version, r.source) for r in rows} == {
        ("postgres", "15.4", "AWS RDS"),
        ("python3", "3.11.6", "AWS Systems Manager"),
        ("nginx", "1.24.0", "AWS Systems Manager"),
    }
    assert svc.last_results["aws"].status == DiscoveryStatus.OK
    assert svc.last_results["ms_graph"].status == DiscoveryStatus.NOT_CONNECTED

    # Idempotent: a second run touches last_seen instead of duplicating rows.
    assert svc.discover_assets() == 3


# ---------------------------------------------------------------------------
# (c) demo org -> synthetic rows still produced, clearly labelled
# ---------------------------------------------------------------------------

def test_demo_org_keeps_synthetic_inventory(db_session):
    _make_demo_org(db_session)
    assert is_demo_org(db_session, DEMO_ORG) is True

    orch = TechnologyDiscoveryOrchestrator(db_session, DEMO_ORG)
    assert orch.is_demo is True
    inventory = orch.run_discovery_cycle()

    hostnames = {a.hostname for a in db_session.query(HostAsset).filter(HostAsset.inventory_id == inventory.id)}
    assert {"EKS-Worker-Node-1", "production-postgres-rds", "desktop-sales-01", "laptop-eng-04"} <= hostnames
    assert orch.last_results["aws"].status == DiscoveryStatus.DEMO
    assert orch.last_results["ms_graph"].status == DiscoveryStatus.DEMO
    assert "aws=demo" in inventory.discovery_source
    assert all("synthetic" in e.connector_name for e in db_session.query(EvidenceSource).all()
               if e.source_type in ("aws", "ms_graph"))


def test_demo_org_asset_discovery_seeds_47(db_session):
    _make_demo_org(db_session)
    svc = AssetDiscoveryService(db_session, DEMO_ORG)
    assert svc.discover_assets() == 47
    assert svc.last_results["demo"].status == DiscoveryStatus.DEMO


def test_demo_prefix_without_org_row_counts_as_demo(db_session):
    assert is_demo_org(db_session, "demo-sandbox-xyz") is True
    assert is_demo_org(db_session, "unknown-org") is False


# ---------------------------------------------------------------------------
# (d) Graph discovery with a stubbed httpx client -> two device rows
# ---------------------------------------------------------------------------

def test_graph_discovery_two_managed_devices(db_session, client_with_org):
    connector = _register_microsoft(db_session)
    client = _StubGraphClient(_graph_routes())
    tokens = {}

    def token_provider(credentials, config, connector_id):
        tokens["credentials"] = credentials
        tokens["connector_id"] = connector_id
        return "stub-token"

    headers_seen = {}

    def http_client_factory(headers):
        headers_seen.update(headers)
        return client

    inventory = TechnologyDiscoveryService(db_session, REAL_ORG).create_inventory("test")
    svc = GraphDiscoveryService(
        db_session, REAL_ORG, http_client_factory=http_client_factory, token_provider=token_provider
    )
    created = svc.discover_from_graph(inventory.id)

    assert created == 2
    assert tokens["connector_id"] == connector.id
    assert tokens["credentials"]["tenant_id"] == "t"
    assert headers_seen == {"Authorization": "Bearer stub-token"}
    assert client.closed is True
    assert any("/deviceManagement/managedDevices" in u for u in client.calls)
    assert any("/security/alerts_v2?$top=50" in u for u in client.calls)

    assets = {a.hostname: a for a in db_session.query(HostAsset).filter(HostAsset.inventory_id == inventory.id)}
    assert set(assets) == {"RECEPTION-PC", "DR-SMITH-MBP"}
    assert assets["RECEPTION-PC"].operating_system == "Windows 10.0.22631.3155"
    assert assets["RECEPTION-PC"].asset_type.value == "HOST"

    products = {p.product_name: p for p in db_session.query(InstalledProduct).all()}
    assert products["windows"].version == "10.0.22631.3155"
    assert products["windows"].installation_source == "microsoft_intune"
    assert {e.connector_name for e in db_session.query(EvidenceSource).all()} == {"Pilot M365"}

    # alerts_v2 returned 403: recorded, nothing invented.
    assert svc.last_result.status == DiscoveryStatus.PARTIAL
    assert svc.last_result.denied_apis == ["/security/alerts_v2"]


def test_graph_403_on_devices_is_permission_missing(db_session, client_with_org):
    _register_microsoft(db_session)
    client = _StubGraphClient(_graph_routes(devices_status=403, alerts_status=200))
    inventory = TechnologyDiscoveryService(db_session, REAL_ORG).create_inventory("test")
    svc = GraphDiscoveryService(
        db_session, REAL_ORG, http_client_factory=lambda h: client, token_provider=lambda *a: "tok"
    )
    assert svc.discover_from_graph(inventory.id) == 0
    assert svc.last_result.status == DiscoveryStatus.PERMISSION_MISSING
    assert "/deviceManagement/managedDevices" in svc.last_result.denied_apis
    assert db_session.query(HostAsset).count() == 0


def test_graph_auth_failure_creates_nothing(db_session, client_with_org):
    _register_microsoft(db_session)
    inventory = TechnologyDiscoveryService(db_session, REAL_ORG).create_inventory("test")
    svc = GraphDiscoveryService(
        db_session, REAL_ORG,
        http_client_factory=MagicMock(side_effect=AssertionError("must not hit network")),
        token_provider=lambda *a: None,
    )
    assert svc.discover_from_graph(inventory.id) == 0
    assert svc.last_result.status == DiscoveryStatus.AUTH_FAILED
    assert db_session.query(HostAsset).count() == 0


def test_graph_connector_feeds_discovered_assets_table(db_session, client_with_org):
    _register_microsoft(db_session)
    client = _StubGraphClient(_graph_routes())
    svc = AssetDiscoveryService(
        db_session, REAL_ORG, http_client_factory=lambda h: client, token_provider=lambda *a: "tok"
    )
    assert svc.discover_assets() == 2
    rows = db_session.query(DiscoveredAsset).filter(DiscoveredAsset.org_id == REAL_ORG).all()
    assert {(r.product, r.version, r.source) for r in rows} == {
        ("windows", "10.0.22631.3155", "Microsoft Intune"),
        ("macos", "14.5", "Microsoft Intune"),
    }


# ---------------------------------------------------------------------------
# Direct pollers: no synthetic fallback for real tenants
# ---------------------------------------------------------------------------

def test_ssm_poller_real_access_denied_yields_no_rows():
    session, _ = _stub_aws_session(ssm_denied=True)
    poller = SSMPoller(credentials={"aws_region": "us-east-1"}, session_factory=lambda *a: session)
    records = asyncio.run(poller.poll())
    assert records == []
    assert poller.status == DiscoveryStatus.PERMISSION_MISSING
    assert poller.result.denied_apis == ["ssm:DescribeInstanceInformation"]


def test_ssm_poller_real_returns_inventory_entries_with_api_source():
    session, _ = _stub_aws_session()
    poller = SSMPoller(credentials={"aws_region": "us-east-1"}, session_factory=lambda *a: session)
    records = asyncio.run(poller.poll())
    assert {(r.software_name, r.version, r.host_id) for r in records} == {
        ("python3", "3.11.6", "i-0real000000000001"),
        ("nginx", "1.24.0", "i-0real000000000001"),
    }
    assert all(r.raw_evidence["source"] == "ssm:ListInventoryEntries" for r in records)
    assert all("mock" not in r.raw_evidence for r in records)
    assert poller.status == DiscoveryStatus.OK


def test_ssm_poller_demo_only_returns_synthetic():
    demo = asyncio.run(SSMPoller(credentials={}, is_demo=True).poll())
    assert len(demo) == 2 and all(r.raw_evidence.get("mock") is True for r in demo)


def test_direct_pollers_real_tenant_no_mock():
    session, _ = _stub_aws_session()
    rds_records = asyncio.run(AWSConfigPoller(credentials={"aws_region": "x"}, session_factory=lambda *a: session).poll())
    assert [(r.software_name, r.version, r.host_id) for r in rds_records] == [("postgres", "15.4", "pilot-postgres")]
    assert rds_records[0].raw_evidence["source"] == "rds:DescribeDBInstances"
    assert "mock" not in rds_records[0].raw_evidence

    graph = MicrosoftGraphPoller(
        credentials={"access_token": "tok"}, http_client_factory=lambda h: _StubGraphClient(_graph_routes())
    )
    graph_records = asyncio.run(graph.poll())
    assert {r.host_id for r in graph_records} == {"dev-1", "dev-2"}
    assert all(r.raw_evidence["source"] == "/deviceManagement/managedDevices" for r in graph_records)

    assert asyncio.run(MicrosoftGraphPoller(credentials={}).poll()) == []

    k8s = KubernetesInventoryPoller(credentials={})
    assert asyncio.run(k8s.poll()) == []
    assert k8s.status == DiscoveryStatus.NOT_IMPLEMENTED
