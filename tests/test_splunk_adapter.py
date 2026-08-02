import pytest
import pytest_asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, PropertyMock

from app.services.evidence.adapters.splunk import SplunkAdapter
from app.services.evidence.base_adapter import EvidenceAdapter, EvidenceRecord, AdapterHealth


@pytest.fixture
def splunk_connector():
    """A ``MagicMock`` shaped like SplunkConnector for unit tests."""
    connector = MagicMock(name="SplunkConnector")
    # Health: healthy response
    health_healthy = MagicMock()
    health_healthy.status = "healthy"
    health_healthy.message = "Splunk MCP v9.1.0"
    connector.health_check = AsyncMock(return_value=health_healthy)
    # Sync: returns a single mock NormalizedEvent
    sync_event = MagicMock()
    sync_event.event_type = "splunk.mfa_evidence"
    sync_event.parsed_fields = {"severity": "high"}
    sync_event.source_event_id = "ev-1"
    sync_event.payload = {"control_id": "IV-001", "host": "auth-01"}
    sync_event.timestamp = "2026-07-13T00:00:00Z"
    sync_event.severity = "high"
    sync_event.id = "ev-1"
    sync_event.raw = "raw payload"
    sync_event.host = "auth-01"
    sync_event.source = "splunk"
    sync_event.sourcetype = "mfa_logs"
    sync_event.time = "2026-07-13T00:00:00Z"
    connector.sync = AsyncMock(return_value=[sync_event])
    return connector


@pytest.fixture
def splunk_adapter(splunk_connector):
    adapter = SplunkAdapter(splunk_connector)
    return adapter


def test_splunk_adapter_conformance(splunk_adapter):
    assert isinstance(splunk_adapter, EvidenceAdapter)
    assert splunk_adapter.connector_name == "splunk"


@pytest.mark.asyncio
async def test_splunk_adapter_health_ok(splunk_adapter, splunk_connector):
    health = await splunk_adapter.health()
    assert isinstance(health, AdapterHealth)
    assert health.healthy is True
    assert health.success_count == 1
    assert health.failure_count == 0
    assert "MCP v9.1.0" in health.detail


@pytest.mark.asyncio
async def test_splunk_adapter_health_unhealthy(splunk_connector):
    splunk_connector.health_check = AsyncMock(
        return_value=MagicMock(status="degraded", message="MCP not reachable")
    )
    adapter = SplunkAdapter(splunk_connector)
    health = await adapter.health()
    assert health.healthy is False
    assert health.failure_count == 1
    assert health.detail == "MCP not reachable"


@pytest.mark.asyncio
async def test_splunk_adapter_health_raises(splunk_connector):
    splunk_connector.health_check = AsyncMock(side_effect=Exception("MCP timeout"))
    adapter = SplunkAdapter(splunk_connector)
    health = await adapter.health()
    assert health.healthy is False
    assert health.failure_count == 1
    assert "MCP timeout" in health.detail


@pytest.mark.asyncio
async def test_splunk_adapter_no_connector_returns_failure():
    adapter = SplunkAdapter()
    health = await adapter.health()
    assert health.healthy is False
    assert "not bound" in (health.detail or "")
