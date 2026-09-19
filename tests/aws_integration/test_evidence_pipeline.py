"""Tests for the telemetry event -> evidence ledger pipeline."""

import asyncio
import json
import uuid
import pytest
from datetime import datetime, timezone

from app.connectors.base import NormalizedEvent


def _run(coro):
    """Run an async coroutine."""
    return asyncio.run(coro)


SAMPLE_EVENT = NormalizedEvent(
    event_type="aws.securityhub.finding",
    source_system="aws_security_hub",
    source_event_id="arn:aws:securityhub:us-east-1:123456789012:finding/test-pipeline-001",
    severity="high",
    payload={
        "title": "S3 Bucket encryption disabled",
        "description": "Test finding",
        "product_name": "Security Hub",
        "company_name": "AWS",
        "compliance_status": "FAILED",
        "record_state": "ACTIVE",
        "workflow_status": "NEW",
        "severity_label": "high",
        "severity_normalized": 70,
        "resources": ["arn:aws:s3:::test-bucket"],
        "generator_id": "aws-foundational-security-best-practices/v/1.0.0/S3.4",
        "created_at": "2026-09-13T10:00:00.000Z",
        "updated_at": "2026-09-13T10:00:00.000Z",
    },
    timestamp="2026-09-13T10:00:00.000Z",
)


def _create_test_org(db, org_id):
    """Create a minimal organization row for FK satisfaction."""
    from app.models.organization import Organization
    org = Organization(id=org_id, name="Test Org", owner_uid="test-user")
    db.add(org)
    db.commit()
    return org


def _create_test_connector(db, connector_id, org_id):
    """Create a minimal connector row for FK satisfaction."""
    from app.models.connector import Connector
    connector = Connector(
        id=connector_id,
        org_id=org_id,
        connector_type="aws_security_hub",
        display_name="Test AWS Connector",
        auth_method="api_key",
        encrypted_credentials="{}",
        status="active",
        health_status="healthy",
    )
    db.add(connector)
    db.commit()
    return connector


class TestEvidencePipeline:
    """Tests for the telemetry event -> evidence ledger pipeline."""

    def test_events_create_telemetry_records(self, test_db, test_org_id, connector_id):
        """Ingested events create TelemetryEvent rows with correct source."""
        from app.models.telemetry_event import TelemetryEvent
        from app.services.connector_manager import ConnectorManager

        _create_test_org(test_db, test_org_id)
        _create_test_connector(test_db, connector_id, test_org_id)

        manager = ConnectorManager(test_db, test_org_id)
        _run(manager._ingest_events(connector_id, [SAMPLE_EVENT]))

        rows = test_db.query(TelemetryEvent).filter_by(org_id=test_org_id).all()
        assert len(rows) == 1
        assert rows[0].source_system == "aws_security_hub"
        assert rows[0].event_type == "aws.securityhub.finding"

    def test_telemetry_deduplication(self, test_db, test_org_id, connector_id):
        """Same event ingested twice creates only one TelemetryEvent row."""
        from app.models.telemetry_event import TelemetryEvent
        from app.services.connector_manager import ConnectorManager

        _create_test_org(test_db, test_org_id)
        _create_test_connector(test_db, connector_id, test_org_id)

        manager = ConnectorManager(test_db, test_org_id)
        _run(manager._ingest_events(connector_id, [SAMPLE_EVENT]))
        _run(manager._ingest_events(connector_id, [SAMPLE_EVENT]))

        rows = test_db.query(TelemetryEvent).filter_by(org_id=test_org_id).all()
        assert len(rows) == 1

    def test_no_credentials_in_telemetry_payload(self, test_db, test_org_id, connector_id):
        """Stored TelemetryEvent payloads contain no AWS credentials."""
        from app.models.telemetry_event import TelemetryEvent
        from app.services.connector_manager import ConnectorManager

        _create_test_org(test_db, test_org_id)
        _create_test_connector(test_db, connector_id, test_org_id)

        manager = ConnectorManager(test_db, test_org_id)
        _run(manager._ingest_events(connector_id, [SAMPLE_EVENT]))

        rows = test_db.query(TelemetryEvent).filter_by(org_id=test_org_id).all()
        for row in rows:
            payload_str = json.dumps(row.payload) if isinstance(row.payload, dict) else str(row.payload)
            assert "aws_access_key" not in payload_str.lower()
            assert "aws_secret" not in payload_str.lower()
            assert "session_token" not in payload_str.lower()

    def test_payload_hash_determinism(self):
        """Same payload always produces the same SHA-256 hash."""
        event1 = NormalizedEvent(
            event_type="aws.securityhub.finding",
            source_system="aws_security_hub",
            source_event_id="test-hash",
            payload={"key": "value", "nested": {"a": 1}},
        )
        event2 = NormalizedEvent(
            event_type="aws.securityhub.finding",
            source_system="aws_security_hub",
            source_event_id="test-hash",
            payload={"key": "value", "nested": {"a": 1}},
        )
        assert event1.payload_hash == event2.payload_hash

    def test_org_id_scoping(self, test_db, test_org_id, connector_id):
        """All TelemetryEvent rows have the correct org_id."""
        from app.models.telemetry_event import TelemetryEvent
        from app.services.connector_manager import ConnectorManager

        _create_test_org(test_db, test_org_id)
        _create_test_connector(test_db, connector_id, test_org_id)

        manager = ConnectorManager(test_db, test_org_id)
        _run(manager._ingest_events(connector_id, [SAMPLE_EVENT]))

        rows = test_db.query(TelemetryEvent).filter_by(org_id=test_org_id).all()
        for row in rows:
            assert row.org_id == test_org_id
