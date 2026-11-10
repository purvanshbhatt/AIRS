"""
AWS connector diagnostics.

A saved AWS connector must end in a verdict the user can act on:

  * the proof of connection is STS, not Security Hub being switched on
  * every failure carries a stable code and a plain-English message, and
    never echoes a credential or raw AWS exception text
  * each data source is reported on its own, and one failing source does
    not stop the others from syncing
  * ConnectorManager persists the verdict in ``config.last_check`` and never
    leaves a checked connector in ``pending_auth``

Every AWS call is stubbed; nothing here touches the network.
"""
import json
import sys
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

import app.connectors  # noqa: F401  (registers connector classes)
from app.connectors.aws_security_hub import AWSSecurityHubConnector
from app.core.security.connector_secrets import scrub_secrets
from app.models.connector import ConnectorStatus
from app.models.organization import Organization
from app.models.telemetry_event import TelemetryEvent
from app.services.connector_manager import ConnectorManager

ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
SESSION_TOKEN = "FQoGZXIvYXdzEXAMPLETOKENvalue"
ACCOUNT = "123456789012"
ROLE_ARN = f"arn:aws:iam::{ACCOUNT}:role/ResilAIReadOnly"
KEY_CREDS = {
    "aws_access_key_id": ACCESS_KEY,
    "aws_secret_access_key": SECRET_KEY,
    "aws_region": "us-east-1",
}

INVALID_KEYS_MESSAGE = "AWS rejected the access key or secret. Check for typos or a deactivated key."
NO_PLATFORM_IDENTITY_MESSAGE = (
    "Role-based access is not available on this workspace yet. Create a read-only "
    "IAM user (SecurityAudit policy) and paste its access key instead."
)

CREDENTIAL_REPORT = (
    "user,arn,user_creation_time,password_enabled,password_last_used,password_last_changed,"
    "password_next_rotation,mfa_active,access_key_1_active,access_key_1_last_rotated,"
    "access_key_1_last_used_date,access_key_2_active,access_key_2_last_rotated,"
    "access_key_2_last_used_date\n"
    f"<root_account>,arn:aws:iam::{ACCOUNT}:root,2020-01-01T00:00:00+00:00,not_supported,"
    "2026-11-01T10:00:00+00:00,not_supported,not_supported,true,false,N/A,N/A,false,N/A,N/A\n"
    f"front-desk,arn:aws:iam::{ACCOUNT}:user/front-desk,2024-03-01T00:00:00+00:00,true,"
    "no_information,2024-03-01T00:00:00+00:00,N/A,false,true,2026-01-05T00:00:00+00:00,"
    "2026-10-30T00:00:00+00:00,false,N/A,N/A\n"
    f"old-contractor,arn:aws:iam::{ACCOUNT}:user/old-contractor,2023-01-01T00:00:00+00:00,false,"
    "N/A,N/A,N/A,false,false,2023-01-01T00:00:00+00:00,N/A,false,N/A,N/A\n"
).encode("utf-8")


# ---------------------------------------------------------------------------
# boto3 stand-in
# ---------------------------------------------------------------------------

def aws_error(code: str, operation: str = "Operation", message: str = "") -> ClientError:
    # The message deliberately carries the key id: it must never be echoed.
    return ClientError(
        {"Error": {"Code": code, "Message": message or f"{code} for key {ACCESS_KEY}"}},
        operation,
    )


class FakeSession:
    def __init__(self, clients):
        self._clients = clients

    def client(self, name, **_kwargs):
        return self._clients[name]


class FakeBoto3:
    """Stands in for the boto3 module: Session(...) and client('sts', ...)."""

    def __init__(self, clients, base_sts=None):
        self.clients = clients
        self.base_sts = base_sts or MagicMock()
        self.session_kwargs = []
        self.client_calls = []

    def Session(self, **kwargs):  # noqa: N802  (mirrors boto3.Session)
        self.session_kwargs.append(kwargs)
        return FakeSession(self.clients)

    def client(self, name, **kwargs):
        self.client_calls.append((name, kwargs))
        return self.base_sts


