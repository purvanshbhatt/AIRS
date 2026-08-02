import pytest
import pytest_asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.services.wazuh_client import WazuhClient, WazuhAgentStatusResponse, WazuhVulnerabilitiesResponse, AgentStatus
from app.services.evidence.adapters.wazuh import WazuhAdapter
from app.services.evidence.base_adapter import EvidenceAdapter, EvidenceRecord, AdapterHealth


@pytest.fixture
def mock_wazuh_client():
    client = MagicMock(spec=WazuhClient)
    
    # Mock agent status
    status_mock = WazuhAgentStatusResponse(
        total_agents=10,
        active_agents=9,
        disconnected_agents=1,
        pending_agents=0,
        never_connected_agents=0,
        agent_list=[
            AgentStatus(agent_id="001", agent_name="srv1", ip_address="10.0.0.1", status="active")
        ]
    )
    client.get_agent_status = AsyncMock(return_value=status_mock)
    
    # Mock vulnerabilities
    vuln_mock = WazuhVulnerabilitiesResponse(
        total_vulnerabilities=5,
        critical_count=1,
        high_count=2,
        medium_count=2,
        low_count=0,
        vulnerabilities=[]
    )
    client.get_vulnerabilities = AsyncMock(return_value=vuln_mock)
    
    return client


@pytest.fixture
def wazuh_adapter(mock_wazuh_client):
    return WazuhAdapter(mock_wazuh_client)


def test_wazuh_adapter_conformance(wazuh_adapter):
    assert isinstance(wazuh_adapter, EvidenceAdapter)
    assert wazuh_adapter.connector_name == "wazuh"


@pytest.mark.asyncio
async def test_wazuh_adapter_fetch_evidence(wazuh_adapter, mock_wazuh_client):
    records = await wazuh_adapter.fetch_evidence()
    assert len(records) == 2
    
    status_record = next(r for r in records if r.control_id == "DC-001")
    assert isinstance(status_record, EvidenceRecord)
    assert status_record.connector_name == "wazuh"
    assert status_record.metadata["total_agents"] == 10
    assert status_record.metadata["active_agents"] == 9
    
    vuln_record = next(r for r in records if r.control_id == "TL-001")
    assert vuln_record.connector_name == "wazuh"
    assert vuln_record.metadata["total_vulnerabilities"] == 5
    assert vuln_record.metadata["critical_count"] == 1


@pytest.mark.asyncio
async def test_wazuh_adapter_health(wazuh_adapter, mock_wazuh_client):
    health = await wazuh_adapter.health()
    assert isinstance(health, AdapterHealth)
    assert health.healthy is True
    assert health.success_count == 1
    assert health.failure_count == 0
    assert "Active agents: 9" in health.detail


@pytest.mark.asyncio
async def test_wazuh_adapter_health_failure(wazuh_adapter, mock_wazuh_client):
    mock_wazuh_client.get_agent_status = AsyncMock(side_effect=Exception("Timeout"))
    health = await wazuh_adapter.health()
    assert health.healthy is False
    assert health.failure_count == 1
    assert "Timeout" in health.detail
