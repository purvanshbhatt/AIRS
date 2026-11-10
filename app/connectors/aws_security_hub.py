"""
AWS Connector — Cloud Security Posture Telemetry.

Proof of connection is ``sts:GetCallerIdentity``. Once AWS confirms who we
are, the connector is authenticated, whatever the account has switched on.
Each data source is then probed on its own and reported separately:

  - Security Hub  -> findings (``aws.securityhub.finding``)
  - EC2 / RDS     -> one ``aws.inventory.snapshot`` event
  - VPC / VPN     -> one ``aws.network.snapshot`` event (networks, subnets,
                     gateways, VPN tunnels, security groups, peerings)
  - IAM           -> one ``aws.iam.credential_report`` event
  - GuardDuty/SSM -> availability only (their output arrives through
                     Security Hub and the EC2 inventory respectively)

An account without Security Hub is a normal small-business account, not an
authentication failure. Failures are explained in plain English through
``last_error`` / ``last_error_code``; raw exception text and credentials
never leave this module.

Gracefully handles environments without boto3 installed.
"""
from __future__ import annotations

import asyncio
import csv
import io
import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.connectors.base import (
    Connector,
    ConnectorHealth,
    RawEvent,
    PermissionResult,
)
from app.services.clinic_engine.v2.schema import ConnectorCapability
from app.connectors.registry import register_connector

try:  # botocore ships with boto3; both are optional at import time
    from botocore.config import Config as _BotoConfig
except Exception:  # pragma: no cover - exercised only without boto3 installed
    _BotoConfig = None

logger = logging.getLogger("airs.connectors.aws_security_hub")


# ---------------------------------------------------------------------------
# Error codes (stable, machine-readable) and their user-facing messages
# ---------------------------------------------------------------------------

CODE_INVALID_KEYS = "INVALID_KEYS"
CODE_EXPIRED_TOKEN = "EXPIRED_TOKEN"
CODE_ROLE_NOT_ASSUMABLE = "ROLE_NOT_ASSUMABLE"
CODE_NO_PLATFORM_IDENTITY = "NO_PLATFORM_IDENTITY"
CODE_PLATFORM_IDENTITY_INVALID = "PLATFORM_IDENTITY_INVALID"
CODE_MISSING_CREDENTIALS = "MISSING_CREDENTIALS"
CODE_INVALID_ROLE_ARN = "INVALID_ROLE_ARN"
CODE_NETWORK = "NETWORK"
CODE_UNAVAILABLE = "UNAVAILABLE"
CODE_UNKNOWN = "UNKNOWN"
CODE_NO_DATA_SOURCES = "NO_DATA_SOURCES"

_MESSAGES = {
    CODE_INVALID_KEYS: "AWS rejected the access key or secret. Check for typos or a deactivated key.",
    CODE_EXPIRED_TOKEN: (
        "The temporary AWS credentials have expired. Paste a fresh access key, "
        "secret and session token."
    ),
    CODE_ROLE_NOT_ASSUMABLE: "AWS refused the role. Check the role's trust policy and External ID.",
    CODE_NO_PLATFORM_IDENTITY: (
        "Role-based access is not available on this workspace yet. Create a read-only "
        "IAM user (SecurityAudit policy) and paste its access key instead."
    ),
    CODE_PLATFORM_IDENTITY_INVALID: (
        "This workspace's own AWS identity is misconfigured, so the role could not be "
        "used. Contact support, or paste a read-only IAM user access key instead."
    ),
    CODE_MISSING_CREDENTIALS: "Enter an AWS access key ID and secret access key.",
    CODE_INVALID_ROLE_ARN: (
        "That role ARN is not valid. It should look like "
        "arn:aws:iam::123456789012:role/RoleName."
    ),
    CODE_NETWORK: "Could not reach AWS. Check the region name and try again in a minute.",
    CODE_UNAVAILABLE: "AWS support is not installed on this server.",
}

_INVALID_KEY_CODES = {
    "InvalidClientTokenId",
    "SignatureDoesNotMatch",
    "AuthFailure",
    "UnrecognizedClientException",
    "IncompleteSignature",
}
_EXPIRED_CODES = {"ExpiredToken", "ExpiredTokenException", "RequestExpired"}
_ACCESS_DENIED_CODES = {
    "AccessDenied",
    "AccessDeniedException",
    "UnauthorizedOperation",
    "UnauthorizedException",
    "AuthorizationError",
}
# Returned when a service has never been switched on for the account/region.
_NOT_ENABLED_CODES = {
    "InvalidAccessException",       # Security Hub: account is not subscribed
    "ResourceNotFoundException",
    "SubscriptionRequiredException",
    "OptInRequired",
}

