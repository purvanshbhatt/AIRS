"""
Comprehensive E2E Tests for All 7 Telemetry Connectors.

Validates:
1. Model & Registry ConnectorType enums have all platforms (aws, duo, webhook, veeam, etc.)
2. ConnectorRegistry correctly resolves all 7 connector classes
3. ConnectorManager registers and retrieves all 7 connectors with encrypted credentials
4. Proper credential preservation (role_arn, external_id, client_id, etc.)
5. Health checks and permissions validation are non-blocking and robust
6. AWS STS assume_role receives ExternalId
"""
import uuid
import pytest
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.organization import Organization
from app.models.connector import Connector, ConnectorType, ConnectorAuthMethod, ConnectorStatus
from app.connectors.registry import get_connector_class, ConnectorRegistry
import app.connectors  # Ensure auto-registration


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def test_org(db_session):
    org = Organization(id=str(uuid.uuid4()), name="Test Healthcare System")
    db_session.add(org)
    db_session.commit()
    return org


def test_connector_type_enum_completeness():
    """Verify all 7 connector platforms are recognized in ConnectorType enums."""
    expected = ["aws", "splunk", "wazuh", "microsoft", "veeam", "duo", "webhook"]
    model_values = [e.value for e in ConnectorType]
    registry_values = ConnectorRegistry.list_available_connectors()

    for item in expected:
        assert item in model_values, f"Missing {item} from app.models.connector.ConnectorType"
        # Registry has aws_security_hub as canonical for aws
        if item == "aws":
            assert "aws_security_hub" in registry_values
        else:
            assert item in registry_values, f"Missing {item} from ConnectorRegistry"


def test_registry_resolves_all_connector_classes():
    """Verify ConnectorRegistry.get_connector_class resolves each of the 7 types."""
    expected_mapping = {
        "aws": "AWSSecurityHubConnector",
        "aws_security_hub": "AWSSecurityHubConnector",
        "splunk": "SplunkConnector",
        "wazuh": "WazuhConnector",
        "microsoft": "MicrosoftConnector",
        "veeam": "VeeamConnector",
        "duo": "DuoConnector",
        "webhook": "WebhookConnector",
    }
    for c_type, expected_class_name in expected_mapping.items():
        cls = get_connector_class(c_type)
        assert cls.__name__ == expected_class_name, f"Expected {expected_class_name} for {c_type}, got {cls.__name__}"


def test_register_and_retrieve_all_connectors(db_session, test_org):
    """Verify ConnectorManager registers all 7 connectors with accurate credentials."""
    from app.services.connector_manager import ConnectorManager

    mgr = ConnectorManager(db_session, test_org.id)

    configs = [
        ("aws", "AWS Telemetry", "iam_role", {
            "role_arn": "arn:aws:iam::505467908065:role/resilai-test-connector-role",
            "external_id": "resilai-test-2026",
        }),
        ("microsoft", "Microsoft 365", "oauth", {
            "tenant_id": "tenant-abc",
            "client_id": "client-123",
            "client_secret": "sec-456",
        }),
        ("splunk", "Splunk Enterprise", "api_key", {
            "host": "splunk.example.com",
            "port": "8089",
            "api_key": "splunk-token-xyz",
        }),
        ("wazuh", "Wazuh XDR", "api_key", {
            "manager_host": "wazuh.example.com",
            "port": "55000",
            "api_key": "wazuh-key-123",
        }),
        ("veeam", "Veeam Backup", "api_key", {
            "server_url": "https://veeam.example.com:9419",
            "api_key": "veeam-token-999",
        }),
        ("duo", "Cisco Duo Security", "api_key", {
            "integration_key": "DIXXXXXXXXXXXXXXXXXX",
            "secret_key": "skey-123456",
            "api_hostname": "api-123.duosecurity.com",
        }),
        ("webhook", "MSP Ingestion Webhook", "webhook", {
            "webhook_name": "Primary MSP Feed",
        }),
    ]

    for c_type, name, auth_method, creds in configs:
        c = mgr.register_connector(
            connector_type=c_type,
            display_name=name,
            auth_method=auth_method,
            credentials=creds,
            config=creds,
            sync_interval_minutes=15,
            created_by="test-admin",
        )
        assert c.id is not None
        assert c.connector_type == c_type
        assert c.status == ConnectorStatus.pending_auth.value

        # Decrypt & verify credentials preserved
        decrypted = mgr._decrypt_credentials(c.encrypted_credentials)
        for k, v in creds.items():
            assert decrypted.get(k) == v, f"Mismatch in {k} for connector {c_type}"

    all_connectors = mgr.list_connectors()
    assert len(all_connectors) == len(configs)


