"""Tests for AWS Security Hub connector authentication, health, and permissions."""

import asyncio
import pytest
from unittest.mock import patch, MagicMock

from app.connectors.aws_security_hub import AWSSecurityHubConnector


def _run(coro):
    """Run an async coroutine in a fresh event loop."""
    return asyncio.run(coro)


class TestAWSConnection:
    """Tests for AWS Security Hub connector authentication and health."""

    def _make_connector(self, credentials, connector_id="test-conn-id", org_id="test-org"):
        return AWSSecurityHubConnector(
            connector_id=connector_id,
            org_id=org_id,
            credentials=credentials,
        )

    def test_authenticate_success(self, mock_aws_credentials):
        """Mock boto3 session and securityhub client, verify authenticate() returns True."""
        connector = self._make_connector(mock_aws_credentials)

        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_client.describe_hub.return_value = {"HubArn": "arn:aws:securityhub:us-east-1:123456789012:hub/default"}
        mock_session.client.return_value = mock_client

        mock_boto3 = MagicMock()
        mock_boto3.Session.return_value = mock_session

        with patch.dict("sys.modules", {"boto3": mock_boto3}):
            result = _run(connector.authenticate())
            assert result is True
            assert connector._authenticated is True

    def test_authenticate_no_boto3(self, mock_aws_credentials):
        """When boto3 is not installed, authenticate() returns False gracefully."""
        connector = self._make_connector(mock_aws_credentials)

        # Remove boto3 from sys.modules so the import inside authenticate() fails
        with patch.dict("sys.modules", {"boto3": None}):
            result = _run(connector.authenticate())
            assert result is False

    def test_authenticate_invalid_credentials(self, mock_aws_credentials):
        """Invalid credentials cause describe_hub to fail, authenticate returns False."""
        connector = self._make_connector(mock_aws_credentials)

        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_client.describe_hub.side_effect = Exception("InvalidClientTokenId")
        mock_session.client.return_value = mock_client

        mock_boto3 = MagicMock()
        mock_boto3.Session.return_value = mock_session

        with patch.dict("sys.modules", {"boto3": mock_boto3}):
            result = _run(connector.authenticate())
            assert result is False
            assert connector._authenticated is False

    def test_authenticate_with_role_arn(self, mock_aws_credentials):
        """When role_arn is provided, STS assume_role is called."""
        creds = {**mock_aws_credentials, "role_arn": "arn:aws:iam::123456789012:role/test-role"}
        connector = self._make_connector(creds)

        # STS client for assume_role
        mock_sts = MagicMock()
        mock_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "temp-key",
                "SecretAccessKey": "temp-secret",
                "SessionToken": "temp-token",
            }
        }

        # Session after assuming role
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_client.describe_hub.return_value = {}
        mock_session.client.return_value = mock_client

        mock_boto3 = MagicMock()
        mock_boto3.client.return_value = mock_sts
        mock_boto3.Session.return_value = mock_session

        with patch.dict("sys.modules", {"boto3": mock_boto3}):
            result = _run(connector.authenticate())
            assert result is True
            # Verify STS assume_role was called
            mock_sts.assume_role.assert_called_once()
            call_kwargs = mock_sts.assume_role.call_args
            assert call_kwargs[1]["RoleArn"] == "arn:aws:iam::123456789012:role/test-role"

    def test_health_check_healthy(self, mock_aws_credentials):
        """When describe_hub succeeds, health status is 'healthy'."""
        connector = self._make_connector(mock_aws_credentials)
        connector._hub_client = MagicMock()
        connector._hub_client.describe_hub.return_value = {}

        result = _run(connector.health_check())
        assert result.status == "healthy"
        assert result.latency_ms is not None

    def test_health_check_unreachable(self, mock_aws_credentials):
        """When describe_hub raises, health status is 'unreachable'."""
        connector = self._make_connector(mock_aws_credentials)
        connector._hub_client = MagicMock()
        connector._hub_client.describe_hub.side_effect = Exception("Connection refused")

        result = _run(connector.health_check())
        assert result.status == "unreachable"

    def test_health_check_not_authenticated(self, mock_aws_credentials):
        """When hub_client is None, health status is 'unreachable'."""
        connector = self._make_connector(mock_aws_credentials)
        # _hub_client is None by default
        result = _run(connector.health_check())
        assert result.status == "unreachable"
        assert "Not authenticated" in result.message

    def test_validate_permissions_all_present(self, mock_aws_credentials):
        """When all API calls succeed, permissions are valid."""
        connector = self._make_connector(mock_aws_credentials)
        connector._hub_client = MagicMock()
        connector._hub_client.describe_hub.return_value = {}
        connector._hub_client.get_findings.return_value = {"Findings": []}

        result = _run(connector.validate_permissions())
        assert result.valid is True

    def test_validate_permissions_missing_get_findings(self, mock_aws_credentials):
        """When GetFindings raises, it's reported as missing permission."""
        connector = self._make_connector(mock_aws_credentials)
        connector._hub_client = MagicMock()
        connector._hub_client.describe_hub.return_value = {}
        connector._hub_client.get_findings.side_effect = Exception("AccessDenied")

        result = _run(connector.validate_permissions())
        assert result.valid is False
        assert "securityhub:GetFindings" in result.missing_permissions

    def test_validate_permissions_not_authenticated(self, mock_aws_credentials):
        """When not authenticated, permissions validation fails cleanly."""
        connector = self._make_connector(mock_aws_credentials)
        result = _run(connector.validate_permissions())
        assert result.valid is False
        assert "Not authenticated" in result.message
