"""Unit tests for the Microsoft Security Graph Connector.

Tests cover:
  - Connector registration and initialization.
  - OAuth2 client credentials authentication and caching.
  - Resilience/exponential backoff for HTTP 429 rate limits.
  - Data extraction and normalization (Intune, Entra ID, Defender).
  - VerificationService integration (SOC-Verified vs. Contradicted states).
  - FastAPI custom API routes for Microsoft sync and health.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.connectors.base import ConnectorHealth, PermissionResult
from app.connectors.registry import ConnectorRegistry
from app.connectors.microsoft import MicrosoftConnector, request_with_backoff
from app.core.auth import require_auth
from app.main import app
from app.models.connector import Connector, ConnectorType, ConnectorStatus
from app.schemas.microsoft import TelemetryPayload
from app.services.verification import VerificationService, VerificationStatusEnum


# =============================================================================
# Connector Registry & Initialization Tests
# =============================================================================

def test_connector_registration():
    """Verify that MicrosoftConnector is registered with ConnectorRegistry."""
    cls = ConnectorRegistry.get_connector_class("microsoft")
    assert cls == MicrosoftConnector
    assert "microsoft" in ConnectorRegistry.list_available_connectors()


def test_connector_initialization():
    """Verify connector credentials and configuration loading."""
    creds = {
        "tenant_id": "test-tenant",
        "client_id": "test-client",
        "client_secret": "test-secret"
    }
    config = {"custom_option": "value"}
    conn = MicrosoftConnector(
        connector_id="conn-123",
        organization_id="org-123",
        credentials=creds,
        config=config,
    )
    assert conn.connector_id == "conn-123"
    assert conn.org_id == "org-123"
    assert conn._tenant_id == "test-tenant"
    assert conn._client_id == "test-client"
    assert conn._resolve_client_secret() == "test-secret"
    assert conn._config == config


# =============================================================================
# Authentication Tests
# =============================================================================

@pytest.mark.asyncio
@patch("app.connectors.microsoft.httpx.AsyncClient")
async def test_authenticate_success(mock_async_client):
    """Test successful client credentials authentication."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "access_token": "mock-access-token",
        "expires_in": 3600,
    }
    
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client.__aenter__.return_value = mock_client
    mock_async_client.return_value = mock_client

    conn = MicrosoftConnector(
        connector_id="conn-123",
        organization_id="org-123",
        credentials={
            "tenant_id": "t",
            "client_id": "c",
            "client_secret": "s"
        }
    )
    
    success = await conn.authenticate()
    assert success is True
    assert conn._token == "mock-access-token"
    assert conn._authenticated is True