def make_clients(
    identity_error=None,
    security_hub="not_subscribed",
    guardduty_detectors=(),
    ec2=True,
    iam=True,
    ssm="denied",
    findings=(),
):
    """Service clients for an ordinary small-business account by default:
    no Security Hub, no GuardDuty, EC2 + IAM readable, SSM not permitted."""
    sts = MagicMock()
    if identity_error is not None:
        sts.get_caller_identity.side_effect = identity_error
    else:
        sts.get_caller_identity.return_value = {
            "Account": ACCOUNT,
            "Arn": f"arn:aws:iam::{ACCOUNT}:user/resilai-readonly",
            "UserId": "AIDAEXAMPLE",
        }

    hub = MagicMock()
    if security_hub == "not_subscribed":
        hub.describe_hub.side_effect = aws_error("InvalidAccessException", "DescribeHub")
    elif security_hub == "denied":
        hub.describe_hub.side_effect = aws_error("AccessDeniedException", "DescribeHub")
    else:
        hub.describe_hub.return_value = {"HubArn": f"arn:aws:securityhub:us-east-1:{ACCOUNT}:hub/default"}
        hub.get_findings.return_value = {"Findings": []}
        paginator = MagicMock()
        paginator.paginate.return_value = [{"Findings": list(findings)}]
        hub.get_paginator.return_value = paginator

    guardduty = MagicMock()
    guardduty.list_detectors.return_value = {"DetectorIds": list(guardduty_detectors)}

    ec2_client = MagicMock()
    rds = MagicMock()
    if ec2:
        ec2_client.describe_instances.return_value = {
            "Reservations": [{
                "Instances": [{
                    "InstanceId": "i-0abc123def4567890",
                    "InstanceType": "t3.micro",
                    "State": {"Name": "running"},
                    "PlatformDetails": "Linux/UNIX",
                    "PrivateIpAddress": "10.0.1.15",
                    "Tags": [{"Key": "Name", "Value": "front-desk-server"}],
                }],
            }],
        }
        rds.describe_db_instances.return_value = {
            "DBInstances": [{
                "DBInstanceIdentifier": "patients-db",
                "Engine": "postgres",
                "EngineVersion": "15.4",
                "DBInstanceStatus": "available",
                "DBInstanceClass": "db.t3.micro",
                "StorageEncrypted": True,
                "PubliclyAccessible": False,
            }],
        }
    else:
        ec2_client.describe_instances.side_effect = aws_error("UnauthorizedOperation", "DescribeInstances")
        rds.describe_db_instances.side_effect = aws_error("AccessDenied", "DescribeDBInstances")

    iam_client = MagicMock()
    if iam:
        iam_client.get_account_summary.return_value = {"SummaryMap": {"Users": 2}}
        iam_client.generate_credential_report.return_value = {"State": "COMPLETE"}
        iam_client.get_credential_report.return_value = {"Content": CREDENTIAL_REPORT}
    else:
        iam_client.get_account_summary.side_effect = aws_error("AccessDenied", "GetAccountSummary")

    ssm_client = MagicMock()
    if ssm == "denied":
        ssm_client.describe_instance_information.side_effect = aws_error(
            "AccessDeniedException", "DescribeInstanceInformation"
        )
    else:
        ssm_client.describe_instance_information.return_value = {"InstanceInformationList": []}

    return {
        "sts": sts,
        "securityhub": hub,
        "guardduty": guardduty,
        "ec2": ec2_client,
        "rds": rds,
        "iam": iam_client,
        "ssm": ssm_client,
    }


def make_connector(credentials=None, config=None):
    return AWSSecurityHubConnector(
        connector_id="conn-aws-diagnostics",
        org_id="org-diagnostics",
        credentials=dict(credentials if credentials is not None else KEY_CREDS),
        config=config or {},
    )


@contextmanager
def use_boto3(fake):
    """Swap only the boto3 entry. ``patch.dict(sys.modules)`` would also evict
    every module first imported inside the block (metrics, discovery, ...)."""
    missing = object()
    original = sys.modules.get("boto3", missing)
    sys.modules["boto3"] = fake
    try:
        yield fake
    finally:
        if original is missing:
            sys.modules.pop("boto3", None)
        else:
            sys.modules["boto3"] = original


def assert_no_secrets(*texts):
    for text in texts:
        blob = text if isinstance(text, str) else json.dumps(text, default=str)
        for secret in (SECRET_KEY, ACCESS_KEY, SESSION_TOKEN):
            assert secret not in blob


