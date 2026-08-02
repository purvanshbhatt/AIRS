import pytest
import asyncio
from datetime import datetime, timezone

from app.connectors.microsoft import MicrosoftConnector
from app.connectors.wazuh import WazuhConnector
from app.connectors.base import NormalizedEvent
from app.services.clinic_engine.v2.providers.microsoft_provider import MicrosoftProvider
from app.services.clinic_engine.v2.providers.wazuh_provider import WazuhProvider
from app.services.clinic_engine.v2.schema import EvidenceKind, ConnectorCapability

from unittest.mock import patch

@pytest.mark.asyncio
async def test_microsoft_produces_user_evidence():
    """Proves Microsoft connector produces UserEvidence."""
    connector = MicrosoftConnector(connector_id="ms-001", organization_id="org-1")
    assert ConnectorCapability.USERS in connector.CAPABILITIES
    
    with patch.object(MicrosoftConnector, "sync") as mock_sync:
        mock_sync.return_value = [
            NormalizedEvent(
                event_type="microsoft.telemetry",
                source_system="microsoft",
                source_event_id="ms-sync-1",
                severity="low",
                payload={"organization_id": "org-1", "entra_users": [{"user_id": "u1", "userPrincipalName": "test@example.com"}]}
            )
        ]
        raw_events = await connector.collect_evidence()
    
    assert len(raw_events) > 0
    
    evidence_list = MicrosoftProvider.extract(raw_events)
    user_evidence = [e for e in evidence_list if e.kind == EvidenceKind.USER_ACCOUNT_STATUS]
    
    assert len(user_evidence) > 0
    assert user_evidence[0].organization_id == "org-1"
    assert user_evidence[0].source_connector == "microsoft"
    assert not user_evidence[0].is_expired

@pytest.mark.asyncio
async def test_wazuh_produces_device_evidence():
    """Proves Wazuh connector produces DeviceEvidence."""
    connector = WazuhConnector(connector_id="wz-001", organization_id="org-1", credentials={"wazuh_url": "mock"})
    assert ConnectorCapability.DEVICES in connector.CAPABILITIES
    
    with patch.object(WazuhConnector, "sync") as mock_sync:
        mock_sync.return_value = [
            NormalizedEvent(
                event_type="wazuh.agent_status",
                source_system="wazuh",
                source_event_id="a1",
                severity="low",
                payload={"organization_id": "org-1", "agent_id": "agent-123", "status": "active"}
            )
        ]
        raw_events = await connector.collect_evidence()
        
    assert len(raw_events) > 0
    
    evidence_list = WazuhProvider.extract(raw_events)
    device_evidence = [e for e in evidence_list if e.kind == EvidenceKind.DEVICE_SECURITY_STATUS]
    
    assert len(device_evidence) > 0
    assert device_evidence[0].organization_id == "org-1"
    assert device_evidence[0].source_connector == "wazuh"
    assert not device_evidence[0].is_expired

@pytest.mark.asyncio
async def test_expired_evidence_ignored():
    """Proves that expired evidence is correctly identified."""
    connector = MicrosoftConnector(connector_id="ms-001", organization_id="org-1")
    
    with patch.object(MicrosoftConnector, "sync") as mock_sync:
        mock_sync.return_value = [
            NormalizedEvent(
                event_type="microsoft.telemetry",
                source_system="microsoft",
                source_event_id="ms-sync-1",
                severity="low",
                payload={"organization_id": "org-1", "entra_users": [{"user_id": "u1", "userPrincipalName": "test@example.com"}]}
            )
        ]
        raw_events = await connector.collect_evidence()
    
    evidence_list = MicrosoftProvider.extract(raw_events)
    
    ev = evidence_list[0]
    # Fast forward the collected_at time to simulate expired evidence
    import datetime as dt
    ev.collected_at = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=2)
    ev.ttl = 3600 # 1 hour TTL
    
    assert ev.is_expired

@pytest.mark.asyncio
async def test_organization_isolation_enforced():
    """Proves evidence holds organization IDs securely."""
    connector_a = MicrosoftConnector(connector_id="ms-a", organization_id="org-a")
    connector_b = MicrosoftConnector(connector_id="ms-b", organization_id="org-b")
    
    with patch.object(MicrosoftConnector, "sync") as mock_sync:
        mock_sync.side_effect = lambda: [
            NormalizedEvent(
                event_type="microsoft.telemetry",
                source_system="microsoft",
                source_event_id="ms-sync-1",
                severity="low",
                payload={"entra_users": [{"user_id": "u1"}]}
            )
        ]
        raw_a = await connector_a.collect_evidence()
        raw_b = await connector_b.collect_evidence()
    
    ev_a = MicrosoftProvider.extract(raw_a)
    ev_b = MicrosoftProvider.extract(raw_b)
    
    assert all(e.organization_id == "org-a" for e in ev_a)
    assert all(e.organization_id == "org-b" for e in ev_b)

@pytest.mark.asyncio
async def test_connector_health_failure():
    """Proves Connector failure is handled gracefully."""
    connector = MicrosoftConnector(connector_id="ms-fail", organization_id="org-1", credentials={"client_secret": "invalid"})
    health = await connector.health_check()
    assert health.status in ["authentication_failed", "unreachable"]
