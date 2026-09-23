"""
Paywall enforcement integration tests.

Verifies that endpoints correctly return HTTP 402 when the organization
lacks the required entitlement, and HTTP 200/201 when entitled.
"""
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Must be set before importing app modules
os.environ["TESTING"] = "true"
os.environ["ENV"] = "local"
os.environ["AUTH_REQUIRED"] = "false"

from fastapi.testclient import TestClient

from app.main import app
from app.services.billing.entitlements import Entitlement, EntitlementService


# ── Test Setup ──────────────────────────────────────────────────────────

client = TestClient(app)


def _auth_headers():
    """Return headers that bypass auth in dev mode."""
    return {"Content-Type": "application/json"}


def _mock_org(plan="free", status="unpaid"):
    """Create a mock org with subscription fields."""
    org = MagicMock()
    org.id = "test-paywall-org"
    org.name = "Paywall Test Org"
    org.owner_uid = "dev-user"
    org.subscription_plan = plan
    org.subscription_status = status
    org.subscription_id = None
    org.customer_id = None
    org.current_period_end = None
    org.org_mode = "production"
    return org


# ── Entitlement Service Mock ────────────────────────────────────────────


class TestPaywallEnforcement:
    """Test that endpoints correctly enforce entitlements."""

    def test_capabilities_endpoint_returns_plan(self):
        """GET /api/orgs/{org_id}/capabilities should return the entitlement map."""
        with patch("app.api.billing.OrganizationService") as MockOrgSvc, \
             patch("app.api.billing.EntitlementService") as MockEntSvc:
            mock_org = _mock_org(plan="design-partner", status="active")
            MockOrgSvc.return_value.get.return_value = mock_org
            MockEntSvc.return_value.get_capabilities.return_value = {
                "plan": "design-partner",
                "status": "active",
                "is_paid": True,
                "entitlements": {"demo_access": True, "connectors_manage": True},
            }

            resp = client.get("/api/orgs/test-paywall-org/capabilities", headers=_auth_headers())
            assert resp.status_code == 200
            data = resp.json()
            assert data["plan"] == "design-partner"
            assert data["is_paid"] is True

    def test_billing_activate_works(self):
        """POST /api/orgs/{org_id}/billing/activate should activate a plan."""
        with patch("app.api.billing.OrganizationService") as MockOrgSvc, \
             patch("app.api.billing.CheckoutService") as MockCheckout:
            mock_org = _mock_org()
            MockOrgSvc.return_value.get.return_value = mock_org
            MockCheckout.return_value.activate_plan_direct.return_value = {
                "success": True,
                "plan": "design-partner",
                "status": "active",
                "current_period_end": "2027-09-22T00:00:00+00:00",
            }

            resp = client.post(
                "/api/orgs/test-paywall-org/billing/activate",
                json={"plan": "design-partner"},
                headers=_auth_headers(),
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["plan"] == "design-partner"

    def test_402_returned_for_unpaid_connector_create(self):
        """POST /api/v1/connectors should return 402 for unpaid org."""
        with patch("app.core.entitlements._resolve_org_id", return_value="test-paywall-org"), \
             patch("app.core.entitlements.EntitlementService") as MockEntSvc:
            mock_svc = MockEntSvc.return_value
            mock_svc.has.return_value = False
            mock_svc.get_effective_plan.return_value = "free"

            resp = client.post(
                "/api/v1/connectors",
                json={
                    "connector_type": "splunk",
                    "display_name": "Test Connector",
                    "auth_method": "token",
                    "credentials": {"token": "test"},
                },
                headers=_auth_headers(),
            )
            assert resp.status_code == 402
            body = resp.json()
            # The app's error middleware wraps HTTPException detail into
            # {"error": {"message": "<stringified detail>", ...}}
            body_str = str(body)
            assert "PAYMENT_REQUIRED" in body_str
            assert "connectors_manage" in body_str

    def test_402_returned_for_unpaid_api_key_create(self):
        """POST /api/orgs/{org_id}/api-keys should return 402 for unpaid org."""
        with patch("app.core.entitlements._resolve_org_id", return_value="test-paywall-org"), \
             patch("app.core.entitlements.EntitlementService") as MockEntSvc:
            mock_svc = MockEntSvc.return_value
            mock_svc.has.return_value = False
            mock_svc.get_effective_plan.return_value = "free"

            resp = client.post(
                "/api/orgs/test-paywall-org/api-keys",
                json={"scopes": ["read"]},
                headers=_auth_headers(),
            )
            assert resp.status_code == 402

    def test_webhook_endpoint_accepts_events(self):
        """POST /api/billing/webhook should process events."""
        with patch("app.api.billing.CheckoutService") as MockCheckout:
            MockCheckout.return_value.handle_stripe_event.return_value = {
                "status": "ignored",
                "event_type": "account.updated",
            }

            resp = client.post(
                "/api/billing/webhook",
                json={
                    "type": "account.updated",
                    "data": {"object": {}},
                },
                headers=_auth_headers(),
            )
            assert resp.status_code == 200
