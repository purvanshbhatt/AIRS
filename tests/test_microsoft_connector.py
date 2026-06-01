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
        org_id="org-123",
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
        org_id="org-123",
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
        org_id="org-123",
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
        org_id="org-123",
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
    """Test that VerificationService evaluates findings correctly against Microsoft telemetry."""
    # Seed mock database event
    mock_db = MagicMock()
    mock_event = MagicMock()
    mock_event.source_system = "microsoft"
    
    telemetry_data = {
        "organization_id": "org-123",
        "connector_id": "conn-123",
        "timestamp": "2026-05-30T10:00:00Z",
        "intune_devices": [],
        "entra_users": [],
        "defender_alerts": [],
        "summary": {
            "total_devices": 10,
            "compliance_rate_pct": 45.0,  # Below 50% / 80% EDR threshold
            "bitlocker_rate_pct": 50.0,
            "total_users": 5,
            "mfa_enforced_rate_pct": 80.0,  # Under 100% MFA
            "active_high_severity_alerts": 2,  # Alert present
            "edr_coverage_pct": 45.0,
        }
    }
    mock_event.payload = telemetry_data
    mock_db.query().filter().order_by().first.return_value = mock_event

    svc = VerificationService(db=mock_db)
    
    # 1. EDR compliance failure (rule DC-001) should return SOC_VERIFIED because telemetry confirms failure
    finding_edr = MockFinding(rule_id="DC-001", title="Inadequate EDR Coverage")
    res_edr = await svc.verify_finding(finding_edr)
    assert res_edr.status == VerificationStatusEnum.SOC_VERIFIED
    assert "below the threshold" in res_edr.evidence_summary

    # 2. MFA failure (rule IV-001) should return SOC_VERIFIED
    finding_mfa = MockFinding(rule_id="IV-001", title="MFA Not Enforced")
    res_mfa = await svc.verify_finding(finding_mfa)
    assert res_mfa.status == VerificationStatusEnum.SOC_VERIFIED
    assert "MFA enforcement rate is 80.0%" in res_mfa.evidence_summary

    # 3. Defender Active alerts failure (rule TL-001) should return SOC_VERIFIED
    finding_alerts = MockFinding(rule_id="TL-001", title="Active Security Alerts")
    res_alerts = await svc.verify_finding(finding_alerts)
    assert res_alerts.status == VerificationStatusEnum.SOC_VERIFIED
    assert "Found 2 active high-severity" in res_alerts.evidence_summary

    # Update telemetry data to show 100% compliance/MFA and 0 alerts
    telemetry_data_clean = {
        "organization_id": "org-123",
        "connector_id": "conn-123",
        "timestamp": "2026-05-30T10:00:00Z",
        "intune_devices": [],
        "entra_users": [],
        "defender_alerts": [],
        "summary": {
            "total_devices": 10,
            "compliance_rate_pct": 98.0,  # Compliant
            "bitlocker_rate_pct": 98.0,
            "total_users": 5,
            "mfa_enforced_rate_pct": 100.0,  # Fully enforced
            "active_high_severity_alerts": 0,  # 0 alerts
            "edr_coverage_pct": 98.0,
        }
    }
    mock_event.payload = telemetry_data_clean
    svc._microsoft_cache = None  # Clear cache to reload

    # Clean compliance should result in CONTRADICTED findings
    res_edr_clean = await svc.verify_finding(finding_edr)
    assert res_edr_clean.status == VerificationStatusEnum.CONTRADICTED

    res_mfa_clean = await svc.verify_finding(finding_mfa)
    assert res_mfa_clean.status == VerificationStatusEnum.CONTRADICTED

    res_alerts_clean = await svc.verify_finding(finding_alerts)
    assert res_alerts_clean.status == VerificationStatusEnum.CONTRADICTED


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
