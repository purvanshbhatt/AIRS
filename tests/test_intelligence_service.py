"""
Unit tests for the Technology Intelligence Drift Detection Service.
"""

import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.organization import Organization
from app.models.telemetry_event import TelemetryEvent
from app.models.software_catalog import SoftwareCatalog
from app.models.drift_event import DriftEvent
from app.services.intelligence import IntelligenceService


@pytest.fixture
def mock_org(db_session: Session) -> Organization:
    """Create a mock organization in the database."""
    org = Organization(
        id="test-org-123",
        name="Test Enterprise",
        owner_uid="test-user-uid",
        integration_status="{}",
    )
    db_session.add(org)
    db_session.commit()
    return org


@pytest.fixture
def mock_user():
    """Mock user object to bypass authentication."""
    class MockUser:
        uid = "test-user-uid"
        org_id = "test-org-123"
    return MockUser()


# =============================================================================
# Core Logic Unit Tests
# =============================================================================

def test_version_older_logic():
    """Verify semantic version drift checking rules."""
    # Simple semantic versions
    assert IntelligenceService.is_version_older("3.8.0", "3.12.3") is True
    assert IntelligenceService.is_version_older("3.12.3", "3.8.0") is False
    assert IntelligenceService.is_version_older("3.12.3", "3.12.3") is False

    # Tag prefix handling (leading v)
    assert IntelligenceService.is_version_older("v3.8.0", "v3.12.3") is True
    assert IntelligenceService.is_version_older("V3.12.3", "v3.8.0") is False

    # Extra components
    assert IntelligenceService.is_version_older("1.22", "1.29.2") is True
    assert IntelligenceService.is_version_older("12", "16.2") is True


@pytest.mark.asyncio
@patch("app.services.intelligence.httpx.AsyncClient")
async def test_fetch_github_releases(mock_async_client):
    """Test fetcher parses GitHub releases metadata correctly."""
    from unittest.mock import MagicMock
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "tag_name": "v3.12.3",
        "html_url": "https://github.com/python/cpython/releases/tag/v3.12.3",
        "published_at": "2024-04-09T18:00:00Z",
    }
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__.return_value = mock_client
    mock_async_client.return_value = mock_client

    service = IntelligenceService(None, "test-org-123")
    res = await service.fetch_github_latest_release("python/cpython")
    assert res is not None
    assert res["tag_name"] == "v3.12.3"
    assert res["html_url"] == "https://github.com/python/cpython/releases/tag/v3.12.3"


@pytest.mark.asyncio
@patch("app.services.intelligence.httpx.AsyncClient")
async def test_fetch_cisa_kev_feed(mock_async_client):
    """Test fetcher scans CISA KEV JSON feed for products."""
    from unittest.mock import MagicMock
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "vulnerabilities": [
            {
                "cveID": "CVE-2023-1234",
                "vendorProject": "Python Software Foundation",
                "product": "Python",
                "shortDescription": "Vulnerability description",
                "notes": "https://nvd.nist.gov/vuln/detail/CVE-2023-1234",
                "dateAdded": "2023-01-01",
            }
        ]
    }
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_resp
    mock_client.__aenter__.return_value = mock_client
    mock_async_client.return_value = mock_client

    service = IntelligenceService(None, "test-org-123")
    res = await service.fetch_cisa_kev_advisory("python")
    assert res is not None
    assert res["cve_id"] == "CVE-2023-1234"
    assert "detail/CVE-2023-1234" in res["advisory_url"]


