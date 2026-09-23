"""
Checkout and plan activation service.

In staging/development, supports direct plan activation without a billing
provider. In production, integrates with Stripe via webhook synchronization.

The billing provider integration is designed to be swappable:
- Direct activation (staging/dev)
- Stripe (production)
- Future: other providers
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.services.billing.entitlements import EntitlementService, PLAN_ENTITLEMENTS

logger = logging.getLogger("airs.billing.checkout")


class CheckoutService:
    """Manages plan selection, checkout, and activation."""

    def __init__(self, db: Session):
        self.db = db
        self._entitlements = EntitlementService(db)

    def activate_plan_direct(self, org_id: str, plan: str,
                             activated_by: str = "system") -> dict:
        """Directly activate a plan for an organization.

        Used in staging/development and for design partner manual activation.
        In production, plan activation flows through billing webhooks.
        """
        if plan not in PLAN_ENTITLEMENTS:
            return {
                "success": False,
                "error": f"Invalid plan: {plan}. Valid plans: {list(PLAN_ENTITLEMENTS.keys())}",
            }

        # Set a 1-year default period for direct activation
        period_end = datetime.now(timezone.utc) + timedelta(days=365)

        success = self._entitlements.activate_plan(
            org_id=org_id,
            plan=plan,
            subscription_id=f"direct-{activated_by}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            period_end=period_end,
        )

        if success:
            # Record audit event
            try:
                from app.services.audit import record_audit_event
                record_audit_event(
                    self.db, org_id, "subscription.activated",
                    activated_by,
                    extra_details={"plan": plan, "method": "direct"},
                )
            except Exception:
                pass

            return {
                "success": True,
                "plan": plan,
                "status": "active",
                "current_period_end": period_end.isoformat(),
            }

        return {"success": False, "error": "Organization not found"}

    def handle_stripe_event(self, event_type: str, event_data: dict) -> dict:
        """Process Stripe webhook events to synchronize subscription state.

        Supported events:
        - checkout.session.completed
        - customer.subscription.created
        - customer.subscription.updated
        - customer.subscription.deleted
        - invoice.payment_succeeded
        - invoice.payment_failed
        """
        logger.info("Processing Stripe event: %s", event_type)

        if event_type == "checkout.session.completed":
            return self._handle_checkout_completed(event_data)
        elif event_type in ("customer.subscription.created", "customer.subscription.updated"):
            return self._handle_subscription_update(event_data)
        elif event_type == "customer.subscription.deleted":
            return self._handle_subscription_deleted(event_data)
        elif event_type == "invoice.payment_failed":
            return self._handle_payment_failed(event_data)
        else:
            logger.debug("Ignoring unhandled Stripe event: %s", event_type)
            return {"status": "ignored", "event_type": event_type}

    def _handle_checkout_completed(self, data: dict) -> dict:
        """Handle successful checkout — activate the subscription."""
        org_id = data.get("metadata", {}).get("org_id")
        plan = data.get("metadata", {}).get("plan", "design-partner")
        subscription_id = data.get("subscription")
        customer_id = data.get("customer")

        if not org_id:
            logger.error("Checkout completed but no org_id in metadata")
            return {"status": "error", "message": "Missing org_id in metadata"}

        success = self._entitlements.activate_plan(
            org_id=org_id,
            plan=plan,
            subscription_id=subscription_id,
            customer_id=customer_id,
        )
        return {"status": "activated" if success else "error", "org_id": org_id, "plan": plan}

    def _handle_subscription_update(self, data: dict) -> dict:
        """Handle subscription updates (plan changes, renewals)."""
        from app.models.organization import Organization

        subscription_id = data.get("id")
        status = data.get("status", "active")
        customer_id = data.get("customer")

        # Find org by subscription_id or customer_id
        org = (
            self.db.query(Organization)
            .filter(
                (Organization.subscription_id == subscription_id)
                | (Organization.customer_id == customer_id)
            )
            .first()
        )
        if not org:
            logger.warning("Subscription update for unknown org: sub=%s cust=%s",
                           subscription_id, customer_id)
            return {"status": "org_not_found"}

        # Map Stripe status to our status
        status_map = {
            "active": "active",
            "trialing": "trialing",
            "past_due": "past_due",
            "canceled": "canceled",
            "unpaid": "unpaid",
        }
        org.subscription_status = status_map.get(status, "unpaid")
        self.db.commit()

        try:
            from app.db.firestore import firestore_save_org
            firestore_save_org(org)
        except Exception:
            pass

        return {"status": "updated", "org_id": org.id}

    def _handle_subscription_deleted(self, data: dict) -> dict:
        """Handle subscription cancellation."""
        from app.models.organization import Organization

        subscription_id = data.get("id")
        customer_id = data.get("customer")

        org = (
            self.db.query(Organization)
            .filter(
                (Organization.subscription_id == subscription_id)
                | (Organization.customer_id == customer_id)
            )
            .first()
        )
        if not org:
            return {"status": "org_not_found"}

        self._entitlements.deactivate(org.id)
        return {"status": "deactivated", "org_id": org.id}

    def _handle_payment_failed(self, data: dict) -> dict:
        """Handle failed payment — set past_due status."""
        from app.models.organization import Organization

        customer_id = data.get("customer")
        org = self.db.query(Organization).filter(
            Organization.customer_id == customer_id
        ).first()

        if not org:
            return {"status": "org_not_found"}

        org.subscription_status = "past_due"
        self.db.commit()

        try:
            from app.db.firestore import firestore_save_org
            firestore_save_org(org)
        except Exception:
            pass

        logger.warning("Payment failed for org %s — set to past_due", org.id)
        return {"status": "past_due", "org_id": org.id}
