import pytest
from unittest.mock import patch, MagicMock, AsyncMock, ANY
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from app.main import app
from app.schemas.connector_progress import ConnectorProgressEvent, ConnectorProgressState
from app.services.wazuh_client import run_wazuh_connect_sync
from app.core.auth import User

client = TestClient(app)

@pytest.fixture
def mock_auth():
    # Mock require_auth dependency to bypass Firebase auth check in tests
    with patch("app.api.integrations.require_auth") as mock:
        user = User(uid="test_uid", email="test@example.com")
        user.org_id = "test-org"
        mock.return_value = user
        yield user

def test_progress_event_model():
    """Test validation and serialization of the ConnectorProgressEvent schema."""
    event = ConnectorProgressEvent(
        org_id="org-123",
        connector_type="wazuh",
        state=ConnectorProgressState.CONNECTING,
        status_message="Connecting...",
        details={"host": "127.0.0.1"},
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    assert event.type == "connector_progress"
    assert event.state == "CONNECTING"
    assert event.details["host"] == "127.0.0.1"

    dumped = event.model_dump()
    assert dumped["state"] == "CONNECTING"

@pytest.mark.asyncio
@patch("app.core.websocket_manager.telemetry_ws_manager.broadcast_connector_progress", new_callable=AsyncMock)
@patch("app.core.websocket_manager.telemetry_ws_manager.broadcast_org_update", new_callable=AsyncMock)
@patch("app.services.wazuh_client.WazuhClientFactory.get_client")
async def test_run_wazuh_connect_sync_success(mock_get_client, mock_broadcast_org_update, mock_broadcast_progress):
    """Test run_wazuh_connect_sync successfully progresses through all states and calls API methods."""
    mock_wazuh_client = MagicMock()
    mock_wazuh_client._get_jwt_token = AsyncMock(return_value="test_token")
    
    # Mock agent status response
    mock_status = MagicMock()
    mock_status.total_agents = 217
    mock_status.to_dict.return_value = {"total_agents": 217}
    mock_wazuh_client.get_agent_status = AsyncMock(return_value=mock_status)

    # Mock vulnerabilities response
    mock_vulns = MagicMock()
    mock_vulns.total_vulnerabilities = 54
    mock_vulns.to_dict.return_value = {"total_vulnerabilities": 54}
    mock_wazuh_client.get_vulnerabilities = AsyncMock(return_value=mock_vulns)

    mock_get_client.return_value = mock_wazuh_client

    # Run background task with pacing sleep mocked to bypass delays in test
    with patch("asyncio.sleep", new_callable=AsyncMock):
        await run_wazuh_connect_sync(
            org_id="test-org",
            client_params={"wazuh_host": "wazuh.local", "wazuh_port": 55000, "wazuh_api_key": "valid_key"},
            user_uid="test_user"
        )

    # Assert correct sequence of progress broadcasts
    assert mock_broadcast_progress.call_count >= 7
    calls = [call.kwargs for call in mock_broadcast_progress.call_args_list]
    
    states = [c["state"] for c in calls]
    assert "CONNECTING" in states
    assert "AUTHENTICATING" in states
    assert "FETCHING_DEVICES" in states
    assert "FETCHING_VULNERABILITIES" in states
    assert "NORMALIZING" in states
    assert "VERIFYING_CONTROLS" in states
    assert "COMPLETE" in states

    # Assert counts were properly set in details/labels
    device_call = next(c for c in calls if c["state"] == "FETCHING_DEVICES" and "Fetching: 217 agents" in c["status_message"])
    assert device_call["details"]["agents_count"] == 217

    vuln_call = next(c for c in calls if c["state"] == "FETCHING_VULNERABILITIES" and "Fetching: 54 vulnerabilities" in c["status_message"])
    assert vuln_call["details"]["vulnerabilities_count"] == 54

    control_call = next(c for c in calls if c["state"] == "VERIFYING_CONTROLS" and "Verifying: 12" in c["status_message"])
    assert control_call["details"]["controls_count"] == 12

    # Assert GHI broadcast update was called at the end
    mock_broadcast_org_update.assert_called_once_with("test-org", db_session=ANY) # Session object check

@pytest.mark.asyncio
@patch("app.core.websocket_manager.telemetry_ws_manager.broadcast_connector_progress", new_callable=AsyncMock)
async def test_run_wazuh_connect_sync_failure(mock_broadcast_progress):
    """Test run_wazuh_connect_sync emits FAILED progress event on connection failure."""
    with patch("asyncio.sleep", new_callable=AsyncMock):
        # Trigger explicit fail.local mock check
        await run_wazuh_connect_sync(
            org_id="test-org",
            client_params={"wazuh_host": "fail.local", "wazuh_port": 55000, "wazuh_api_key": "any"},
            user_uid="test_user"
        )

    calls = [call.kwargs for call in mock_broadcast_progress.call_args_list]
    states = [c["state"] for c in calls]
    
    assert "CONNECTING" in states
    assert "FAILED" in states
    
    failed_call = next(c for c in calls if c["state"] == "FAILED")
    assert "Connection refused" in failed_call["status_message"]

def test_configure_wazuh_endpoint_initiates_background_sync(mock_auth):
    """Test configure endpoint returns 200 and initiates background sync."""
    app.dependency_overrides[app.dependency_overrides.get("require_auth", "")] = lambda: mock_auth

    with patch("app.services.organization.OrganizationService.get") as mock_get_org:
        mock_org = MagicMock()
        mock_org.id = "test-org"
        mock_get_org.return_value = mock_org

        payload = {
            "org_id": "test-org",
            "wazuh_host": "wazuh.local",
            "wazuh_port": 55000,
            "wazuh_api_key": "some_api_key",
            "verify_ssl": True
        }

        response = client.post("/api/integrations/wazuh/configure", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "initiating"
        assert "background" in data["message"]

    app.dependency_overrides.clear()