@pytest.mark.asyncio
async def test_aws_connector_passes_external_id_to_sts(db_session, test_org):
    """Verify AWSSecurityHubConnector includes ExternalId when assuming cross-account role."""
    from app.connectors.aws_security_hub import AWSSecurityHubConnector

    connector = AWSSecurityHubConnector(
        connector_id="test-aws-conn",
        org_id=test_org.id,
        credentials={
            "role_arn": "arn:aws:iam::123456789012:role/AuditRole",
            "external_id": "test-ext-id-123",
            "aws_region": "us-east-1",
        },
        config={},
    )

    mock_boto3 = MagicMock()
    mock_sts = MagicMock()
    mock_sts.assume_role.return_value = {
        "Credentials": {
            "AccessKeyId": "AKIA_MOCK",
            "SecretAccessKey": "SECRET_MOCK",
            "SessionToken": "TOKEN_MOCK",
        }
    }
    mock_session = MagicMock()
    mock_hub = MagicMock()
    mock_session.client.return_value = mock_hub
    mock_boto3.Session.return_value = mock_session
    mock_boto3.client.return_value = mock_sts

    with patch.dict("sys.modules", {"boto3": mock_boto3}):
        ok = await connector.authenticate()
        assert ok is True
        mock_sts.assume_role.assert_called_once_with(
            RoleArn="arn:aws:iam::123456789012:role/AuditRole",
            RoleSessionName="resilai-connector-test-aws",
            DurationSeconds=3600,
            ExternalId="test-ext-id-123",
        )


@pytest.mark.asyncio
async def test_webhook_connector_lifecycle(db_session, test_org):
    """Verify WebhookConnector authenticate, sync, and health_check work without external network."""
    from app.connectors.webhook import WebhookConnector

    connector = WebhookConnector(
        connector_id="webhook-001",
        org_id=test_org.id,
        credentials={"webhook_name": "Clinic MSP Feed"},
        config={},
    )

    assert await connector.authenticate() is True
    health = await connector.health_check()
    assert health.status == "healthy"

    events = await connector.sync()
    assert len(events) == 1
    assert events[0].event_type == "webhook.heartbeat"
    assert events[0].payload["webhook_name"] == "Clinic MSP Feed"


@pytest.mark.asyncio
async def test_all_connectors_health_check_non_blocking(db_session, test_org):
    """Verify health_check on all 7 connectors returns clean ConnectorHealth objects without throwing unhandled exceptions."""
    from app.services.connector_manager import ConnectorManager

    mgr = ConnectorManager(db_session, test_org.id)
    c_types = ["aws", "microsoft", "splunk", "wazuh", "veeam", "duo", "webhook"]

    for c_type in c_types:
        c = mgr.register_connector(
            connector_type=c_type,
            display_name=f"Test {c_type}",
            auth_method="api_key",
            credentials={"host": "127.0.0.1", "server_url": "http://127.0.0.1"},
            config={},
        )
        health = await mgr.health_check(c.id)
        assert health.status in ("healthy", "unreachable", "degraded", "unknown")
        assert isinstance(health.message, str)
