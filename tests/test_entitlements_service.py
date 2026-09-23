"""
Unit tests for the EntitlementService.

Verifies:
  - Plan-to-entitlement mapping correctness
  - Effective plan resolution (active/trialing/canceled/unpaid)
  - Demo org isolation
  - Capabilities endpoint payload structure
  - Plan activation and deactivation
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.services.billing.entitlements import (
    Entitlement,
    EntitlementService,
    PLAN_ENTITLEMENTS,
)


# ── Fixtures ────────────────────────────────────────────────────────────


def _create_mock_org(
    org_id="test-org-1",
    subscription_plan="free",
    subscription_status="unpaid",
    org_mode="production",
    subscription_id=None,
    customer_id=None,
    current_period_end=None,
):
    """Create a mock Organization with billing fields."""
    org = MagicMock()
    org.id = org_id
    org.subscription_plan = subscription_plan
    org.subscription_status = subscription_status
    org.org_mode = org_mode
    org.subscription_id = subscription_id
    org.customer_id = customer_id
    org.current_period_end = current_period_end
    return org


def _create_service(mock_org=None):
    """Create an EntitlementService with a mock DB session."""
    db = MagicMock()
    if mock_org:
        db.query.return_value.filter.return_value.first.return_value = mock_org
    else:
        db.query.return_value.filter.return_value.first.return_value = None
    svc = EntitlementService(db)
    return svc, db


# ── Plan Entitlement Mapping Tests ──────────────────────────────────────


class TestPlanEntitlements:
    """Verify entitlement mapping integrity."""

    def test_free_plan_has_only_base_entitlements(self):
        free = PLAN_ENTITLEMENTS["free"]
        assert Entitlement.DEMO_ACCESS in free
        assert Entitlement.SIMULATED_DATA in free
        assert Entitlement.PUBLIC_PRODUCT_PREVIEW in free
        assert Entitlement.ACCOUNT_MANAGEMENT in free
        # Free should NOT have paid features
        assert Entitlement.CONNECTORS_MANAGE not in free
        assert Entitlement.EXECUTIVE_REPORTS not in free
        assert Entitlement.API_KEYS not in free

    def test_design_partner_includes_free_and_core_paid(self):
        dp = PLAN_ENTITLEMENTS["design-partner"]
        # Inherits free
        assert Entitlement.DEMO_ACCESS in dp
        # Has paid features
        assert Entitlement.REAL_ORGANIZATION in dp
        assert Entitlement.CONNECTORS_MANAGE in dp
        assert Entitlement.EXECUTIVE_REPORTS in dp
        assert Entitlement.TELEMETRY_INGESTION in dp
        # Not growth-tier
        assert Entitlement.API_KEYS not in dp
        assert Entitlement.WEBHOOKS not in dp

    def test_growth_includes_api_keys_and_webhooks(self):
        growth = PLAN_ENTITLEMENTS["growth"]
        assert Entitlement.API_KEYS in growth
        assert Entitlement.WEBHOOKS in growth
        assert Entitlement.ADVANCED_REPORTING in growth
        # Not enterprise
        assert Entitlement.ADVANCED_INTEGRATIONS not in growth

    def test_enterprise_includes_everything(self):
        enterprise = PLAN_ENTITLEMENTS["enterprise"]
        assert Entitlement.ADVANCED_INTEGRATIONS in enterprise
        assert Entitlement.ENTERPRISE_CONTROLS in enterprise
        assert Entitlement.CUSTOM_FRAMEWORKS in enterprise
        # All lower tiers included
        for ent in PLAN_ENTITLEMENTS["growth"]:
            assert ent in enterprise

    def test_plans_are_cumulative(self):
        """Each higher plan is a strict superset of the lower plan."""
        plan_order = ["free", "design-partner", "growth", "enterprise"]
        for i in range(1, len(plan_order)):
            lower = set(PLAN_ENTITLEMENTS[plan_order[i - 1]])
            higher = set(PLAN_ENTITLEMENTS[plan_order[i]])
            assert lower.issubset(higher), (
                f"{plan_order[i]} must be a superset of {plan_order[i-1]}"
            )


# ── Effective Plan Resolution Tests ─────────────────────────────────────


class TestEffectivePlan:
    """Verify that the effective plan correctly reflects subscription state."""

    def test_active_subscription_returns_plan(self):
        org = _create_mock_org(subscription_plan="growth", subscription_status="active")
        svc, _ = _create_service(org)
        assert svc.get_effective_plan("test-org-1") == "growth"

    def test_trialing_subscription_returns_plan(self):
        org = _create_mock_org(subscription_plan="design-partner", subscription_status="trialing")
        svc, _ = _create_service(org)
        assert svc.get_effective_plan("test-org-1") == "design-partner"

    def test_unpaid_falls_back_to_free(self):
        org = _create_mock_org(subscription_plan="growth", subscription_status="unpaid")
        svc, _ = _create_service(org)
        assert svc.get_effective_plan("test-org-1") == "free"

    def test_canceled_falls_back_to_free(self):
        org = _create_mock_org(subscription_plan="enterprise", subscription_status="canceled")
        svc, _ = _create_service(org)
        assert svc.get_effective_plan("test-org-1") == "free"

    def test_past_due_falls_back_to_free(self):
        org = _create_mock_org(subscription_plan="growth", subscription_status="past_due")
        svc, _ = _create_service(org)
        assert svc.get_effective_plan("test-org-1") == "free"

    def test_missing_org_returns_free(self):
        svc, _ = _create_service(None)
        assert svc.get_effective_plan("nonexistent") == "free"

    def test_demo_org_always_free(self):
        org = _create_mock_org(
            subscription_plan="enterprise", subscription_status="active", org_mode="demo"
        )
        svc, _ = _create_service(org)
        assert svc.get_effective_plan("test-org-1") == "free"

    def test_null_plan_defaults_to_free(self):
        org = _create_mock_org(subscription_plan=None, subscription_status="active")
        svc, _ = _create_service(org)
        assert svc.get_effective_plan("test-org-1") == "free"

    def test_null_status_defaults_to_free(self):
        org = _create_mock_org(subscription_plan="growth", subscription_status=None)
        svc, _ = _create_service(org)
        assert svc.get_effective_plan("test-org-1") == "free"


# ── Entitlement Check Tests ─────────────────────────────────────────────


class TestEntitlementCheck:
    """Verify has() correctly gates features."""

    def test_free_user_can_access_demo(self):
        org = _create_mock_org(subscription_plan="free", subscription_status="unpaid")
        svc, _ = _create_service(org)
        assert svc.has("test-org-1", Entitlement.DEMO_ACCESS) is True

    def test_free_user_cannot_create_connectors(self):
        org = _create_mock_org(subscription_plan="free", subscription_status="unpaid")
        svc, _ = _create_service(org)
        assert svc.has("test-org-1", Entitlement.CONNECTORS_MANAGE) is False

    def test_paid_user_can_create_connectors(self):
        org = _create_mock_org(subscription_plan="design-partner", subscription_status="active")
        svc, _ = _create_service(org)
        assert svc.has("test-org-1", Entitlement.CONNECTORS_MANAGE) is True

    def test_growth_user_can_create_api_keys(self):
        org = _create_mock_org(subscription_plan="growth", subscription_status="active")
        svc, _ = _create_service(org)
        assert svc.has("test-org-1", Entitlement.API_KEYS) is True

    def test_design_partner_cannot_create_api_keys(self):
        org = _create_mock_org(subscription_plan="design-partner", subscription_status="active")
        svc, _ = _create_service(org)
        assert svc.has("test-org-1", Entitlement.API_KEYS) is False

    def test_canceled_user_loses_paid_features(self):
        org = _create_mock_org(subscription_plan="growth", subscription_status="canceled")
        svc, _ = _create_service(org)
        assert svc.has("test-org-1", Entitlement.CONNECTORS_MANAGE) is False
        assert svc.has("test-org-1", Entitlement.DEMO_ACCESS) is True  # Free tier retained


# ── Capabilities Endpoint Tests ─────────────────────────────────────────


class TestCapabilities:
    """Verify the capabilities response structure."""

    def test_capabilities_structure(self):
        org = _create_mock_org(subscription_plan="design-partner", subscription_status="active")
        svc, _ = _create_service(org)
        caps = svc.get_capabilities("test-org-1")

        assert caps["plan"] == "design-partner"
        assert caps["status"] == "active"
        assert caps["is_paid"] is True
        assert isinstance(caps["entitlements"], dict)
        # Check that all Entitlement enum values are represented
        assert len(caps["entitlements"]) == len(Entitlement)

    def test_capabilities_for_free_user(self):
        org = _create_mock_org(subscription_plan="free", subscription_status="unpaid")
        svc, _ = _create_service(org)
        caps = svc.get_capabilities("test-org-1")

        assert caps["plan"] == "free"
        assert caps["is_paid"] is False
        assert caps["entitlements"]["demo_access"] is True
        assert caps["entitlements"]["connectors_manage"] is False

    def test_capabilities_for_missing_org(self):
        svc, _ = _create_service(None)
        caps = svc.get_capabilities("nonexistent")
        assert caps["plan"] == "free"
        assert caps["is_paid"] is False


# ── Plan Activation Tests ───────────────────────────────────────────────


class TestPlanActivation:
    """Verify plan activation and deactivation."""

    @patch("app.db.firestore.firestore_save_org")
    def test_activate_valid_plan(self, mock_firestore):
        org = _create_mock_org(subscription_plan="free", subscription_status="unpaid")
        svc, db = _create_service(org)

        result = svc.activate_plan("test-org-1", "design-partner", subscription_id="sub_123")
        assert result is True
        assert org.subscription_plan == "design-partner"
        assert org.subscription_status == "active"
        assert org.subscription_id == "sub_123"
        db.commit.assert_called_once()

    def test_activate_invalid_plan(self):
        org = _create_mock_org()
        svc, db = _create_service(org)
        result = svc.activate_plan("test-org-1", "nonexistent-plan")
        assert result is False
        db.commit.assert_not_called()

    def test_activate_missing_org(self):
        svc, db = _create_service(None)
        result = svc.activate_plan("nonexistent", "growth")
        assert result is False
        db.commit.assert_not_called()

    @patch("app.db.firestore.firestore_save_org")
    def test_deactivate(self, mock_firestore):
        org = _create_mock_org(subscription_plan="growth", subscription_status="active")
        svc, db = _create_service(org)

        result = svc.deactivate("test-org-1")
        assert result is True
        assert org.subscription_status == "canceled"
        db.commit.assert_called_once()