# ---------------------------------------------------------------------------
# Authentication failures: code + plain-English message, no secrets
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_keys_are_unreachable_with_code_and_no_secret():
    fake = FakeBoto3(make_clients(identity_error=aws_error("InvalidClientTokenId", "GetCallerIdentity")))
    connector = make_connector()

    with use_boto3(fake):
        health = await connector.health_check()

    assert health.status == "unreachable"
    assert health.message == INVALID_KEYS_MESSAGE
    assert connector.last_error_code == "INVALID_KEYS"
    assert connector.last_error == INVALID_KEYS_MESSAGE
    assert connector._authenticated is False
    assert_no_secrets(health.message, connector.last_error)


@pytest.mark.asyncio
async def test_role_arn_without_platform_identity_is_explained():
    fake = FakeBoto3(make_clients())
    connector = make_connector({"role_arn": ROLE_ARN, "external_id": "ext-1", "aws_region": "us-east-1"})

    with use_boto3(fake), patch(
        "app.connectors.aws_security_hub._platform_identity", return_value=None
    ):
        health = await connector.health_check()

    assert health.status == "unreachable"
    assert connector.last_error_code == "NO_PLATFORM_IDENTITY"
    assert health.message == NO_PLATFORM_IDENTITY_MESSAGE
    # Nothing to call AWS with, so nothing was called.
    assert fake.client_calls == []
    assert fake.session_kwargs == []


def test_platform_identity_is_unset_by_default():
    from app.core.config import Settings

    assert Settings.model_fields["RESILAI_AWS_ACCESS_KEY_ID"].default is None
    assert Settings.model_fields["RESILAI_AWS_SECRET_ACCESS_KEY"].default is None


@pytest.mark.asyncio
async def test_role_arn_is_assumed_from_platform_identity_when_no_own_keys():
    base_sts = MagicMock()
    base_sts.assume_role.return_value = {
        "Credentials": {"AccessKeyId": "ASIATEMP", "SecretAccessKey": "temp-secret", "SessionToken": "temp-token"}
    }
    fake = FakeBoto3(make_clients(), base_sts=base_sts)
    connector = make_connector({"role_arn": ROLE_ARN, "external_id": "ext-1", "aws_region": "eu-west-1"})

    with use_boto3(fake), patch(
        "app.connectors.aws_security_hub._platform_identity",
        return_value=("AKIAPLATFORMEXAMPLE", "platform-secret"),
    ):
        assert await connector.authenticate() is True

    name, kwargs = fake.client_calls[0]
    assert name == "sts"
    assert kwargs["aws_access_key_id"] == "AKIAPLATFORMEXAMPLE"
    assert kwargs["aws_secret_access_key"] == "platform-secret"
    base_sts.assume_role.assert_called_once_with(
        RoleArn=ROLE_ARN,
        RoleSessionName="resilai-connector-conn-aws",
        DurationSeconds=3600,
        ExternalId="ext-1",
    )
    assert fake.session_kwargs[0]["aws_session_token"] == "temp-token"
    assert connector.account_id == ACCOUNT


@pytest.mark.asyncio
async def test_own_keys_are_the_base_identity_for_role_assumption():
    base_sts = MagicMock()
    base_sts.assume_role.side_effect = aws_error("AccessDenied", "AssumeRole")
    fake = FakeBoto3(make_clients(), base_sts=base_sts)
    connector = make_connector({**KEY_CREDS, "role_arn": ROLE_ARN})

    with use_boto3(fake), patch(
        "app.connectors.aws_security_hub._platform_identity",
        return_value=("AKIAPLATFORMEXAMPLE", "platform-secret"),
    ):
        health = await connector.health_check()

    assert fake.client_calls[0][1]["aws_access_key_id"] == ACCESS_KEY
    assert health.status == "unreachable"
    assert connector.last_error_code == "ROLE_NOT_ASSUMABLE"
    assert health.message == "AWS refused the role. Check the role's trust policy and External ID."
    assert_no_secrets(health.message)


