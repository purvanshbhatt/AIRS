"""Tests that ResilAI handles AWS failure states correctly."""

import asyncio
import pytest
from unittest.mock import patch, MagicMock

from app.connectors.aws_security_hub import AWSSecurityHubConnector


def _run(coro):
    """Run an async coroutine."""
    return asyncio.run(coro)


class TestNegativeCases:
    """Tests that ResilAI handles AWS failure states correctly.

    Expected behaviors:
    - Invalid credentials: auth fails, no crash
    - Missing permissions: PermissionResult.valid=False
    - Security Hub not enabled: health unreachable
    - Malformed findings: graceful skip, no crash
    - Partial failures: no false positives
    """

    def _make_connector(self, credentials=None):
        return AWSSecurityHubConnector(
            connector_id="neg-test",
            org_id="neg-org",
            credentials=credentials or {},
        )

    def test_invalid_credentials_auth_fails(self):
        """Invalid AWS credentials cause authentication to fail gracefully."""
        connector = self._make_connector(
            {"aws_access_key_id": "INVALID", "aws_secret_access_key": "INVALID"}
        )
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_client.describe_hub.side_effect = Exception("InvalidClientTokenId")
        mock_session.client.return_value = mock_client

        mock_boto3 = MagicMock()
        mock_boto3.Session.return_value = mock_session

        with patch.dict("sys.modules", {"boto3": mock_boto3}):
            result = _run(connector.authenticate())
            assert result is False

    def test_insufficient_permissions(self):
        """Missing GetFindings permission is reported in PermissionResult."""
        connector = self._make_connector()
        connector._hub_client = MagicMock()
        connector._hub_client.describe_hub.return_value = {}
        connector._hub_client.get_findings.side_effect = Exception("AccessDeniedException")

        result = _run(connector.validate_permissions())
        assert result.valid is False
        assert "securityhub:GetFindings" in result.missing_permissions

    def test_security_hub_not_enabled(self):
        """When Security Hub is not enabled, health returns unreachable."""
        connector = self._make_connector()
        connector._hub_client = MagicMock()
        connector._hub_client.describe_hub.side_effect = Exception(
            "InvalidAccessException: Security Hub is not enabled"
        )

        result = _run(connector.health_check())
        assert result.status == "unreachable"

    def test_malformed_finding_payload(self):
        """Finding with minimal/missing fields does not crash normalization."""
        connector = self._make_connector()
        malformed = {"Id": "test-malformed"}
        event = connector._normalize_finding(malformed)
        assert event.event_type == "aws.securityhub.finding"
        assert event.source_event_id == "test-malformed"
        assert event.payload["title"] == ""

    def test_partial_sync_failure(self):
        """Sync error returns empty list rather than crashing."""
        connector = self._make_connector()
        mock_client = MagicMock()
        mock_paginator = MagicMock()
        mock_paginator.paginate.side_effect = Exception("API Error")
        mock_client.get_paginator.return_value = mock_paginator
        connector._hub_client = mock_client

        events = _run(connector.sync())
        assert events == []

    def test_empty_payload_handling(self):
        """Finding with empty severity/resources normalizes with defaults."""
        connector = self._make_connector()
        finding = {
            "Id": "empty-payload-test",
            "Severity": {},
            "Resources": [],
        }
        event = connector._normalize_finding(finding)
        assert event.source_event_id == "empty-payload-test"
        assert event.severity == "medium"  # default

    def test_boto3_not_installed_graceful_degradation(self):
        """When boto3 is missing, authenticate returns False without crash."""
        connector = self._make_connector()
        with patch.dict("sys.modules", {"boto3": None}):
            result = _run(connector.authenticate())
            assert result is False

    def test_not_authenticated_validate_permissions(self):
        """Permissions check on unauthenticated connector returns valid=False."""
        connector = self._make_connector()
        result = _run(connector.validate_permissions())
        assert result.valid is False
        assert "Not authenticated" in result.message
