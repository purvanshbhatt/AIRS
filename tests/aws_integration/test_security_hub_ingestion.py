"""Tests for AWS Security Hub finding sync and normalization."""

import asyncio
import uuid
import pytest
from unittest.mock import patch, MagicMock

from app.connectors.aws_security_hub import AWSSecurityHubConnector


def _run(coro):
    """Run an async coroutine."""
    return asyncio.run(coro)


# Sample AWS Security Hub finding for testing
SAMPLE_FINDING = {
    "Id": "arn:aws:securityhub:us-east-1:123456789012:finding/test-001",
    "Title": "S3 Bucket does not have default encryption enabled",
    "Description": "This S3 bucket does not have default encryption enabled.",
    "ProductName": "Security Hub",
    "CompanyName": "AWS",
    "Severity": {"Label": "HIGH", "Normalized": 70},
    "Compliance": {"Status": "FAILED"},
    "RecordState": "ACTIVE",
    "Workflow": {"Status": "NEW"},
    "Resources": [
        {"Id": "arn:aws:s3:::resilai-test-bucket", "Type": "AwsS3Bucket"}
    ],
    "GeneratorId": "aws-foundational-security-best-practices/v/1.0.0/S3.4",
    "CreatedAt": "2026-09-13T10:00:00.000Z",
    "UpdatedAt": "2026-09-13T10:00:00.000Z",
}

SAMPLE_FINDING_LOW = {
    **SAMPLE_FINDING,
    "Id": "arn:aws:securityhub:us-east-1:123456789012:finding/test-002",
    "Severity": {"Label": "LOW", "Normalized": 10},
}


class TestSecurityHubIngestion:
    """Tests for AWS Security Hub finding sync and normalization."""

    def _make_connector(self, credentials):
        return AWSSecurityHubConnector(
            connector_id="test-conn",
            org_id="test-org",
            credentials=credentials,
        )

    def test_sync_returns_normalized_events(self, mock_aws_credentials):
        """Sync with sample findings returns properly normalized RawEvents."""
        connector = self._make_connector(mock_aws_credentials)
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {"Findings": [SAMPLE_FINDING]}
        ]
        mock_client.get_paginator.return_value = mock_paginator
        connector._hub_client = mock_client

        events = _run(connector.sync())
        assert len(events) == 1
        assert events[0].event_type == "aws.securityhub.finding"
        assert events[0].source_system == "aws_security_hub"
        assert events[0].source_event_id == SAMPLE_FINDING["Id"]
        assert events[0].severity == "high"

    def test_sync_empty_findings(self, mock_aws_credentials):
        """Sync with no findings returns empty list."""
        connector = self._make_connector(mock_aws_credentials)
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"Findings": []}]
        mock_client.get_paginator.return_value = mock_paginator
        connector._hub_client = mock_client

        events = _run(connector.sync())
        assert len(events) == 0

    def test_sync_not_authenticated(self):
        """When hub_client is None, sync returns empty list without error."""
        connector = AWSSecurityHubConnector(
            connector_id="test", org_id="test", credentials={}
        )
        events = _run(connector.sync())
        assert events == []

    def test_normalize_finding_severity_mapping(self):
        """All AWS severity labels map to expected ResilAI severity strings."""
        connector = self._make_connector({})
        assert connector._map_severity("critical") == "critical"
        assert connector._map_severity("high") == "high"
        assert connector._map_severity("medium") == "medium"
        assert connector._map_severity("low") == "low"
        assert connector._map_severity("informational") == "info"
        assert connector._map_severity("UNKNOWN") == "medium"  # default

    def test_normalize_finding_payload_fields(self):
        """Normalized finding contains all expected payload keys."""
        connector = self._make_connector({})
        event = connector._normalize_finding(SAMPLE_FINDING)
        expected_keys = {
            "title", "description", "product_name", "company_name",
            "compliance_status", "record_state", "workflow_status",
            "severity_label", "severity_normalized", "resources",
            "generator_id", "created_at", "updated_at",
        }
        assert set(event.payload.keys()) == expected_keys

    def test_normalize_finding_resource_extraction(self):
        """Resource ARNs are extracted from finding."""
        connector = self._make_connector({})
        event = connector._normalize_finding(SAMPLE_FINDING)
        assert "arn:aws:s3:::resilai-test-bucket" in event.payload["resources"]

    def test_sync_pagination(self, mock_aws_credentials):
        """Multiple pages of findings are all collected."""
        connector = self._make_connector(mock_aws_credentials)
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {"Findings": [SAMPLE_FINDING]},
            {"Findings": [SAMPLE_FINDING_LOW]},
        ]
        mock_client.get_paginator.return_value = mock_paginator
        connector._hub_client = mock_client

        events = _run(connector.sync())
        assert len(events) == 2

    def test_sync_error_handling(self, mock_aws_credentials):
        """API error during sync returns empty list, no crash."""
        connector = self._make_connector(mock_aws_credentials)
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.side_effect = Exception("Throttled")
        mock_client.get_paginator.return_value = mock_paginator
        connector._hub_client = mock_client

        events = _run(connector.sync())
        assert events == []