@pytest.mark.asyncio
async def test_bad_platform_identity_does_not_blame_the_customers_keys():
    base_sts = MagicMock()
    base_sts.assume_role.side_effect = aws_error("InvalidClientTokenId", "AssumeRole")
    fake = FakeBoto3(make_clients(), base_sts=base_sts)
    connector = make_connector({"role_arn": ROLE_ARN})

    with use_boto3(fake), patch(
        "app.connectors.aws_security_hub._platform_identity",
        return_value=("AKIAPLATFORMEXAMPLE", "platform-secret"),
    ):
        assert await connector.authenticate() is False

    assert connector.last_error_code == "PLATFORM_IDENTITY_INVALID"
    assert "platform-secret" not in connector.last_error


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error, code",
    [
        (aws_error("SignatureDoesNotMatch", "GetCallerIdentity"), "INVALID_KEYS"),
        (aws_error("AuthFailure", "GetCallerIdentity"), "INVALID_KEYS"),
        (aws_error("ExpiredToken", "GetCallerIdentity"), "EXPIRED_TOKEN"),
        (EndpointConnectionError(endpoint_url="https://sts.us-eats-1.amazonaws.com"), "NETWORK"),
        (ConnectionError("connection reset"), "NETWORK"),
    ],
)
async def test_identity_errors_map_to_codes(error, code):
    connector = make_connector({**KEY_CREDS, "aws_session_token": SESSION_TOKEN})

    with use_boto3(FakeBoto3(make_clients(identity_error=error))):
        health = await connector.health_check()

    assert health.status == "unreachable"
    assert connector.last_error_code == code
    assert health.message == connector.last_error
    assert_no_secrets(health.message)


@pytest.mark.asyncio
async def test_unknown_errors_name_the_exception_class_never_its_text():
    error = RuntimeError(f"boom with {SECRET_KEY}")
    connector = make_connector()

    with use_boto3(FakeBoto3(make_clients(identity_error=error))):
        health = await connector.health_check()

    assert connector.last_error_code == "UNKNOWN"
    assert "RuntimeError" in health.message
    assert "boom" not in health.message
    assert_no_secrets(health.message)


@pytest.mark.asyncio
async def test_missing_credentials_never_fall_back_to_the_servers_identity():
    fake = FakeBoto3(make_clients())
    connector = make_connector({"aws_region": "us-east-1"})

    with use_boto3(fake):
        health = await connector.health_check()

    assert health.status == "unreachable"
    assert connector.last_error_code == "MISSING_CREDENTIALS"
    assert fake.session_kwargs == []


@pytest.mark.asyncio
async def test_malformed_role_arn_is_rejected_before_calling_aws():
    fake = FakeBoto3(make_clients())
    connector = make_connector({**KEY_CREDS, "role_arn": "resilai-read-only"})

    with use_boto3(fake):
        assert await connector.authenticate() is False

    assert connector.last_error_code == "INVALID_ROLE_ARN"
    assert fake.client_calls == []


@pytest.mark.asyncio
async def test_session_token_is_passed_for_temporary_credentials():
    fake = FakeBoto3(make_clients())
    connector = make_connector({**KEY_CREDS, "aws_session_token": SESSION_TOKEN})

    with use_boto3(fake):
        assert await connector.authenticate() is True

    assert fake.session_kwargs[0]["aws_session_token"] == SESSION_TOKEN


@pytest.mark.asyncio
async def test_safe_sync_reports_the_real_cause():
    connector = make_connector()

    with use_boto3(FakeBoto3(make_clients(identity_error=aws_error("InvalidClientTokenId")))):
        result = await connector.safe_sync()

    assert result.success is False
    assert result.error_details == INVALID_KEYS_MESSAGE


# ---------------------------------------------------------------------------
# Authenticated without Security Hub: sources, health, sync
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_account_without_security_hub_is_healthy_when_ec2_is_readable():
    connector = make_connector()

    with use_boto3(FakeBoto3(make_clients())):
        assert await connector.authenticate() is True
        health = await connector.health_check()

    assert connector._authenticated is True
    assert connector.account_id == ACCOUNT
    assert connector.sources == {
        "security_hub": "not_enabled",
        "guardduty": "not_enabled",
        "ec2": "available",
        "iam": "available",
        "ssm": "access_denied",
    }
    assert health.status == "healthy"
    assert health.message == (
        f"Connected to AWS account {ACCOUNT}. Reading: EC2, IAM. "
        "Not enabled: Security Hub, GuardDuty. Missing permission: SSM."
    )
    assert connector.last_error is None


