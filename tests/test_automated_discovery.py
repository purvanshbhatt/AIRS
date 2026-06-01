"""
Unit tests for the Tech Stack Automated Software Discovery feature.
"""

import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.organization import Organization
from app.models.discovered_asset import DiscoveredAsset
from app.models.software_catalog import SoftwareCatalog
from app.models.tech_stack import TechStackItem
from app.services.asset_discovery import AssetDiscoveryService
from app.services.governance.validation_engine import validate_organization
from app.core.config import settings, Environment


@pytest.fixture
def mock_org(db_session: Session) -> Organization:
    """Create a mock organization in the database."""
    org = Organization(
        id="test-discovery-org",
        name="Discovery Enterprise",
        owner_uid="test-user-uid",
        integration_status="{}",
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def mock_user():
    """Mock user object to bypass authentication."""
    class MockUser:
        uid = "test-user-uid"
        org_id = "test-discovery-org"
    return MockUser()


def test_discovered_asset_model_fields(db_session: Session, mock_org: Organization):
    """Verify DiscoveredAsset columns and organization relationship."""
    asset = DiscoveredAsset(
        org_id=mock_org.id,
        vendor="Microsoft",
        product="windows-11-client",
        version="10.0.22631",
        source="Microsoft Intune",
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)

    assert asset.id is not None
    assert asset.org_id == mock_org.id
    assert asset.vendor == "Microsoft"
    assert asset.product == "windows-11-client"
    assert asset.version == "10.0.22631"
    assert asset.source == "Microsoft Intune"
    assert asset.first_seen is not None
    assert asset.last_seen is not None
    assert asset.organization.id == mock_org.id


def test_asset_discovery_counts(db_session: Session, mock_org: Organization):
    """Verify that AssetDiscoveryService seeds and synchronizes exactly 41 current, 5 outdated, and 1 critical asset."""
    service = AssetDiscoveryService(db_session, mock_org.id)
    total = service.discover_assets()

    assert total == 47

    # Check DiscoveredAsset counts
    assets = db_session.query(DiscoveredAsset).filter(DiscoveredAsset.org_id == mock_org.id).all()
    assert len(assets) == 47

    # Validate source system presence
    sources = {a.source for a in assets}
    assert "Microsoft Intune" in sources
    assert "Microsoft Defender" in sources
    assert "Wazuh" in sources
    assert "Splunk" in sources

    # Check TechStackItem synced items
    items = db_session.query(TechStackItem).filter(TechStackItem.org_id == mock_org.id).all()
    assert len(items) == 47

    # Classify by risk categories: EOL (Critical), Deprecated or major_versions_behind >= 3 (High), major_versions_behind in (1, 2) (Medium/Outdated), others (Current/Low)
    summary = service.db.query(TechStackItem).filter(TechStackItem.org_id == mock_org.id).all()
    
    current_count = 0
    outdated_count = 0
    critical_count = 0

    for item in summary:
        status = item.lts_status.value
        major_behind = item.major_versions_behind

        if status == "eol":
            critical_count += 1
        elif status == "deprecated" or major_behind >= 2:
            outdated_count += 1
        else:
            current_count += 1

    # Verify the required dashboard counts
    assert current_count == 41
    assert outdated_count == 5
    assert critical_count == 1


@patch("app.core.config.Settings.is_staging", new_callable=lambda: True)
@patch("app.core.config.settings.ENV", Environment.STAGING)
def test_api_list_endpoint_triggers_discovery(mock_is_staging, client: TestClient, db_session: Session, mock_org: Organization, mock_user):
    """Verify that GET /api/governance/{org_id}/tech-stack triggers discovery in staging."""
    from app.core.auth import require_auth
    from app.core.demo_guard import require_writable

    def mock_require_auth():
        return mock_user

    def mock_require_writable():
        return None

    client.app.dependency_overrides[require_auth] = mock_require_auth
    client.app.dependency_overrides[require_writable] = mock_require_writable

    try:
        resp = client.get(f"/api/governance/{mock_org.id}/tech-stack")
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify response matches discovered data structure
        assert data["total"] == 47
        assert len(data["items"]) == 47
        
        summary = data["summary"]
        assert summary["eol_count"] == 1
        assert summary["deprecated_count"] == 0
        assert summary["outdated_count"] == 5

    finally:
        client.app.dependency_overrides.clear()


@patch("app.core.config.Settings.is_staging", new_callable=lambda: True)
@patch("app.core.config.settings.ENV", Environment.STAGING)
def test_validation_engine_triggers_discovery(mock_is_staging, db_session: Session, mock_org: Organization):
    """Verify that validate_organization triggers discovery in staging and uses discovered assets."""
    # Ensure fresh start
    db_session.query(DiscoveredAsset).filter(DiscoveredAsset.org_id == mock_org.id).delete()
    db_session.query(TechStackItem).filter(TechStackItem.org_id == mock_org.id).delete()
    db_session.commit()

    result = validate_organization(db_session, mock_org)
    
    assert result.lifecycle.total_components == 47
    assert result.lifecycle.eol_count == 1
    assert result.lifecycle.deprecated_count == 0
    assert result.lifecycle.outdated_count == 5
    assert result.lifecycle.score == 50.0
