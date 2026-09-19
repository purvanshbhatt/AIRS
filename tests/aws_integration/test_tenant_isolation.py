"""Verify that AWS telemetry is org-scoped and cross-tenant access is denied."""

import asyncio
import json
import uuid
import pytest

from app.connectors.base import NormalizedEvent


def _run(coro):
    """Run an async coroutine."""
    return asyncio.run(coro)


def _create_test_org(db, org_id):
    from app.models.organization import Organization
    org = Organization(id=org_id, name=f"Test Org {org_id[:8]}", owner_uid=f"user-{org_id[:8]}")
    db.add(org)
    db.commit()
    return org


def _create_test_connector(db, connector_id, org_id):
    from app.models.connector import Connector
    connector = Connector(
        id=connector_id,
        org_id=org_id,
        connector_type="aws_security_hub",
        display_name=f"AWS Connector {org_id[:8]}",
        auth_method="api_key",
        encrypted_credentials="{}",
        status="active",
        health_status="healthy",
    )
    db.add(connector)
    db.commit()
    return connector


class TestTenantIsolation:
    """Verify that AWS telemetry is org-scoped and cross-tenant access is denied."""

    def test_org_a_cannot_access_org_b_telemetry(self, test_db, test_org_id, test_org_id_b):
        """Events ingested for Org A are invisible to Org B queries."""
        from app.models.telemetry_event import TelemetryEvent
        from app.services.connector_manager import ConnectorManager

        _create_test_org(test_db, test_org_id)
        _create_test_org(test_db, test_org_id_b)
        conn_a_id = str(uuid.uuid4())
        _create_test_connector(test_db, conn_a_id, test_org_id)

        event = NormalizedEvent(
            event_type="aws.securityhub.finding",
            source_system="aws_security_hub",
            source_event_id="finding-org-a-only",
            severity="high",
            payload={"title": "Org A finding"},
        )

        manager_a = ConnectorManager(test_db, test_org_id)
        _run(manager_a._ingest_events(conn_a_id, [event]))

        # Org B should see nothing
        rows_b = test_db.query(TelemetryEvent).filter_by(org_id=test_org_id_b).all()
        assert len(rows_b) == 0

        # Org A should see the event
        rows_a = test_db.query(TelemetryEvent).filter_by(org_id=test_org_id).all()
        assert len(rows_a) == 1

    def test_org_a_cannot_access_org_b_connector(self, test_db, test_org_id, test_org_id_b):
        """ConnectorManager for Org B raises ConnectorNotFoundError for Org A's connector."""
        from app.services.connector_manager import ConnectorManager, ConnectorNotFoundError

        _create_test_org(test_db, test_org_id)
        _create_test_org(test_db, test_org_id_b)
        conn_a_id = str(uuid.uuid4())
        _create_test_connector(test_db, conn_a_id, test_org_id)

        manager_b = ConnectorManager(test_db, test_org_id_b)
        with pytest.raises(ConnectorNotFoundError):
            manager_b.get_connector(conn_a_id)

    def test_connector_manager_enforces_org_scope(self, test_db, test_org_id, test_org_id_b):
        """Org A can access its connector; Org B is denied."""
        from app.services.connector_manager import ConnectorManager, ConnectorNotFoundError

        _create_test_org(test_db, test_org_id)
        _create_test_org(test_db, test_org_id_b)
        conn_id = str(uuid.uuid4())
        _create_test_connector(test_db, conn_id, test_org_id)

        manager_a = ConnectorManager(test_db, test_org_id)
        connector = manager_a.get_connector(conn_id)
        assert connector is not None
        assert connector.org_id == test_org_id

        manager_b = ConnectorManager(test_db, test_org_id_b)
        with pytest.raises(ConnectorNotFoundError):
            manager_b.get_connector(conn_id)
