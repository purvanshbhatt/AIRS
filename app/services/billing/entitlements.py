"""
ResilAI Entitlement Engine.

Defines subscription plans, their entitlements, and the service that
resolves what an organization is allowed to do based on its subscription.

Architectural rule:
    Authentication answers: "Who are you?"
    Authorization answers: "What are you allowed to do?"
    Entitlement answers: "What has your organization paid for?"

All three are required. This module handles entitlements.
"""
from __future__ import annotations

import enum
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger("airs.billing.entitlements")


class Entitlement(str, enum.Enum):
    """Capabilities that can be gated by subscription plan."""
    # Free tier
    DEMO_ACCESS = "demo_access"
    SIMULATED_DATA = "simulated_data"
    PUBLIC_PRODUCT_PREVIEW = "public_product_preview"
    ACCOUNT_MANAGEMENT = "account_management"

    # Paid: Starter / Design Partner
    REAL_ORGANIZATION = "real_organization"
    TELEMETRY_INGESTION = "telemetry_ingestion"
    EVIDENCE_COLLECTION = "evidence_collection"
    READINESS_SCORING = "readiness_scoring"
    CONNECTORS_MANAGE = "connectors_manage"
    EXECUTIVE_REPORTS = "executive_reports"

    # Paid: Growth
    API_KEYS = "api_keys"
    WEBHOOKS = "webhooks"
    ADVANCED_REPORTING = "advanced_reporting"
    ADDITIONAL_USERS = "additional_users"

    # Paid: Enterprise
    ADVANCED_INTEGRATIONS = "advanced_integrations"
    ENTERPRISE_CONTROLS = "enterprise_controls"
    CUSTOM_FRAMEWORKS = "custom_frameworks"


# ── Plan → Entitlement Mapping ──────────────────────────────────────
# Derived from the live pricing page (frontend/src/pages/Pricing.tsx)
# and the user's access model specification.

_FREE_ENTITLEMENTS = [
    Entitlement.DEMO_ACCESS,
    Entitlement.SIMULATED_DATA,
    Entitlement.PUBLIC_PRODUCT_PREVIEW,
    Entitlement.ACCOUNT_MANAGEMENT,
]

_DESIGN_PARTNER_ENTITLEMENTS = _FREE_ENTITLEMENTS + [
    Entitlement.REAL_ORGANIZATION,
    Entitlement.TELEMETRY_INGESTION,
    Entitlement.EVIDENCE_COLLECTION,
    Entitlement.READINESS_SCORING,
    Entitlement.CONNECTORS_MANAGE,
    Entitlement.EXECUTIVE_REPORTS,
]

_GROWTH_ENTITLEMENTS = _DESIGN_PARTNER_ENTITLEMENTS + [
    Entitlement.API_KEYS,
    Entitlement.WEBHOOKS,
    Entitlement.ADVANCED_REPORTING,
    Entitlement.ADDITIONAL_USERS,
]

_ENTERPRISE_ENTITLEMENTS = _GROWTH_ENTITLEMENTS + [
    Entitlement.ADVANCED_INTEGRATIONS,
    Entitlement.ENTERPRISE_CONTROLS,
    Entitlement.CUSTOM_FRAMEWORKS,
]

PLAN_ENTITLEMENTS: Dict[str, List[Entitlement]] = {
    "free": _FREE_ENTITLEMENTS,
    "design-partner": _DESIGN_PARTNER_ENTITLEMENTS,
    "growth": _GROWTH_ENTITLEMENTS,
    "enterprise": _ENTERPRISE_ENTITLEMENTS,
}

# Active subscription statuses that unlock paid entitlements
_ACTIVE_STATUSES = {"active", "trialing"}


