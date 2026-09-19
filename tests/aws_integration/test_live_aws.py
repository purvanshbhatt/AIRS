"""
Live integration tests for AWS Security Hub Connector.

Executes against the live AWS test environment deployed in Phase 20
when AWS credentials / active session are present.
"""
from __future__ import annotations

import asyncio
import os
import pytest

from app.connectors.aws_security_hub import AWSSecurityHubConnector
from app.services.connector_manager import ConnectorManager
from app.models.organization import Organization
from app.models.connector import Connector


@pytest.mark.aws_integration
class TestLiveAWSIntegration:
    """Live tests against real AWS Security Hub environment."""

    @pytest.fixture(autouse=True)
    def check_aws_session(self):
        """Verify AWS CLI / SDK can reach AWS Security Hub or skip."""
        try:
            import boto3
            session = boto3.Session(region_name="us-east-1")
            hub = session.client("securityhub")
            hub.describe_hub()
        except Exception as exc:
            pytest.skip(f"Live AWS Security Hub not reachable: {exc}")

    def test_live_security_hub_authentication(self):
        """Verify live authentication against AWS Security Hub."""
        connector = AWSSecurityHubConnector(
            connector_id="live-test-conn",
            org_id="live-test-org",
            credentials={"aws_region": "us-east-1"},
        )
        auth_ok = asyncio.run(connector.authenticate())
        assert auth_ok is True
        assert connector._authenticated is True

    def test_live_security_hub_health(self):
        """Verify live health check against AWS Security Hub."""
        connector = AWSSecurityHubConnector(
            connector_id="live-test-conn",
            org_id="live-test-org",
            credentials={"aws_region": "us-east-1"},
        )
        asyncio.run(connector.authenticate())
        health = asyncio.run(connector.health_check())
        assert health.status == "healthy"
        assert health.latency_ms is not None
        assert health.latency_ms > 0

    def test_live_security_hub_permissions(self):
        """Verify live permissions validation against AWS Security Hub."""
        connector = AWSSecurityHubConnector(
            connector_id="live-test-conn",
            org_id="live-test-org",
            credentials={"aws_region": "us-east-1"},
        )
        asyncio.run(connector.authenticate())
        perms = asyncio.run(connector.validate_permissions())
        assert perms.valid is True
        assert len(perms.missing_permissions) == 0

    def test_live_security_hub_sync(self):
        """Verify live sync against AWS Security Hub returns valid event list."""
        connector = AWSSecurityHubConnector(
            connector_id="live-test-conn",
            org_id="live-test-org",
            credentials={"aws_region": "us-east-1"},
        )
        asyncio.run(connector.authenticate())
        events = asyncio.run(connector.sync())
        assert isinstance(events, list)

    def test_live_connector_manager_sync(self, test_db, test_org_id, connector_id):
        """Verify full ConnectorManager pipeline with live AWS Security Hub."""
        # Create test org & connector in in-memory test_db
        org = Organization(id=test_org_id, name="Live AWS Test Org", owner_uid="test-user")
        test_db.add(org)
        test_db.commit()

        connector = Connector(
            id=connector_id,
            org_id=test_org_id,
            connector_type="aws_security_hub",
            display_name="Live AWS Security Hub",
            auth_method="api_key",
            encrypted_credentials="{}",
            config={"aws_region": "us-east-1"},
            status="active",
            health_status="healthy",
        )
        test_db.add(connector)
        test_db.commit()

        manager = ConnectorManager(test_db, test_org_id)
        result = asyncio.run(manager.sync_connector(connector_id))

        assert result.success is True
        assert result.duration_ms >= 0
