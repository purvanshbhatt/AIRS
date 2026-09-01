import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.wazuh_config import WazuhConfig
from app.models.wazuh_telemetry_cache import WazuhTelemetryCache
from app.models.connector import Connector
from app.core.auth import User

@pytest.fixture
def mock_auth():
    # Mock require_auth to return a valid user with an org_id
    user = User(uid="test_uid", email="test@example.com")
    user.org_id = "test-org"
    return user

@pytest.fixture
def mock_wazuh_client():
    with patch("app.services.wazuh_client.WazuhClientFactory.get_client") as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client

@pytest.fixture
def mock_refresh_cache():
    with patch("app.services.wazuh_client.refresh_wazuh_cache") as mock:
        mock.return_value = True
        yield mock

def test_wazuh_connect_success(client, mock_auth, mock_wazuh_client, mock_refresh_cache):
    from app.core.auth import require_auth
    client.app.dependency_overrides[require_auth] = lambda: mock_auth

    payload = {
        "org_id": "test-org",
        "manager_host": "192.168.1.100",
        "port": 55000,
        "credentials": "supersecretapikey123"
    }

    response = client.post("/api/v1/connectors/wazuh/connect", json=payload)
    
    assert response.status_code != 422, response.text
    
    client.app.dependency_overrides.clear()

def test_wazuh_connect_missing_org_id(client, mock_auth):
    from app.core.auth import require_auth
    client.app.dependency_overrides[require_auth] = lambda: mock_auth

    payload = {
        "manager_host": "192.168.1.100",
        "port": 55000,
        "credentials": "supersecretapikey123"
    }

    response = client.post("/api/v1/connectors/wazuh/connect", json=payload)
    
    assert response.status_code == 422
    assert "org_id" in response.text
    
    client.app.dependency_overrides.clear()

def test_wazuh_connect_invalid_credentials(client, mock_auth, mock_wazuh_client):
    from app.core.auth import require_auth
    client.app.dependency_overrides[require_auth] = lambda: mock_auth

    payload = {
        "org_id": "test-org",
        "manager_host": "192.168.1.100",
        "port": 55000,
        "credentials": "short" # < 8 characters
    }

    response = client.post("/api/v1/connectors/wazuh/connect", json=payload)
    
    assert response.status_code == 422
    assert "credentials" in response.text
    
    client.app.dependency_overrides.clear()

def test_wazuh_connect_api_timeout(client, mock_auth, mock_wazuh_client):
    from app.core.auth import require_auth
    client.app.dependency_overrides[require_auth] = lambda: mock_auth
    
    # Mock timeout exception during refresh_wazuh_cache
    with patch("app.services.wazuh_client.refresh_wazuh_cache") as mock_refresh:
        import httpx
        mock_refresh.side_effect = httpx.TimeoutException("API timeout", request=None) if hasattr(httpx, "TimeoutException") else Exception("API timeout")
        
        payload = {
            "org_id": "test-org",
            "manager_host": "192.168.1.100",
            "port": 55000,
            "credentials": "supersecretapikey123"
        }

        # The endpoint should catch it and return 400
        response = client.post("/api/v1/connectors/wazuh/connect", json=payload)
        
        assert response.status_code == 400
        assert "Wazuh connection failed: API timeout" in response.text

    client.app.dependency_overrides.clear()
