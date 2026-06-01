import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from types import SimpleNamespace

from app.core.security.encryption import generate_encryption_key, get_encryption_service
from app.db.firestore import _wazuh_config_to_doc, _decrypt_doc_fields
from app.models.wazuh_config import WazuhConfig
from app.models.organization import Organization
from app.services.wazuh_client import WazuhAgentStatusResponse

def test_wazuh_config_encryption_round_trip(monkeypatch):
    """Verify that sensitive Wazuh configuration fields are encrypted before saving and correctly decrypted."""
    monkeypatch.setenv("ENCRYPTION_SECRET", generate_encryption_key())
    get_encryption_service.cache_clear()
    
    config = SimpleNamespace(
        id="c1",
        org_id="org1",
        wazuh_host="wazuh.example.com",
        wazuh_port=55000,
        wazuh_api_key="my-secret-key-12345",
        verify_ssl=True,
        created_at=None,
        updated_at=None,
    )
    
    doc = _wazuh_config_to_doc(config)
    
    # Assert it is encrypted
    assert "encrypted_blob" in doc
    assert "wazuh_api_key" not in doc
    assert doc["wazuh_host"] == "wazuh.example.com"
    
    # Decrypt
    decrypted = _decrypt_doc_fields(doc)
    assert decrypted["wazuh_api_key"] == "my-secret-key-12345"
    assert decrypted["wazuh_host"] == "wazuh.example.com"


def test_wazuh_configure_persistence(client, db_session, monkeypatch):
    """Verify that configuring Wazuh saves details in the database and triggers a Firestore dual-write."""
    # Mock Firestore save helper
    firestore_save_mock = MagicMock(return_value=True)
    monkeypatch.setattr("app.db.firestore.firestore_save_wazuh_config", firestore_save_mock)
    
    # Mock WazuhClient authentication so we don't make real network calls
    monkeypatch.setattr("app.services.wazuh_client.WazuhClient._get_jwt_token", MagicMock(return_value="mock-token"))
    
    # 1. Create organization owned by dev-user
    org = Organization(id="test-org-123", name="Test Org", owner_uid="dev-user")
    db_session.add(org)
    db_session.commit()
    
    # 2. Call configure endpoint (v1)
    payload = {
        "org_id": "test-org-123",
        "wazuh_host": "wazuh.test",
        "wazuh_port": 55000,
        "wazuh_api_key": "some-api-key-here",
        "verify_ssl": True
    }
    
    response = client.post("/api/v1/integrations/wazuh/configure", json=payload)
    assert response.status_code == 200
    
    # 3. Check SQLite database config
    cfg = db_session.query(WazuhConfig).filter(WazuhConfig.org_id == "test-org-123").first()
    assert cfg is not None
    assert cfg.wazuh_host == "wazuh.test"
    assert cfg.wazuh_api_key == "some-api-key-here"
    
    # 4. Check Firestore dual-write was triggered
    firestore_save_mock.assert_called_once()


def test_wazuh_client_factory_resolution(db_session):
    """Verify that WazuhClientFactory retrieves a client from SQLite database config."""
    from app.services.wazuh_client import WazuhClientFactory
    
    org_id = "test-org-factory-1"
    # Ensure cache is clean
    WazuhClientFactory.invalidate_client(org_id)
    
    # 1. Add WazuhConfig to database
    cfg = WazuhConfig(
        org_id=org_id,
        wazuh_host="wazuh.factory.test",
        wazuh_port=55000,
        wazuh_api_key="api-key-factory",
        verify_ssl=False
    )
    db_session.add(cfg)
    db_session.commit()
    
    # 2. Retrieve client
    client = WazuhClientFactory.get_client(org_id, db_session)
    assert client is not None
    assert client.host == "wazuh.factory.test"
    assert client.api_key == "api-key-factory"
    
    # 3. Assert in-memory cache caching (same client instance on repeat call)
    client2 = WazuhClientFactory.get_client(org_id, db_session)
    assert client is client2


def test_wazuh_client_factory_firestore_fallback(db_session, monkeypatch):
    """Verify that WazuhClientFactory falls back to Firestore when SQLite is empty, then hydrates SQLite."""
    from app.services.wazuh_client import WazuhClientFactory
    
    org_id = "test-org-fs-fallback"
    WazuhClientFactory.invalidate_client(org_id)
    
    # Ensure SQLite is empty for this org
    db_session.query(WazuhConfig).filter(WazuhConfig.org_id == org_id).delete()
    db_session.commit()
    
    # Mock Firestore Client
    mock_doc = MagicMock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = {
        "org_id": org_id,
        "wazuh_host": "fs-fallback.host",
        "wazuh_port": 55000,
        "wazuh_api_key": "fs-api-key",
        "verify_ssl": True
    }
    
    mock_collection = MagicMock()
    mock_collection.document.return_value.get.return_value = mock_doc
    
    mock_fs_client = MagicMock()
    mock_fs_client.collection.return_value = mock_collection
    
    monkeypatch.setattr("app.db.firestore.is_firestore_available", lambda: True)
    monkeypatch.setattr("app.db.firestore.get_firestore_client", lambda: mock_fs_client)
    monkeypatch.setattr("app.db.firestore._decrypt_doc_fields", lambda d: d)
    
    # Retrieve client - should trigger fallback
    client = WazuhClientFactory.get_client(org_id, db_session)
    assert client is not None
    assert client.host == "fs-fallback.host"
    assert client.api_key == "fs-api-key"
    
    # Verify SQLite DB is hydrated
    cfg = db_session.query(WazuhConfig).filter(WazuhConfig.org_id == org_id).first()
    assert cfg is not None
    assert cfg.wazuh_host == "fs-fallback.host"
    assert cfg.wazuh_api_key == "fs-api-key"


