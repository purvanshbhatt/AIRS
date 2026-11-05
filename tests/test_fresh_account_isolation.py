"""
Fresh account isolation and zero-synthetic-data acceptance tests.

Enforces:
1. Fresh organization has 0% verification, 0 evidence, and unknown readiness status.
2. Demo data is never seeded for real organizations (org_mode != 'demo').
3. Unpaid organization is blocked from connector creation with HTTP 402.
4. Direct activation is strictly blocked in production with HTTP 403.
5. Admin test exemption is explicit (ADMIN_TEST_EXEMPTION != PAID_SUBSCRIPTION).
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

os.environ["TESTING"] = "true"
os.environ["ENV"] = "staging"
os.environ["AUTH_REQUIRED"] = "false"

from app.main import app
from app.models.organization import Organization
from app.core.auth import User, require_auth, get_current_user

client = TestClient(app)


def _auth_headers():
    return {"Content-Type": "application/json"}


class TestFreshAccountIsolation:
    """Acceptance tests for new customer isolation and commercial gates."""

    def test_fresh_organization_has_zero_synthetic_data(self):
        """A new customer organization without connectors must return 0% verification."""
        fresh_org = Organization(
            id="fresh-customer-org-001",
            name="Acme Health Testing",
            industry="Healthcare",
            size="1-50",
            org_mode="production",
            subscription_plan="free",
            subscription_status="unpaid",
            owner_uid="regular-customer-uid",
        )

        regular_user = User(
            uid="regular-customer-uid",
            email="customer@clinic.com",
            name="Customer Admin",
        )
        app.dependency_overrides[get_current_user] = lambda: regular_user
        try:
            with patch("app.services.organization.OrganizationService") as MockOrgSvc, \
                 patch("app.api.clinic.router._fetch_persisted_telemetry", return_value=[]), \
                 patch("app.services.clinic_engine.v2.pilot.PilotService.get_mode", return_value="production"):

                MockOrgSvc.return_value.get.return_value = fresh_org

                resp = client.get("/api/clinic/readiness/fresh-customer-org-001")
                assert resp.status_code == 200
                data = resp.json()

                # Zero synthetic telemetry invariants
                assert data["clinic_health_pct"] == 0
                assert data["connector_health_pct"] == 0
                assert data["status"] == "unknown"
                assert len(data.get("failed_checks", [])) == 0
                assert len(data.get("passed_checks", [])) == 0
                assert len(data.get("timeline", [])) == 0
                assert len(data.get("immediate_actions", [])) == 0
                assert data["coverage"]["coverage_pct"] == 0
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_unpaid_customer_blocked_from_connector_create(self):
        """Unpaid organization receives HTTP 402 with structured payment required payload."""
        regular_user = User(
            uid="customer-unpaid-002",
            email="unpaid@example.com",
            name="Unpaid User",
        )
        app.dependency_overrides[require_auth] = lambda: regular_user
        try:
            with patch("app.core.entitlements._resolve_org_id", return_value="unpaid-org-002"), \
                 patch("app.core.entitlements.EntitlementService") as MockEnt:
                mock_svc = MockEnt.return_value
                mock_svc.has.return_value = False
                mock_svc.get_effective_plan.return_value = "free"

                resp = client.post(
                    "/api/v1/connectors",
                    json={
                        "connector_type": "aws",
                        "display_name": "AWS Security Hub",
                        "auth_method": "iam_role",
                        "credentials": {"role_arn": "arn:aws:iam::123456789012:role/ResilAI"},
                    },
                    headers=_auth_headers(),
                )
                assert resp.status_code == 402
                body = resp.json()
                assert "PAYMENT_REQUIRED" in str(body)
                assert "connectors_manage" in str(body)
        finally:
            app.dependency_overrides.pop(require_auth, None)

    def test_direct_activation_production_vs_staging(self):
        """Direct plan activation is allowed in staging but blocked in production."""
        regular_user = User(
            uid="customer-003",
            email="customer3@example.com",
            name="Customer Three",
        )
        app.dependency_overrides[require_auth] = lambda: regular_user
        try:
            with patch("app.api.billing.OrganizationService") as MockOrgSvc, \
                 patch("app.api.billing.CheckoutService") as MockCheckout:
                mock_org = MagicMock()
                mock_org.id = "org-003"
                MockOrgSvc.return_value.get.return_value = mock_org

                # 1. Staging environment -> succeeds
                MockCheckout.return_value.activate_plan_direct.return_value = {
                    "success": True,
                    "plan": "design-partner",
                    "status": "active",
                }
                with patch("app.core.config.settings.ENV", "staging"):
                    resp_staging = client.post(
                        "/api/orgs/org-003/billing/activate",
                        json={"plan": "design-partner"},
                        headers=_auth_headers(),
                    )
                    assert resp_staging.status_code == 200
                    assert resp_staging.json()["success"] is True

                # 2. Production environment -> 403 Forbidden
                with patch("app.core.config.settings.ENV", "prod"):
                    resp_prod = client.post(
                        "/api/orgs/org-003/billing/activate",
                        json={"plan": "design-partner"},
                        headers=_auth_headers(),
                    )
                    assert resp_prod.status_code == 403
                    assert "DIRECT_ACTIVATION_DISABLED" in str(resp_prod.json())
        finally:
            app.dependency_overrides.pop(require_auth, None)

    def test_admin_test_exemption_explicit_contract(self):
        """Admin test accounts have explicit is_exempt=True and is_paid=False."""
        admin_user = User(
            uid="purvansh-admin-uid",
            email="purvansh@resilai.org",
            name="Purvansh Bhatt",
        )
        app.dependency_overrides[require_auth] = lambda: admin_user
        try:
            with patch("app.api.billing.OrganizationService") as MockOrgSvc:
                mock_org = MagicMock()
                mock_org.id = "admin-test-org"
                MockOrgSvc.return_value.get.return_value = mock_org

                resp = client.get(
                    "/api/orgs/admin-test-org/capabilities",
                    headers=_auth_headers(),
                )
                assert resp.status_code == 200
                data = resp.json()
                assert data["plan"] == "enterprise"
                assert data["status"] == "exempt"
                assert data["is_exempt"] is True
                assert data["is_paid"] is False
                assert data["exemption_type"] == "admin_test"
                assert data["entitlements"]["connectors_manage"] is True
        finally:
            app.dependency_overrides.pop(require_auth, None)