@pytest.mark.asyncio
async def test_sync_without_security_hub_returns_inventory_and_iam_events():
    connector = make_connector()

    with use_boto3(FakeBoto3(make_clients())):
        result = await connector.safe_sync()

    assert result.success is True
    assert [e.event_type for e in result.events] == [
        "aws.inventory.snapshot",
        "aws.iam.credential_report",
    ]
    assert result.events_ingested == 2

    inventory, iam = result.events
    assert inventory.source_system == "aws"
    resources = {r["kind"]: r for r in inventory.payload["resources"]}
    assert resources["ec2_instance"]["instance_id"] == "i-0abc123def4567890"
    assert resources["ec2_instance"]["name"] == "front-desk-server"
    assert resources["ec2_instance"]["private_ip"] == "10.0.1.15"
    assert resources["rds_instance"]["identifier"] == "patients-db"
    assert resources["rds_instance"]["engine"] == "postgres"
    assert inventory.payload["account_id"] == ACCOUNT
    json.dumps(inventory.payload)  # must be storable as JSON

    users = {u["user_name"]: u for u in iam.payload["iam_users"]}
    assert set(users) == {"<root_account>", "front-desk", "old-contractor"}
    front_desk = users["front-desk"]
    assert front_desk["user_id"] == f"arn:aws:iam::{ACCOUNT}:user/front-desk"
    assert front_desk["display_name"] == "front-desk"
    assert front_desk["mfa_enforced"] is False
    assert front_desk["account_enabled"] is True
    assert front_desk["password_enabled"] is True
    assert front_desk["password_last_used"] is None
    # No console sign-in on record, so the last access-key use stands in.
    assert front_desk["last_sign_in"] == "2026-10-30T00:00:00+00:00"
    assert front_desk["access_key_1_active"] is True
    assert front_desk["access_key_1_last_rotated"] == "2026-01-05T00:00:00+00:00"
    assert users["<root_account>"]["mfa_enforced"] is True
    assert users["<root_account>"]["last_sign_in"] == "2026-11-01T10:00:00+00:00"
    # Neither a password nor a live key: cannot sign in, and no date is invented.
    assert users["old-contractor"]["account_enabled"] is False
    assert users["old-contractor"]["last_sign_in"] is None
    assert_no_secrets(inventory.payload, iam.payload)


@pytest.mark.asyncio
async def test_nothing_readable_is_degraded_and_says_what_to_enable():
    clients = make_clients(security_hub="not_subscribed", ec2=False, iam=False, ssm="denied")
    connector = make_connector()

    with use_boto3(FakeBoto3(clients)):
        health = await connector.health_check()
        result = await connector.safe_sync()

    assert connector._authenticated is True
    assert health.status == "degraded"
    assert health.message.startswith(f"Connected to AWS account {ACCOUNT}, but nothing can be read yet.")
    assert "Not enabled: Security Hub, GuardDuty." in health.message
    assert "Missing permission: EC2, IAM, SSM." in health.message
    assert "SecurityAudit" in health.message
    assert connector.last_error_code == "NO_DATA_SOURCES"
    # Signed in fine and found nothing to read: an empty sync, not a failed one.
    assert result.success is True
    assert result.events == []


@pytest.mark.asyncio
async def test_security_hub_findings_come_first_and_other_sources_still_sync():
    finding = {
        "Id": "arn:aws:securityhub:us-east-1:123456789012:finding/abc",
        "Title": "S3 bucket allows public read",
        "Severity": {"Label": "HIGH", "Normalized": 70},
        "Resources": [{"Id": "arn:aws:s3:::clinic-records"}],
    }
    clients = make_clients(security_hub="enabled", guardduty_detectors=["d-1"], ssm="ok", findings=[finding])
    connector = make_connector()

    with use_boto3(FakeBoto3(clients)):
        result = await connector.safe_sync()
        health = await connector.health_check()

    assert [e.event_type for e in result.events] == [
        "aws.securityhub.finding",
        "aws.inventory.snapshot",
        "aws.iam.credential_report",
    ]
    assert result.events[0].severity == "high"
    assert result.events[0].payload["title"] == "S3 bucket allows public read"
    assert health.message == (
        f"Connected to AWS account {ACCOUNT}. Reading: Security Hub, GuardDuty, EC2, IAM, SSM."
    )


@pytest.mark.asyncio
async def test_one_failing_source_does_not_abort_the_others():
    clients = make_clients(security_hub="enabled", findings=[{"Id": "finding-1"}])
    clients["securityhub"].get_paginator.return_value.paginate.side_effect = aws_error(
        "AccessDeniedException", "GetFindings"
    )
    clients["iam"].get_credential_report.side_effect = aws_error("AccessDenied", "GetCredentialReport")
    connector = make_connector()

    with use_boto3(FakeBoto3(clients)):
        result = await connector.safe_sync()

    assert result.success is True
    assert [e.event_type for e in result.events] == ["aws.inventory.snapshot"]
    # The probe passed but the real read was refused: say so.
    assert connector.sources["security_hub"] == "access_denied"
    assert connector.sources["iam"] == "access_denied"
    assert connector.sources["ec2"] == "available"