@pytest.mark.asyncio
@patch("app.connectors.microsoft.httpx.AsyncClient")
async def test_authenticate_failure(mock_async_client):
    """Test authentication failure."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 400
    mock_resp.text = "Invalid client secret"
    
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_resp
    mock_client.__aenter__.return_value = mock_client
    mock_async_client.return_value = mock_client

    conn = MicrosoftConnector(
        connector_id="conn-123",
        organization_id="org-123",
        credentials={
            "tenant_id": "t",
            "client_id": "c",
            "client_secret": "s"
        }
    )
    
    success = await conn.authenticate()
    assert success is False
    assert conn._token is None
    assert conn._authenticated is False


# =============================================================================
# Backoff & Resilience Tests
# =============================================================================

@pytest.mark.asyncio
@patch("app.connectors.microsoft.asyncio.sleep", new_callable=AsyncMock)
async def test_request_with_backoff_429(mock_sleep):
    """Verify that request_with_backoff handles HTTP 429 and retries with backoff."""
    mock_client = AsyncMock()
    
    # First response: 429, Second response: 200
    resp_429 = MagicMock(spec=httpx.Response)
    resp_429.status_code = 429
    resp_429.headers = {"Retry-After": "2"}
    
    resp_200 = MagicMock(spec=httpx.Response)
    resp_200.status_code = 200
    
    mock_client.request.side_effect = [resp_429, resp_200]
    
    resp = await request_with_backoff(mock_client, "GET", "https://graph.microsoft.com/v1.0")
    
    assert resp.status_code == 200
    mock_sleep.assert_called_once_with(2.0)


# =============================================================================
# Data Extraction & Normalization Sync Tests
# =============================================================================

@pytest.mark.asyncio
@patch("app.connectors.microsoft.IntuneService.fetch_devices")
@patch("app.connectors.microsoft.EntraIDService.fetch_users_and_mfa")
@patch("app.connectors.microsoft.DefenderService.fetch_alerts")
async def test_connector_sync_normalization(
    mock_fetch_alerts, mock_fetch_users, mock_fetch_devices
):
    """Test full sync pipeline and normalization into TelemetryPayload."""
    # Seed mock responses from services
    from app.schemas.microsoft import IntuneDeviceTelemetry, EntraUserTelemetry, DefenderAlertTelemetry
    
    mock_fetch_devices.return_value = [
        IntuneDeviceTelemetry(
            device_id="d1",
            device_name="device1",
            compliance_state="compliant",
            bitlocker_status="encrypted",
            os_version="10.0.19045",
        ),
        IntuneDeviceTelemetry(
            device_id="d2",
            device_name="device2",
            compliance_state="noncompliant",
            bitlocker_status="not_encrypted",
            os_version="10.0.19045",
        )
    ]
    mock_fetch_users.return_value = [
        EntraUserTelemetry(
            user_id="u1",
            user_principal_name="admin@domain.com",
            mfa_enforced=True,
            conditional_access_status="enforced",
        ),
        EntraUserTelemetry(
            user_id="u2",
            user_principal_name="user@domain.com",
            mfa_enforced=False,
            conditional_access_status="unknown",
        )
    ]
    mock_fetch_alerts.return_value = [
        DefenderAlertTelemetry(
            alert_id="a1",
            title="High Severity Malicious Activity",
            severity="high",
            status="new",
            device_id="d1",
        )
    ]

    conn = MicrosoftConnector(
        connector_id="conn-123",
        organization_id="org-123",
        credentials={"tenant_id": "t", "client_id": "c", "client_secret": "s"}
    )
    conn._authenticated = True
    conn._token = "mock-token"

    events = await conn.sync()
    
    assert len(events) == 1
    event = events[0]
    assert event.event_type == "microsoft.telemetry"
    assert event.source_system == "microsoft"
    
    # Validate payload against TelemetryPayload schema
    payload = TelemetryPayload(**event.payload)
    assert payload.organization_id == "org-123"
    assert payload.connector_id == "conn-123"
    assert len(payload.intune_devices) == 2
    assert len(payload.entra_users) == 2
    assert len(payload.defender_alerts) == 1
    
    # Verify pre-computed summary statistics
    summary = payload.summary
    assert summary["total_devices"] == 2
    assert summary["compliance_rate_pct"] == 50.0
    assert summary["bitlocker_rate_pct"] == 50.0
    assert summary["total_users"] == 2
    assert summary["mfa_enforced_rate_pct"] == 50.0
    assert summary["active_high_severity_alerts"] == 1
    assert summary["edr_coverage_pct"] == 50.0


# =============================================================================
# VerificationService Integration Tests
# =============================================================================

class MockFinding:
    def __init__(self, rule_id, title, severity="high"):
        self.rule_id = rule_id
        self.title = title
        self.severity = severity


@pytest.mark.asyncio
async def test_verification_service_evaluation():
    """Test that VerificationService evaluates findings correctly against DB Evidence."""
    mock_db = MagicMock()
    mock_evidence_high = MagicMock()
    mock_evidence_high.evidence_hash = "mock-hash-high"
    mock_evidence_high.severity = "high"

    # Initially return a high severity evidence (should result in SOC_VERIFIED)
    mock_db.query().filter().order_by().first.return_value = mock_evidence_high

    svc = VerificationService(db=mock_db)
    
    # 1. EDR compliance failure (rule DC-001) should return SOC_VERIFIED
    finding_edr = MockFinding(rule_id="DC-001", title="Inadequate EDR Coverage")
    res_edr = await svc.verify_finding(finding_edr)
    assert res_edr.status == VerificationStatusEnum.SOC_VERIFIED
    assert "SIEM-Verified via Adapter" in res_edr.evidence_summary

    # 2. MFA failure (rule IV-001) should return SOC_VERIFIED
    finding_mfa = MockFinding(rule_id="IV-001", title="MFA Not Enforced")
    res_mfa = await svc.verify_finding(finding_mfa)
    assert res_mfa.status == VerificationStatusEnum.SOC_VERIFIED
    assert "SIEM-Verified via Adapter" in res_mfa.evidence_summary

    # Clean compliance (critical severity means it contradicts)
    mock_evidence_crit = MagicMock()
    mock_evidence_crit.evidence_hash = "mock-hash-crit"
    mock_evidence_crit.severity = "critical"
    mock_db.query().filter().order_by().first.return_value = mock_evidence_crit

    # 3. Clean compliance should result in CONTRADICTED findings
    res_edr_clean = await svc.verify_finding(finding_edr)
    assert res_edr_clean.status == VerificationStatusEnum.CONTRADICTED

    res_mfa_clean = await svc.verify_finding(finding_mfa)
    assert res_mfa_clean.status == VerificationStatusEnum.CONTRADICTED


# =============================================================================
# API Route Endpoint Tests
# =============================================================================

def test_api_routes_not_found(client):
    """Verify that Microsoft API endpoints return 404 if no connector is registered."""
    mock_user = MagicMock()
    mock_user.org_id = "org-123"
    mock_user.uid = "user-123"
    
    app.dependency_overrides[require_auth] = lambda: mock_user
    try:
        # 1. Test Sync Route Not Found
        resp_sync = client.post("/api/v1/connectors/microsoft/sync")
        assert resp_sync.status_code == 404
        assert "connector not found" in resp_sync.json()["error"]["message"]

        # 2. Test Health Route Not Found
        resp_health = client.get("/api/v1/connectors/microsoft/health")
        assert resp_health.status_code == 404
        assert "connector not found" in resp_health.json()["error"]["message"]
    finally:
        if require_auth in app.dependency_overrides:
            del app.dependency_overrides[require_auth]