_ROLE_ARN_RE = re.compile(r"^arn:aws[a-z-]*:iam::\d{12}:role/.+$")
_SAFE_CODE_RE = re.compile(r"^[A-Za-z0-9.]{1,64}$")
_ACCOUNT_ID_RE = re.compile(r"^\d{12}$")

# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------

SOURCE_AVAILABLE = "available"
SOURCE_NOT_ENABLED = "not_enabled"
SOURCE_ACCESS_DENIED = "access_denied"
SOURCE_ERROR = "error"

# Probe order is also the order sources are listed to the user.
SOURCE_LABELS: Dict[str, str] = {
    "security_hub": "Security Hub",
    "guardduty": "GuardDuty",
    "ec2": "EC2",
    "iam": "IAM",
    "ssm": "SSM",
}

# IAM actions each source needs (all are in the AWS-managed SecurityAudit policy).
SOURCE_ACTIONS: Dict[str, List[str]] = {
    "security_hub": ["securityhub:DescribeHub", "securityhub:GetFindings"],
    "guardduty": ["guardduty:ListDetectors"],
    "ec2": ["ec2:DescribeInstances"],
    "iam": [
        "iam:GetAccountSummary",
        "iam:GenerateCredentialReport",
        "iam:GetCredentialReport",
    ],
    "ssm": ["ssm:DescribeInstanceInformation"],
}

_MAX_INVENTORY_RESOURCES = 200
_MAX_IAM_USERS = 500
_CREDENTIAL_REPORT_POLLS = 6
_CREDENTIAL_REPORT_POLL_SECONDS = 2
_REPORT_EMPTY_VALUES = {"", "N/A", "no_information", "not_supported"}


class _AuthError(Exception):
    """Authentication failed for a reason we can explain to the user."""

    def __init__(self, code: str, message: Optional[str] = None):
        super().__init__(code)
        self.code = code
        self.message = message or _MESSAGES[code]


def _platform_identity() -> Optional[Tuple[str, str]]:
    """Access key pair of the ResilAI-owned IAM principal, when configured.

    This is the identity customer roles trust. Cloud Run has no AWS
    principal of its own, so without it a role ARN cannot be assumed.
    """
    try:
        from app.core.config import get_settings

        settings = get_settings()
        key = getattr(settings, "RESILAI_AWS_ACCESS_KEY_ID", None)
        secret = getattr(settings, "RESILAI_AWS_SECRET_ACCESS_KEY", None)
    except Exception:  # settings unavailable: behave as "not configured"
        return None
    if key and secret:
        return str(key), str(secret)
    return None


def _error_code(exc: BaseException) -> Optional[str]:
    """AWS error code from a botocore ClientError (duck-typed), else None."""
    response = getattr(exc, "response", None)
    if isinstance(response, dict):
        code = (response.get("Error") or {}).get("Code")
        return str(code) if code else None
    return None


def _is_network_error(exc: BaseException) -> bool:
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return True
    try:
        from botocore import exceptions as bex

        network_types = tuple(
            t for t in (
                getattr(bex, "EndpointConnectionError", None),
                getattr(bex, "ConnectionError", None),
                getattr(bex, "HTTPClientError", None),
                getattr(bex, "InvalidRegionError", None),
                getattr(bex, "NoRegionError", None),
            ) if isinstance(t, type)
        )
        if network_types and isinstance(exc, network_types):
            return True
    except Exception:
        pass
    name = type(exc).__name__
    return any(marker in name for marker in ("EndpointConnection", "ConnectTimeout", "ReadTimeout"))


def _unknown_message(exc: BaseException) -> str:
    """Describe an unmapped failure by exception class (and AWS error code) only.

    Never includes the exception text: it can echo request details.
    """
    detail = type(exc).__name__
    code = _error_code(exc)
    if code and _SAFE_CODE_RE.match(code):
        detail = f"{detail}: {code}"
    return (
        f"AWS returned an unexpected error ({detail}). Try again, and contact "
        "support if it keeps happening."
    )


def _report_value(value: Any) -> Optional[str]:
    """Credential-report cell -> value, or None for AWS's 'no data' markers."""
    if value is None:
        return None
    text = str(value).strip()
    return None if text in _REPORT_EMPTY_VALUES else text