@pytest.mark.asyncio
async def test_validate_permissions_names_the_missing_iam_actions():
    clients = make_clients(security_hub="denied", ssm="denied")
    connector = make_connector()

    with use_boto3(FakeBoto3(clients)):
        result = await connector.validate_permissions()

    assert result.valid is False
    assert result.missing_permissions == [
        "securityhub:DescribeHub",
        "securityhub:GetFindings",
        "ssm:DescribeInstanceInformation",
    ]
    assert "ssm:DescribeInstanceInformation" in result.message


@pytest.mark.asyncio
async def test_validate_permissions_passes_when_nothing_is_denied():
    connector = make_connector()

    with use_boto3(FakeBoto3(make_clients(ssm="ok"))):
        result = await connector.validate_permissions()

    # Security Hub / GuardDuty being switched off is not a permission problem.
    assert result.valid is True
    assert result.missing_permissions == []


# ---------------------------------------------------------------------------
# ConnectorManager: persisted verdict and lifecycle status
# ---------------------------------------------------------------------------

@pytest.fixture
def org(db_session):
    organization = Organization(id="org-aws-diagnostics", name="Small Clinic", owner_uid="owner-1")
    db_session.add(organization)
    db_session.commit()
    return organization


def register_aws(db_session, org_id, credentials=None):
    mgr = ConnectorManager(db_session, org_id)
    connector = mgr.register_connector(
        connector_type="aws",
        display_name="Amazon Web Services (AWS)",
        auth_method="api_key",
        credentials=dict(credentials or KEY_CREDS),
        config={"aws_region": "us-east-1"},
    )
    assert connector.status == ConnectorStatus.pending_auth.value
    return mgr, connector


@pytest.mark.asyncio
async def test_manager_health_check_persists_last_check_and_activates(db_session, org):
    mgr, connector = register_aws(db_session, org.id)

    with use_boto3(FakeBoto3(make_clients())):
        health = await mgr.health_check(connector.id)

    db_session.expire_all()
    saved = mgr.get_connector(connector.id)
    assert health.status == "healthy"
    assert saved.status == ConnectorStatus.active.value
    assert saved.health_status == "healthy"
    last_check = saved.config["last_check"]
    assert last_check["status"] == "healthy"
    assert last_check["message"] == health.message
    assert last_check["code"] is None
    assert last_check["checked_at"]
    assert last_check["sources"]["ec2"] == "available"
    assert last_check["sources"]["security_hub"] == "not_enabled"
    # Form config is kept, the verdict survives secret scrubbing, no secret leaks.
    assert saved.config["aws_region"] == "us-east-1"
    assert scrub_secrets(saved.config)["last_check"] == last_check
    assert_no_secrets(saved.config)


@pytest.mark.asyncio
async def test_manager_health_check_with_bad_keys_sets_error_not_pending(db_session, org):
    mgr, connector = register_aws(db_session, org.id)

    with use_boto3(FakeBoto3(make_clients(identity_error=aws_error("InvalidClientTokenId")))):
        health = await mgr.health_check(connector.id)

    db_session.expire_all()
    saved = mgr.get_connector(connector.id)
    assert health.status == "unreachable"
    assert saved.status == ConnectorStatus.error.value
    assert saved.health_status == "unreachable"
    assert saved.config["last_check"]["status"] == "unreachable"
    assert saved.config["last_check"]["code"] == "INVALID_KEYS"
    assert saved.config["last_check"]["message"] == INVALID_KEYS_MESSAGE
    assert saved.error_message == INVALID_KEYS_MESSAGE
    assert_no_secrets(saved.config, saved.error_message)