class EntitlementService:
    """Resolves organization entitlements from subscription state.

    Usage:
        svc = EntitlementService(db)
        if not svc.has(org_id, Entitlement.CONNECTORS_MANAGE):
            raise HTTPException(402, ...)
    """

    def __init__(self, db: Session):
        self.db = db

    def _get_org(self, org_id: str):
        from app.models.organization import Organization
        return self.db.query(Organization).filter(Organization.id == org_id).first()

    def is_exempt_org(self, org_id: str) -> bool:
        """Check if an organization is owned by or associated with an administrator account."""
        from app.core.config import settings
        org = self._get_org(org_id)
        if not org:
            return False
        owner_uid = getattr(org, "owner_uid", None)
        created_by = getattr(org, "created_by", None)
        if isinstance(owner_uid, str) and settings.is_admin_email(owner_uid):
            return True
        if isinstance(created_by, str) and settings.is_admin_email(created_by):
            return True
        return False

    def get_effective_plan(self, org_id: str) -> str:
        """Return the plan the org is effectively on right now.

        If subscription_status is not active/trialing, falls back to 'free'
        regardless of what subscription_plan says.
        """
        if self.is_exempt_org(org_id):
            return "enterprise"

        org = self._get_org(org_id)
        if not org:
            return "free"

        # Demo organizations are always on the free/demo tier
        if getattr(org, "org_mode", None) == "demo":
            return "free"

        plan = getattr(org, "subscription_plan", "free") or "free"
        status = getattr(org, "subscription_status", "unpaid") or "unpaid"

        if status in _ACTIVE_STATUSES:
            return plan

        # Unpaid / canceled / past_due -> free
        return "free"

    def has(self, org_id: str, entitlement: Entitlement) -> bool:
        """Check if the organization has a specific entitlement."""
        if self.is_exempt_org(org_id):
            return True
        plan = self.get_effective_plan(org_id)
        allowed = PLAN_ENTITLEMENTS.get(plan, _FREE_ENTITLEMENTS)
        return entitlement in allowed

    def get_capabilities(self, org_id: str) -> Dict[str, Any]:
        """Return the full capability map for an organization.

        This is the payload returned by GET /api/orgs/{org_id}/capabilities
        and consumed by the frontend to determine what to show/hide.
        """
        if self.is_exempt_org(org_id):
            return {
                "plan": "enterprise",
                "status": "exempt",
                "is_paid": False,
                "is_exempt": True,
                "exemption_type": "admin_test",
                "entitlements": {e.value: True for e in Entitlement},
            }

        org = self._get_org(org_id)
        if not org:
            return {
                "plan": "free",
                "status": "unpaid",
                "is_paid": False,
                "is_exempt": False,
                "exemption_type": None,
                "entitlements": {e.value: (e in _FREE_ENTITLEMENTS) for e in Entitlement},
            }

        plan = self.get_effective_plan(org_id)
        status = getattr(org, "subscription_status", "unpaid") or "unpaid"
        allowed = PLAN_ENTITLEMENTS.get(plan, _FREE_ENTITLEMENTS)

        return {
            "plan": plan,
            "status": status,
            "is_paid": status in _ACTIVE_STATUSES,
            "is_exempt": False,
            "exemption_type": None,
            "entitlements": {e.value: (e in allowed) for e in Entitlement},
        }

    def activate_plan(self, org_id: str, plan: str, subscription_id: str = None,
                      customer_id: str = None, period_end=None) -> bool:
        """Activate or change a subscription plan for an organization.

        Called by checkout completion or billing webhook handlers.
        """
        org = self._get_org(org_id)
        if not org:
            logger.error("Cannot activate plan: org %s not found", org_id)
            return False

        if plan not in PLAN_ENTITLEMENTS:
            logger.error("Invalid plan '%s' for org %s", plan, org_id)
            return False

        org.subscription_plan = plan
        org.subscription_status = "active"
        if subscription_id:
            org.subscription_id = subscription_id
        if customer_id:
            org.customer_id = customer_id
        if period_end:
            org.current_period_end = period_end

        self.db.commit()

        # Dual-write to Firestore for Cloud Run cold-start persistence
        try:
            from app.db.firestore import firestore_save_org
            firestore_save_org(org)
        except Exception as exc:
            logger.warning("Firestore sync failed after plan activation for org %s: %s", org_id, exc)

        logger.info("Activated plan '%s' for org %s (subscription=%s)",
                    plan, org_id, subscription_id or "manual")
        return True

    def deactivate(self, org_id: str) -> bool:
        """Deactivate an organization's subscription (e.g. on cancellation)."""
        org = self._get_org(org_id)
        if not org:
            return False

        org.subscription_status = "canceled"
        self.db.commit()

        try:
            from app.db.firestore import firestore_save_org
            firestore_save_org(org)
        except Exception as exc:
            logger.warning("Firestore sync failed after deactivation for org %s: %s", org_id, exc)

        logger.info("Deactivated subscription for org %s", org_id)
        return True
