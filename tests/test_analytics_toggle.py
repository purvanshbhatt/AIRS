"""
Tests for PATCH /api/orgs/{org_id}/analytics — analytics toggle endpoint.
"""

import pytest


def _create_org(client, name="Analytics Test Org") -> dict:
    resp = client.post("/api/orgs", json={"name": name})
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_analytics_toggle_enable(client):
    """PATCH analytics with enabled=True should return 200 and reflect the value."""
    org = _create_org(client, "Toggle Enable Org")
    org_id = org["id"]

    response = client.patch(
        f"/api/orgs/{org_id}/analytics",
        json={"analytics_enabled": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["analytics_enabled"] is True


def test_analytics_toggle_disable(client):
    """PATCH analytics with enabled=False should return 200 and reflect the value."""
    org = _create_org(client, "Toggle Disable Org")
    org_id = org["id"]

    response = client.patch(
        f"/api/orgs/{org_id}/analytics",
        json={"analytics_enabled": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["analytics_enabled"] is False


def test_analytics_toggle_round_trip(client):
    """Toggle off then back on should produce consistent state."""
    org = _create_org(client, "Round Trip Org")
    org_id = org["id"]

    # Disable
    r1 = client.patch(f"/api/orgs/{org_id}/analytics", json={"analytics_enabled": False})
    assert r1.status_code == 200
    assert r1.json()["analytics_enabled"] is False

    # Re-enable
    r2 = client.patch(f"/api/orgs/{org_id}/analytics", json={"analytics_enabled": True})
    assert r2.status_code == 200
    assert r2.json()["analytics_enabled"] is True


def test_analytics_toggle_not_found(client):
    """PATCH on a non-existent org should return 404."""
    response = client.patch(
        "/api/orgs/nonexistent-org-id/analytics",
        json={"analytics_enabled": True},
    )
    assert response.status_code == 404


def test_analytics_toggle_returns_org_response(client):
    """Response should include standard org fields (id, name)."""
    org = _create_org(client, "Response Shape Org")
    org_id = org["id"]

    response = client.patch(
        f"/api/orgs/{org_id}/analytics",
        json={"analytics_enabled": True},
    )
    data = response.json()
    assert "id" in data
    assert "name" in data
    assert data["id"] == org_id