@pytest.mark.asyncio
async def test_manager_degraded_without_data_is_error_with_data_is_active(db_session, org):
    mgr, connector = register_aws(db_session, org.id)
    nothing_readable = make_clients(ec2=False, iam=False)

    with use_boto3(FakeBoto3(nothing_readable)):
        health = await mgr.health_check(connector.id)
    db_session.expire_all()
    saved = mgr.get_connector(connector.id)
    assert health.status == "degraded"
    assert saved.status == ConnectorStatus.error.value
    assert saved.config["last_check"]["code"] == "NO_DATA_SOURCES"

    # Evidence already ingested from this connector keeps it active while degraded.
    db_session.add(TelemetryEvent(
        org_id=org.id,
        connector_id=connector.id,
        event_type="aws.inventory.snapshot",
        source_system="aws",
        source_event_id="earlier-snapshot",
        payload_hash="0" * 64,
        payload="{}",
    ))
    db_session.commit()
    with use_boto3(FakeBoto3(nothing_readable)):
        await mgr.health_check(connector.id)
    db_session.expire_all()
    assert mgr.get_connector(connector.id).status == ConnectorStatus.active.value


@pytest.mark.asyncio
async def test_manager_sync_persists_last_check_and_ingests_events(db_session, org):
    mgr, connector = register_aws(db_session, org.id)

    with use_boto3(FakeBoto3(make_clients())):
        result = await mgr.sync_connector(connector.id)

    db_session.expire_all()
    saved = mgr.get_connector(connector.id)
    assert result.success is True
    assert result.events_ingested == 2
    assert saved.status == ConnectorStatus.active.value
    last_check = saved.config["last_check"]
    assert last_check["status"] == "healthy"
    assert last_check["message"].startswith(f"Connected to AWS account {ACCOUNT}. Reading: EC2, IAM.")
    assert last_check["message"].endswith("Synced 2 records.")
    stored = {
        row.event_type
        for row in db_session.query(TelemetryEvent).filter(TelemetryEvent.connector_id == connector.id)
    }
    assert stored == {"aws.inventory.snapshot", "aws.iam.credential_report"}


@pytest.mark.asyncio
async def test_manager_sync_with_bad_keys_reports_the_cause(db_session, org):
    mgr, connector = register_aws(db_session, org.id)

    with use_boto3(FakeBoto3(make_clients(identity_error=aws_error("InvalidClientTokenId")))):
        result = await mgr.sync_connector(connector.id)

    db_session.expire_all()
    saved = mgr.get_connector(connector.id)
    assert result.success is False
    assert result.error_details == INVALID_KEYS_MESSAGE
    assert saved.status == ConnectorStatus.error.value
    assert saved.config["last_check"]["code"] == "INVALID_KEYS"
    assert saved.config["last_check"]["status"] == "unreachable"


@pytest.mark.asyncio
async def test_updating_with_blank_secret_keeps_the_saved_one(db_session, org):
    mgr, connector = register_aws(db_session, org.id)
    with use_boto3(FakeBoto3(make_clients())):
        await mgr.health_check(connector.id)

    # The form sends only what was re-entered: region changed, secret left blank.
    mgr.update_connector(
        connector.id,
        credentials={"aws_region": "eu-west-1", "role_arn": ""},
        config={"aws_region": "eu-west-1"},
    )

    db_session.expire_all()
    saved = mgr.get_connector(connector.id)
    stored = mgr._decrypt_credentials(saved.encrypted_credentials)
    assert stored["aws_secret_access_key"] == SECRET_KEY
    assert stored["aws_access_key_id"] == ACCESS_KEY
    assert stored["aws_region"] == "eu-west-1"
    # New credentials make the old verdict stale.
    assert saved.status == ConnectorStatus.pending_auth.value
    assert "last_check" not in saved.config


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def test_health_endpoint_returns_the_plain_english_message(client_with_org, db_session):
    _, connector = register_aws(db_session, "test-org-123")

    with use_boto3(FakeBoto3(make_clients(identity_error=aws_error("InvalidClientTokenId")))):
        response = client_with_org.get(f"/api/v1/connectors/{connector.id}/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unreachable"
    assert body["message"] == INVALID_KEYS_MESSAGE
    assert_no_secrets(response.text)

    with use_boto3(FakeBoto3(make_clients())):
        response = client_with_org.get(f"/api/v1/connectors/{connector.id}/health")

    body = response.json()
    assert body["status"] == "healthy"
    assert body["message"].startswith(f"Connected to AWS account {ACCOUNT}. Reading: EC2, IAM.")

    listed = client_with_org.get("/api/v1/connectors").json()["connectors"][0]
    assert listed["status"] == "active"
    assert listed["config"]["last_check"]["message"] == body["message"]
    assert_no_secrets(listed)