@pytest.mark.asyncio
@patch("app.services.intelligence.httpx.AsyncClient")
async def test_fetch_nvd_isolated_failures(mock_async_client):
    """Verify NVD client handles failures gracefully without crashing."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = Exception("NVD API Timeout")
    mock_client.__aenter__.return_value = mock_client
    mock_async_client.return_value = mock_client

    service = IntelligenceService(None, "test-org-123")
    # Should not raise exception
    res = await service.fetch_nvd_severity("python")
    assert res is None


# =============================================================================
# Integration & API Tests
# =============================================================================

@pytest.mark.asyncio
@patch("app.services.intelligence.IntelligenceService.fetch_github_latest_release")
@patch("app.services.intelligence.IntelligenceService.fetch_cisa_kev_advisory")
@patch("app.services.intelligence.IntelligenceService.fetch_nvd_severity")
async def test_drift_detection_flow(
    mock_nvd, mock_cisa, mock_github, db_session: Session, mock_org: Organization
):
    """Verify version Diff Engine creates catalog entries and triggers DriftEvents."""
    # 1. Setup mock returns
    mock_github.return_value = {
        "tag_name": "3.12.3",
        "html_url": "https://github.com/python/cpython/releases/tag/v3.12.3",
        "published_at": "2024-04-09T18:00:00Z",
    }
    mock_cisa.return_value = None
    mock_nvd.return_value = "high"

    # 2. Seed a TelemetryEvent representing Microsoft Connector software inventory
    ev = TelemetryEvent(
        org_id=mock_org.id,
        connector_id="mock-conn-id",
        event_type="azure_security_center.software_inventory",
        source_system="azure_security_center",
        source_event_id="software-inv-python",
        payload_hash="mock-hash",
        payload={
            "product": "python",
            "vendor": "Python Software Foundation",
            "version": "3.8.0",
        },
        severity="low",
    )
    db_session.add(ev)
    db_session.commit()

    # 3. Run sync
    service = IntelligenceService(db_session, mock_org.id)
    drift_count = await service.sync_intelligence_and_detect_drift()

    assert drift_count == 1

    # 4. Check DB entries
    catalog_item = (
        db_session.query(SoftwareCatalog)
        .filter(SoftwareCatalog.org_id == mock_org.id, SoftwareCatalog.product == "python")
        .first()
    )
    assert catalog_item is not None
    assert catalog_item.current_version == "3.8.0"
    assert catalog_item.latest_version == "3.12.3"
    assert catalog_item.severity == "high"

    drift_event = (
        db_session.query(DriftEvent)
        .filter(DriftEvent.org_id == mock_org.id, DriftEvent.signal_type == "software_drift")
        .first()
    )
    assert drift_event is not None
    assert "version 3.8.0" in drift_event.description
    assert drift_event.severity == "high"


def test_api_endpoints_flow(client: TestClient, db_session: Session, mock_org: Organization, mock_user):
    """Test GET and POST HTTP endpoint requests."""
    # Bypass auth using overrides
    from app.core.auth import require_auth
    from app.core.demo_guard import require_writable

    def mock_require_auth():
        return mock_user

    def mock_require_writable():
        return None

    client.app.dependency_overrides[require_auth] = mock_require_auth
    client.app.dependency_overrides[require_writable] = mock_require_writable

    try:
        # Seed software catalog item
        entry = SoftwareCatalog(
            org_id=mock_org.id,
            product="python",
            vendor="Python Software Foundation",
            current_version="3.8.0",
            latest_version="3.12.3",
            severity="high",
        )
        db_session.add(entry)
        db_session.commit()

        # Test GET /api/v1/intelligence/latest-versions
        resp = client.get("/api/v1/intelligence/latest-versions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["product"] == "python"
        assert data[0]["current_version"] == "3.8.0"
        assert data[0]["latest_version"] == "3.12.3"

        # Test POST /api/v1/intelligence/sync (mocks downstream fetchers)
        with patch("app.services.intelligence.IntelligenceService.sync_intelligence_and_detect_drift", return_value=0) as mock_sync:
            resp_post = client.post("/api/v1/intelligence/sync")
            assert resp_post.status_code == 200
            assert resp_post.json() == {"status": "success", "drift_detected": 0}
            mock_sync.assert_called_once()

    finally:
        client.app.dependency_overrides.clear()