@register_connector
class AWSSecurityHubConnector(Connector):
    """AWS connector for cloud security posture telemetry.

    Credentials:
      - aws_access_key_id / aws_secret_access_key: IAM access key
        (recommended: a read-only IAM user with the SecurityAudit policy)
      - aws_session_token: optional, for temporary credentials
      - aws_region: AWS region (default us-east-1)
      - role_arn / external_id: optional IAM role to assume via STS. The
        base identity is the connector's own keys when supplied, otherwise
        the platform identity (RESILAI_AWS_ACCESS_KEY_ID / _SECRET_ACCESS_KEY).

    After ``authenticate()``:
      - ``account_id`` / ``caller_arn``: who AWS says we are
      - ``sources``: {name: available | not_enabled | access_denied | error}

    Gracefully degrades if boto3 is not installed.
    """

    CONNECTOR_TYPE = "aws_security_hub"
    REQUIRED_PERMISSIONS = [
        "sts:GetCallerIdentity",
        "securityhub:GetFindings",
        "securityhub:DescribeHub",
        "securityhub:GetEnabledStandards",
        "guardduty:ListDetectors",
        "ec2:DescribeInstances",
        "rds:DescribeDBInstances",
        "iam:GetAccountSummary",
        "iam:GenerateCredentialReport",
        "iam:GetCredentialReport",
        "ssm:DescribeInstanceInformation",
    ]
    CAPABILITIES = [ConnectorCapability.CLOUD_ASSETS]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = None
        self._hub_client = None
        self._client_config = None
        self._region = (
            str(self._credentials.get("aws_region") or self._config.get("aws_region") or "").strip()
            or "us-east-1"
        )
        self.account_id: Optional[str] = None
        self.caller_arn: Optional[str] = None
        self.sources: Dict[str, str] = {}

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def authenticate(self) -> bool:
        # boto3 is blocking; keep the event loop free while AWS answers.
        return await asyncio.to_thread(self._authenticate_blocking)

    def _authenticate_blocking(self) -> bool:
        self._authenticated = False
        self._session = None
        self._hub_client = None
        self.account_id = None
        self.caller_arn = None
        self.sources = {}
        self.last_error = None
        self.last_error_code = None

        try:
            import boto3
        except ImportError:
            self.logger.warning("boto3 not installed — AWS connector unavailable")
            self._set_error(CODE_UNAVAILABLE)
            return False

        try:
            self._client_config = self._build_client_config()
            self._session = self._build_session(boto3)
            identity = self._session.client("sts", **self._client_kwargs()).get_caller_identity()
        except _AuthError as err:
            self._session = None
            self._set_error(err.code, err.message)
            self.logger.warning("AWS authentication failed: code=%s", err.code)
            return False
        except Exception as exc:
            self._session = None
            code, message = self._classify_auth_failure(exc, stage="identity")
            self._set_error(code, message)
            self._log_failure("identity check", exc, code)
            return False

        account = identity.get("Account") if hasattr(identity, "get") else None
        arn = identity.get("Arn") if hasattr(identity, "get") else None
        self.account_id = account if isinstance(account, str) and _ACCOUNT_ID_RE.match(account) else None
        self.caller_arn = arn if isinstance(arn, str) else None

        # AWS has confirmed the identity: the connector is authenticated.
        # What the account lets us read is a separate question.
        self._authenticated = True
        self._probe_sources()
        self.logger.info(
            "AWS authentication successful: account=%s sources=%s",
            self.account_id, self.sources,
        )
        return True

    @staticmethod
    def _build_client_config():
        """Short timeouts so a bad region fails in seconds, not minutes."""
        if _BotoConfig is None:
            return None
        try:
            return _BotoConfig(
                connect_timeout=8,
                read_timeout=20,
                retries={"max_attempts": 2, "mode": "standard"},
            )
        except Exception:
            return None

    def _client_kwargs(self) -> Dict[str, Any]:
        return {"config": self._client_config} if self._client_config is not None else {}

    def _client(self, service: str):
        return self._session.client(service, **self._client_kwargs())

    def _build_session(self, boto3):
        """Session from access keys, or from an assumed role. Raises _AuthError."""
        creds = self._credentials
        access_key = str(creds.get("aws_access_key_id") or "").strip()
        secret_key = str(creds.get("aws_secret_access_key") or "").strip()
        session_token = str(creds.get("aws_session_token") or "").strip() or None
        role_arn = str(creds.get("role_arn") or "").strip() or None
        has_own_keys = bool(access_key and secret_key)

        if not role_arn:
            if not has_own_keys:
                # Never fall back to the server's ambient AWS identity: that
                # would show one tenant the platform's own account.
                raise _AuthError(CODE_MISSING_CREDENTIALS)
            session_kwargs: Dict[str, Any] = {
                "region_name": self._region,
                "aws_access_key_id": access_key,
                "aws_secret_access_key": secret_key,
            }
            if session_token:
                session_kwargs["aws_session_token"] = session_token
            return boto3.Session(**session_kwargs)

        # ---- Role assumption ------------------------------------------
        if not _ROLE_ARN_RE.match(role_arn):
            raise _AuthError(CODE_INVALID_ROLE_ARN)

        using_platform_identity = False
        if has_own_keys:
            base_key, base_secret, base_token = access_key, secret_key, session_token
        else:
            platform = _platform_identity()
            if not platform:
                raise _AuthError(CODE_NO_PLATFORM_IDENTITY)
            base_key, base_secret = platform
            base_token = None
            using_platform_identity = True

        sts_kwargs: Dict[str, Any] = {
            "region_name": self._region,
            "aws_access_key_id": base_key,
            "aws_secret_access_key": base_secret,
        }
        if base_token:
            sts_kwargs["aws_session_token"] = base_token
        sts_kwargs.update(self._client_kwargs())

        assume_params: Dict[str, Any] = {
            "RoleArn": role_arn,
            "RoleSessionName": f"resilai-connector-{self.connector_id[:8]}",
            "DurationSeconds": 3600,
        }
        external_id = creds.get("external_id") or self._config.get("external_id")
        if external_id:
            assume_params["ExternalId"] = external_id

        try:
            sts = boto3.client("sts", **sts_kwargs)
            assumed = sts.assume_role(**assume_params)
            temp = assumed["Credentials"]
        except Exception as exc:
            code, message = self._classify_auth_failure(exc, stage="assume_role")
            if using_platform_identity and code in (CODE_INVALID_KEYS, CODE_EXPIRED_TOKEN):
                # The customer supplied no keys: do not blame theirs.
                code, message = CODE_PLATFORM_IDENTITY_INVALID, _MESSAGES[CODE_PLATFORM_IDENTITY_INVALID]
            self._log_failure("assume role", exc, code)
            raise _AuthError(code, message) from None

        return boto3.Session(
            aws_access_key_id=temp["AccessKeyId"],
            aws_secret_access_key=temp["SecretAccessKey"],
            aws_session_token=temp["SessionToken"],
            region_name=self._region,
        )

    @staticmethod
    def _classify_auth_failure(exc: BaseException, stage: str) -> Tuple[str, str]:
        """Map a boto/botocore failure to (code, plain-English message)."""
        code = _error_code(exc)
        if code in _INVALID_KEY_CODES:
            return CODE_INVALID_KEYS, _MESSAGES[CODE_INVALID_KEYS]
        if code in _EXPIRED_CODES:
            return CODE_EXPIRED_TOKEN, _MESSAGES[CODE_EXPIRED_TOKEN]
        if stage == "assume_role" and code in _ACCESS_DENIED_CODES:
            return CODE_ROLE_NOT_ASSUMABLE, _MESSAGES[CODE_ROLE_NOT_ASSUMABLE]
        if stage == "assume_role" and (
            code == "ValidationError" or type(exc).__name__ == "ParamValidationError"
        ):
            return CODE_INVALID_ROLE_ARN, _MESSAGES[CODE_INVALID_ROLE_ARN]
        if _is_network_error(exc):
            return CODE_NETWORK, _MESSAGES[CODE_NETWORK]
        return CODE_UNKNOWN, _unknown_message(exc)

    def _set_error(self, code: str, message: Optional[str] = None) -> None:
        self.last_error_code = code
        self.last_error = message or _MESSAGES.get(code) or "AWS could not be reached."

    def _log_failure(self, what: str, exc: BaseException, code: str) -> None:
        # Class name and AWS error code only: exception text stays out of logs.
        self.logger.error(
            "AWS %s failed: code=%s exception=%s aws_error=%s",
            what, code, type(exc).__name__, _error_code(exc),
        )

    # ------------------------------------------------------------------
    # Data-source probes
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_source_failure(exc: BaseException) -> str:
        code = _error_code(exc)
        if code in _ACCESS_DENIED_CODES:
            return SOURCE_ACCESS_DENIED
        if code in _NOT_ENABLED_CODES:
            return SOURCE_NOT_ENABLED
        return SOURCE_ERROR

    def _probe(self, name: str, call, interpret=None) -> str:
        """Run one read-only call; ``interpret`` may turn its response into a state."""
        try:
            response = call()
            state = interpret(response) if interpret else SOURCE_AVAILABLE
        except Exception as exc:
            state = self._classify_source_failure(exc)
            self.logger.info(
                "AWS source %s is %s (exception=%s aws_error=%s)",
                name, state, type(exc).__name__, _error_code(exc),
            )
        self.sources[name] = state
        return state

    def _probe_security_hub(self) -> None:
        """Probe Security Hub on the current client; keep the client only if usable."""
        hub = self._hub_client
        if hub is None:
            hub = self._client("securityhub")

        state = self._probe("security_hub", hub.describe_hub)
        if self._session is not None:
            self._hub_client = hub if state == SOURCE_AVAILABLE else None

    def _probe_sources(self) -> None:
        """Find out what this identity can read. Never fails authentication."""
        self.sources = {}
        self._probe_security_hub()

        def has_detector(response) -> str:
            # GuardDuty answers with an empty list when it was never enabled.
            detectors = response.get("DetectorIds") if hasattr(response, "get") else None
            return SOURCE_AVAILABLE if detectors else SOURCE_NOT_ENABLED

        self._probe("guardduty", lambda: self._client("guardduty").list_detectors(), has_detector)
        self._probe("ec2", lambda: self._client("ec2").describe_instances(MaxResults=5))
        self._probe("iam", lambda: self._client("iam").get_account_summary())
        self._probe("ssm", lambda: self._client("ssm").describe_instance_information(MaxResults=5))

    def _sources_in(self, state: str) -> List[str]:
        return [
            SOURCE_LABELS.get(name, name)
            for name in list(SOURCE_LABELS) + [n for n in self.sources if n not in SOURCE_LABELS]
            if self.sources.get(name) == state
        ]

    def status_summary(self) -> str:
        """One plain-English line: who we are connected as and what is readable."""
        available = self._sources_in(SOURCE_AVAILABLE)
        if self.account_id:
            head = f"Connected to AWS account {self.account_id}"
        elif self._authenticated or available:
            head = "Connected to AWS"
        else:
            head = "AWS could not be verified"

        parts: List[str] = []
        if available:
            parts.append(f"Reading: {', '.join(available)}.")
        not_enabled = self._sources_in(SOURCE_NOT_ENABLED)
        if not_enabled:
            parts.append(f"Not enabled: {', '.join(not_enabled)}.")
        denied = self._sources_in(SOURCE_ACCESS_DENIED)
        if denied:
            parts.append(f"Missing permission: {', '.join(denied)}.")
        errored = self._sources_in(SOURCE_ERROR)
        if errored:
            parts.append(f"Could not check: {', '.join(errored)}.")

        if available or not (self.account_id or self._authenticated):
            return " ".join([f"{head}."] + parts)

        advice = (
            "Attach the AWS-managed SecurityAudit policy to this user or role"
            + (f", or enable Security Hub in {self._region}." if not_enabled else ".")
        )
        return " ".join([f"{head}, but nothing can be read yet."] + parts + [advice])

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    async def sync(self) -> List[RawEvent]:
        if self._session is None and self._hub_client is None:
            self.logger.error("AWS connector not authenticated - authenticate first")
            return []
        return await asyncio.to_thread(self._collect_events)

    def _collect_events(self) -> List[RawEvent]:
        """Collect from every readable source; one failing source never aborts the rest."""
        events: List[RawEvent] = []

        # Findings go first: downstream uses the first event's source system
        # to pick the evidence adapter.
        if self._hub_client is not None:
            events.extend(self._collect_findings())

        if self._session is not None:
            for collect in (
                self._collect_inventory_event,
                self._collect_network_event,
                self._collect_iam_event,
            ):
                try:
                    event = collect()
                except Exception as exc:  # defensive: collectors guard themselves
                    self.logger.warning(
                        "AWS %s failed: %s", collect.__name__, type(exc).__name__
                    )
                    event = None
                if event is not None:
                    events.append(event)

        self.logger.info("AWS sync: %d events (sources=%s)", len(events), self.sources)
        return events

    def _collect_findings(self) -> List[RawEvent]:
        events: List[RawEvent] = []
        try:
            filters = {
                "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}],
                "WorkflowStatus": [{"Value": "NEW", "Comparison": "EQUALS"}],
            }

            paginator = self._hub_client.get_paginator("get_findings")
            for page in paginator.paginate(
                Filters=filters, MaxResults=100
            ):
                for finding in page.get("Findings", []):
                    events.append(self._normalize_finding(finding))

        except Exception as exc:
            self._note_source_failure("security_hub", exc)
            self.logger.error(
                "AWS Security Hub sync error: exception=%s aws_error=%s",
                type(exc).__name__, _error_code(exc),
            )
        return events

    def _note_source_failure(self, name: str, exc: BaseException) -> None:
        """Downgrade a source that the probe passed but the real read was denied."""
        state = self._classify_source_failure(exc)
        if state in (SOURCE_ACCESS_DENIED, SOURCE_NOT_ENABLED) and name in self.sources:
            self.sources[name] = state

    def _collect_inventory_event(self) -> Optional[RawEvent]:
        """EC2 + RDS resources as one ``aws.inventory.snapshot`` event."""
        # Runs even when the EC2 probe was denied: RDS may still be readable,
        # and the discovery service records each denied API on its own.
        try:
            from app.services.discovery.aws_discovery import AWSDiscoveryService
            from app.services.discovery.discovery import SourceDiscoveryResult

            service = AWSDiscoveryService(db=None, org_id=self.org_id, is_demo=False)
            result = SourceDiscoveryResult(source="aws")
            raw_resources = service.fetch_aws_resources(self._session, result)
        except Exception as exc:
            self._note_source_failure("ec2", exc)
            self.logger.warning(
                "AWS inventory failed: exception=%s aws_error=%s",
                type(exc).__name__, _error_code(exc),
            )
            return None

        resources = [self._inventory_resource(r) for r in raw_resources if isinstance(r, dict)]
        if not resources:
            return None

        now = datetime.now(timezone.utc)
        payload = {
            "resources": resources[:_MAX_INVENTORY_RESOURCES],
            "resource_count": len(resources),
            "truncated": len(resources) > _MAX_INVENTORY_RESOURCES,
            "account_id": self.account_id,
            "region": self._region,
            "denied_apis": list(result.denied_apis),
        }
        return RawEvent(
            event_type="aws.inventory.snapshot",
            source_system="aws",
            source_event_id=(
                f"aws-inventory-{self.account_id or 'account'}-{self._region}-"
                f"{now.strftime('%Y%m%d%H')}"
            ),
            payload=json.loads(json.dumps(payload, default=str)),
            timestamp=now.isoformat(),
        )

    def _collect_network_event(self) -> Optional[RawEvent]:
        """VPCs, subnets, gateways, VPNs and security groups as one ``aws.network.snapshot`` event.

        Uses the session built from this connector's own credentials. Each
        EC2 API is read on its own, so a missing permission only leaves that
        part of the map out. Returns None when the account shows no network
        and no VPN (nothing to draw).
        """
        try:
            from app.services.discovery.aws_network import collect_aws_network

            snapshot = collect_aws_network(self._session, self._region, self._client_kwargs())
        except Exception as exc:  # defensive: the collector guards each call itself
            self.logger.warning(
                "AWS network snapshot failed: exception=%s aws_error=%s",
                type(exc).__name__, _error_code(exc),
            )
            return None

        if not snapshot.get("networks") and not snapshot.get("vpns"):
            return None

        now = datetime.now(timezone.utc)
        snapshot["account_id"] = self.account_id
        snapshot["region"] = self._region
        return RawEvent(
            event_type="aws.network.snapshot",
            source_system="aws",
            source_event_id=(
                f"aws-network-{self.account_id or 'account'}-{self._region}-"
                f"{now.strftime('%Y%m%d%H')}"
            ),
            payload=json.loads(json.dumps(snapshot, default=str)),
            timestamp=now.isoformat(),
        )

    @staticmethod
    def _inventory_resource(res: Dict[str, Any]) -> Dict[str, Any]:
        """Discovery resource -> the inventory shape the network map reads."""
        source = str(res.get("source") or "")
        raw = res.get("raw") if isinstance(res.get("raw"), dict) else {}
        software = res.get("software") if isinstance(res.get("software"), list) else []
        security_groups = res.get("security_group_ids")
        security_group_ids = [str(g) for g in security_groups if g] if isinstance(security_groups, list) else []
        if source.startswith("rds:"):
            engine = software[0] if software and isinstance(software[0], dict) else {}
            return {
                "kind": "rds_instance",
                "identifier": res.get("external_id"),
                "name": res.get("name"),
                "engine": engine.get("name"),
                "engine_version": engine.get("version"),
                "instance_type": res.get("instance_type"),
                "state": res.get("state"),
                "endpoint": res.get("ip"),
                "public_ip": res.get("public_ip"),
                "publicly_accessible": raw.get("PubliclyAccessible"),
                "storage_encrypted": raw.get("StorageEncrypted"),
                "multi_az": raw.get("MultiAZ"),
                "vpc_id": res.get("vpc_id"),
                "security_group_ids": security_group_ids,
                "source": source,
            }
        return {
            "kind": "ec2_instance",
            "instance_id": res.get("external_id"),
            "name": res.get("name"),
            "instance_type": res.get("instance_type"),
            "platform": res.get("os"),
            "state": res.get("state"),
            "launch_time": res.get("launch_time"),
            "private_ip": res.get("ip"),
            "public_ip": res.get("public_ip"),
            "vpc_id": res.get("vpc_id"),
            "subnet_id": res.get("subnet_id"),
            "security_group_ids": security_group_ids,
            "availability_zone": res.get("availability_zone"),
            "software_count": len(software),
            "source": source,
        }

    def _collect_iam_event(self) -> Optional[RawEvent]:
        """IAM credential report as one ``aws.iam.credential_report`` event."""
        if self.sources.get("iam") != SOURCE_AVAILABLE:
            return None
        try:
            iam = self._client("iam")
            for attempt in range(_CREDENTIAL_REPORT_POLLS):
                state = iam.generate_credential_report().get("State")
                if state not in ("STARTED", "INPROGRESS"):
                    break  # COMPLETE (or an unexpected value: let the read decide)
                if attempt < _CREDENTIAL_REPORT_POLLS - 1:
                    time.sleep(_CREDENTIAL_REPORT_POLL_SECONDS)
            content = iam.get_credential_report()["Content"]
            if isinstance(content, (bytes, bytearray)):
                content = bytes(content).decode("utf-8")
            rows = list(csv.DictReader(io.StringIO(content)))
        except Exception as exc:
            self._note_source_failure("iam", exc)
            self.logger.warning(
                "AWS IAM credential report failed: exception=%s aws_error=%s",
                type(exc).__name__, _error_code(exc),
            )
            return None

        iam_users = [self._iam_user(row) for row in rows if row.get("user")]
        if not iam_users:
            return None

        now = datetime.now(timezone.utc)
        return RawEvent(
            event_type="aws.iam.credential_report",
            source_system="aws",
            source_event_id=(
                f"aws-iam-report-{self.account_id or 'account'}-{now.strftime('%Y%m%d%H')}"
            ),
            payload={
                "iam_users": iam_users[:_MAX_IAM_USERS],
                "user_count": len(iam_users),
                "account_id": self.account_id,
            },
            timestamp=now.isoformat(),
        )

    @staticmethod
    def _iam_user(row: Dict[str, Any]) -> Dict[str, Any]:
        """Credential-report row -> the iam_users entry consumers expect.

        Only reports what AWS reported: a missing sign-in date stays None.
        """
        name = str(row.get("user") or "").strip()
        is_root = name == "<root_account>"
        mfa_active = row.get("mfa_active") == "true"
        password_enabled = row.get("password_enabled") == "true"
        password_last_used = _report_value(row.get("password_last_used"))
        key_1_active = row.get("access_key_1_active") == "true"
        key_2_active = row.get("access_key_2_active") == "true"
        key_last_used = max(
            (
                v for v in (
                    _report_value(row.get("access_key_1_last_used_date")),
                    _report_value(row.get("access_key_2_last_used_date")),
                ) if v
            ),
            default=None,
        )
        return {
            "user_id": _report_value(row.get("arn")) or f"iam-{name}",
            "user_name": name,
            "display_name": "AWS root account" if is_root else name,
            "mfa_enforced": mfa_active,
            # Able to sign in at all: console password or a live access key.
            "account_enabled": bool(is_root or password_enabled or key_1_active or key_2_active),
            "last_sign_in": password_last_used or key_last_used,
            "mfa_active": mfa_active,
            "password_enabled": password_enabled,
            "password_last_used": password_last_used,
            "access_key_active": key_1_active,
            "access_key_last_rotated": _report_value(row.get("access_key_1_last_rotated")),
            "access_key_1_active": key_1_active,
            "access_key_1_last_rotated": _report_value(row.get("access_key_1_last_rotated")),
        }

    def _normalize_finding(self, finding: Dict[str, Any]) -> RawEvent:
        """Convert an AWS Security Hub finding to a RawEvent."""
        finding_id = finding.get("Id", str(uuid.uuid4()))
        severity = finding.get("Severity", {})
        severity_label = severity.get("Label", "MEDIUM").lower()

        # Extract key metadata
        resources = finding.get("Resources", [])
        resource_ids = [r.get("Id", "") for r in resources]

        return RawEvent(
            event_type="aws.securityhub.finding",
            source_system="aws_security_hub",
            source_event_id=finding_id,
            severity=self._map_severity(severity_label),
            payload={
                "title": finding.get("Title", ""),
                "description": finding.get("Description", ""),
                "product_name": finding.get("ProductName", ""),
                "company_name": finding.get("CompanyName", ""),
                "compliance_status": finding.get("Compliance", {}).get("Status", ""),
                "record_state": finding.get("RecordState", ""),
                "workflow_status": finding.get("Workflow", {}).get("Status", ""),
                "severity_label": severity_label,
                "severity_normalized": severity.get("Normalized", 0),
                "resources": resource_ids,
                "generator_id": finding.get("GeneratorId", ""),
                "created_at": finding.get("CreatedAt", ""),
                "updated_at": finding.get("UpdatedAt", ""),
            },
        )

    # ------------------------------------------------------------------
    # Health Check
    # ------------------------------------------------------------------

    async def _refresh(self) -> bool:
        """Re-verify identity and re-probe sources. False when AWS rejects us.

        A caller that handed us a ready Security Hub client (no session) is
        probed on that client alone.
        """
        if self._session is None and self._hub_client is not None:
            await asyncio.to_thread(self._probe_security_hub)
            return True
        return await self.authenticate()

    async def health_check(self) -> ConnectorHealth:
        start = time.monotonic()
        try:
            ok = await self._refresh()
        except Exception as exc:  # never let a health probe raise
            self._set_error(CODE_UNKNOWN, _unknown_message(exc))
            ok = False
        latency = int((time.monotonic() - start) * 1000)

        if not ok:
            return ConnectorHealth(
                status="unreachable",
                latency_ms=latency,
                message=self.last_error or "AWS could not be reached.",
            )

        summary = self.status_summary()
        if self._sources_in(SOURCE_AVAILABLE):
            return ConnectorHealth(status="healthy", latency_ms=latency, message=summary)

        self._set_error(CODE_NO_DATA_SOURCES, summary)
        # Identity proven but nothing readable is degraded; with no proven
        # identity either, there is nothing to stand on.
        return ConnectorHealth(
            status="degraded" if self._authenticated else "unreachable",
            latency_ms=latency,
            message=summary,
        )

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    async def validate_permissions(self) -> PermissionResult:
        try:
            ok = await self._refresh()
        except Exception as exc:
            self._set_error(CODE_UNKNOWN, _unknown_message(exc))
            ok = False
        if not ok:
            return PermissionResult(
                valid=False,
                message=self.last_error or "AWS could not be reached.",
            )

        missing: List[str] = []
        for name, actions in SOURCE_ACTIONS.items():
            if self.sources.get(name) == SOURCE_ACCESS_DENIED:
                missing.extend(actions)

        # DescribeHub passing does not prove findings are readable.
        if self._hub_client is not None and self.sources.get("security_hub") == SOURCE_AVAILABLE:
            try:
                await asyncio.to_thread(self._hub_client.get_findings, MaxResults=1)
            except Exception:
                missing.append("securityhub:GetFindings")

        if missing:
            return PermissionResult(
                valid=False,
                missing_permissions=missing,
                message=f"Missing: {', '.join(missing)}",
            )
        if not self._sources_in(SOURCE_AVAILABLE):
            return PermissionResult(valid=False, message=self.status_summary())
        return PermissionResult(valid=True, message="All required permissions verified")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_severity(aws_label: str) -> str:
        mapping = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "informational": "info",
        }
        return mapping.get(aws_label.lower(), "medium")