def test_wazuh_telemetry_cache_fallback(client, db_session, monkeypatch):
    """Verify that v1 telemetry endpoint returns from cache, falling back to a refresh on cache miss."""
    from app.models.wazuh_telemetry_cache import WazuhTelemetryCache
    
    org_id = "test-org-123"
    
    # 1. Create organization owned by dev-user
    org = db_session.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        org = Organization(id=org_id, name="Test Org", owner_uid="dev-user")
        db_session.add(org)
        
    # Ensure cache is empty
    db_session.query(WazuhTelemetryCache).filter(WazuhTelemetryCache.org_id == org_id).delete()
    
    # Ensure config exists
    cfg = db_session.query(WazuhConfig).filter(WazuhConfig.org_id == org_id).first()
    if not cfg:
        cfg = WazuhConfig(
            org_id=org_id,
            wazuh_host="wazuh.test",
            wazuh_port=55000,
            wazuh_api_key="api-key",
            verify_ssl=False
        )
        db_session.add(cfg)
    db_session.commit()
    
    # Mock WazuhClient responses for immediate refresh
    mock_status = WazuhAgentStatusResponse(
        total_agents=3,
        active_agents=3,
        disconnected_agents=0,
        pending_agents=0,
        never_connected_agents=0,
        agent_list=[]
    )
    monkeypatch.setattr("app.services.wazuh_client.WazuhClient.get_agent_status", AsyncMock(return_value=mock_status))
    monkeypatch.setattr("app.services.wazuh_client.WazuhClient.get_vulnerabilities", AsyncMock(return_value=MagicMock(to_dict=lambda: {})))
    monkeypatch.setattr("app.services.wazuh_client.WazuhClient._get_jwt_token", AsyncMock(return_value="token"))
    
    # Call endpoint - should hit cache miss, refresh, and return
    response = client.get("/api/v1/integrations/wazuh/agent-status")
    assert response.status_code == 200
    assert response.json()["total_agents"] == 3
    
    # Check cache table is populated
    cache = db_session.query(WazuhTelemetryCache).filter(WazuhTelemetryCache.org_id == org_id).first()
    assert cache is not None
    assert "total_agents" in cache.agent_status


def test_wazuh_audit_logs_format(db_session, monkeypatch):
    """Verify that record_connector_audit writes structured JSON logs suitable for SIEM ingestion."""
    from app.services.audit import record_connector_audit
    import json
    
    logged_messages = []
    def mock_info(msg):
        logged_messages.append(msg)
        
    monkeypatch.setattr("app.services.audit.logger.info", mock_info)
    monkeypatch.setattr("app.core.logging.get_request_id", lambda: "test-req-id")
    
    record_connector_audit(
        db=db_session,
        org_id="audit-org-1",
        action="poll_success",
        actor="system",
        connector_type="wazuh",
        status="success",
        extra_details={"test_key": "test_val"}
    )
    
    assert len(logged_messages) == 1
    log_payload = json.loads(logged_messages[0])
    
    assert log_payload["event"] == "integration.poll_success"
    assert log_payload["connector_type"] == "wazuh"
    assert log_payload["org_id"] == "audit-org-1"
    assert log_payload["actor"] == "system"
    assert log_payload["status"] == "success"
    assert log_payload["request_id"] == "test-req-id"
    assert log_payload["test_key"] == "test_val"
    assert "timestamp" in log_payload


def test_demo_mode_write_blocking(client, db_session, monkeypatch):
    """Verify that the demo environment blocks configuration changes for Wazuh, Splunk, and Elastic."""
    # Mock settings.ENV to be Environment.DEMO
    from app.core.config import Environment
    monkeypatch.setattr("app.core.config.settings.ENV", Environment.DEMO)
    
    # 1. Wazuh configure should fail with 403
    payload = {
        "org_id": "test-org-123",
        "wazuh_host": "wazuh.test",
        "wazuh_port": 55000,
        "wazuh_api_key": "some-api-key-here",
        "verify_ssl": True
    }
    response = client.post("/api/v1/integrations/wazuh/configure", json=payload)
    assert response.status_code == 403
    assert "read-only" in response.json()["error"]["message"].lower()
    
    # 2. Splunk configure should fail with 403
    splunk_payload = {
        "splunk_host": "splunk.test",
        "splunk_hec_token": "token-12345"
    }
    response = client.post("/api/v1/integrations/splunk/configure", json=splunk_payload)
    assert response.status_code == 403
    
    # 3. Elastic configure should fail with 403
    elastic_payload = {
        "elastic_host": "elastic.test",
        "elastic_api_key": "elastic-key-12345"
    }
    response = client.post("/api/v1/integrations/elastic/configure", json=elastic_payload)
    assert response.status_code == 403
