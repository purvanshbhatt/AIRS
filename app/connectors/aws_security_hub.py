"""
AWS Security Hub Connector — Cloud Security Posture Telemetry.

Ingests findings from AWS Security Hub including compliance checks,
GuardDuty detections, Inspector results, and IAM Access Analyzer findings.

Gracefully handles environments without boto3 installed.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from app.connectors.base import (
    Connector,
    ConnectorHealth,
    RawEvent,
    PermissionResult,
)
from app.services.clinic_engine.v2.schema import ConnectorCapability
from app.connectors.registry import register_connector

logger = logging.getLogger("airs.connectors.aws_security_hub")


@register_connector
class AWSSecurityHubConnector(Connector):
    """AWS Security Hub connector for cloud security posture telemetry.

    Credentials:
      - aws_access_key_id: IAM access key
      - aws_secret_access_key: IAM secret key
      - aws_region: AWS region (default us-east-1)
      - role_arn: Optional IAM role to assume via STS

    Gracefully degrades if boto3 is not installed.
    """

    CONNECTOR_TYPE = "aws_security_hub"
    REQUIRED_PERMISSIONS = [
        "securityhub:GetFindings",
        "securityhub:DescribeHub",
        "securityhub:GetEnabledStandards",
    ]
    CAPABILITIES = [ConnectorCapability.CLOUD_ASSETS]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = None
        self._hub_client = None
        self._region = self._credentials.get("aws_region", "us-east-1")

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def authenticate(self) -> bool:
        try:
            import boto3
        except ImportError:
            self.logger.warning("boto3 not installed — AWS connector unavailable")
            return False

        try:
            access_key = self._credentials.get("aws_access_key_id", "")
            secret_key = self._credentials.get("aws_secret_access_key", "")
            role_arn = self._credentials.get("role_arn")

            if role_arn:
                # Assume role via STS
                sts = boto3.client(
                    "sts",
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=self._region,
                )
                assumed = sts.assume_role(
                    RoleArn=role_arn,
                    RoleSessionName=f"resilai-connector-{self.connector_id[:8]}",
                    DurationSeconds=3600,
                )
                creds = assumed["Credentials"]
                self._session = boto3.Session(
                    aws_access_key_id=creds["AccessKeyId"],
                    aws_secret_access_key=creds["SecretAccessKey"],
                    aws_session_token=creds["SessionToken"],
                    region_name=self._region,
                )
            else:
                self._session = boto3.Session(
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=self._region,
                )

            self._hub_client = self._session.client("securityhub")
            # Verify connectivity
            self._hub_client.describe_hub()
            self._authenticated = True
            self.logger.info("AWS Security Hub authentication successful")
            return True

        except Exception as exc:
            self.logger.error("AWS Security Hub auth error: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    async def sync(self) -> List[RawEvent]:
        if not self._hub_client:
            self.logger.error("Hub client not initialized - authenticate first")
            return []

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
            self.logger.error("AWS Security Hub sync error: %s", exc)

        self.logger.info("AWS Security Hub sync: %d events", len(events))
        return events

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

    async def health_check(self) -> ConnectorHealth:
        import time
        start = time.monotonic()
        try:
            if not self._hub_client:
                return ConnectorHealth(
                    status="unreachable",
                    message="Not authenticated",
                )
            self._hub_client.describe_hub()
            latency = int((time.monotonic() - start) * 1000)
            return ConnectorHealth(
                status="healthy",
                latency_ms=latency,
                message="Security Hub reachable",
            )
        except Exception as exc:
            latency = int((time.monotonic() - start) * 1000)
            return ConnectorHealth(
                status="unreachable",
                latency_ms=latency,
                message=str(exc),
            )

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    async def validate_permissions(self) -> PermissionResult:
        if not self._hub_client:
            return PermissionResult(valid=False, message="Not authenticated")

        missing = []
        try:
            self._hub_client.describe_hub()
        except Exception:
            missing.append("securityhub:DescribeHub")

        try:
            self._hub_client.get_findings(MaxResults=1)
        except Exception:
            missing.append("securityhub:GetFindings")

        if missing:
            return PermissionResult(
                valid=False,
                missing_permissions=missing,
                message=f"Missing: {', '.join(missing)}",
            )
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
