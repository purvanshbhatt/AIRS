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

from app.services.billing.entitlements import EntitlementService, PLAN_ENTITLEMENTS, FOUNDING_PLANS

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
        In production, direct activation is disabled to enforce Stripe checkout.
        """
        from app.core.config import settings, Environment
        is_prod = (settings.ENV == Environment.PROD) or (settings.ENVIRONMENT == "production")
        if is_prod and not (settings.is_admin_email(activated_by) or settings.is_admin_uid(activated_by)):
            return {
                "success": False,
                "error": "Direct activation is disabled in production. Checkout must be completed through Stripe.",
            }

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

    # Plans whose price IDs are required in production
    _PRICE_SETTING_FOR_PLAN = {
        "founding-sysadmin": "STRIPE_PRICE_DESIGN_PARTNER",
        "solo-it": "STRIPE_PRICE_DESIGN_PARTNER",
        "starter": "STRIPE_PRICE_DESIGN_PARTNER",
        "design-partner": "STRIPE_PRICE_DESIGN_PARTNER",
        "growth": "STRIPE_PRICE_GROWTH",
        "enterprise": "STRIPE_PRICE_ENTERPRISE",
    }
    # Fallback monthly amounts (cents) for non-production environments only
    _FALLBACK_UNIT_AMOUNT = {
        "founding-sysadmin": 14900,
        "solo-it": 19900,
        "starter": 19900,
        "design-partner": 19900,
        "growth": 39900,
        "enterprise": 499900,
    }

    def build_checkout_payload(
        self,
        org_id: str,
        plan: str,
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None,
        customer_id: Optional[str] = None,
        allow_price_data_fallback: bool = False,
    ) -> dict:
        """Assemble the form-encoded Stripe Checkout Session payload.

        Invoice-friendly by default so a practice manager or partner can
        expense the subscription: billing address and tax ID are collected,
        the Stripe Customer carries the firm's legal name/address, promotion
        codes are accepted, and an optional card-free trial gives the solo
        admin an approval window. Raises ValueError when the price ID is
        missing and dynamic pricing is not allowed (production).
        """
        from app.core.config import settings

        price_id = getattr(settings, self._PRICE_SETTING_FOR_PLAN[plan], None)
        if plan == "founding-sysadmin":
            # Founding seats carry their own locked price when configured.
            price_id = getattr(settings, "STRIPE_PRICE_FOUNDING_SYSADMIN", None) or price_id
        payload = {
            "mode": "subscription",
            "success_url": success_url if "{CHECKOUT_SESSION_ID}" in success_url else f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": cancel_url,
            "client_reference_id": org_id,
            "metadata[org_id]": org_id,
            "metadata[plan]": plan,
            "subscription_data[metadata][org_id]": org_id,
            "subscription_data[metadata][plan]": plan,
            "billing_address_collection": "required",
            "tax_id_collection[enabled]": "true",
            "allow_promotion_codes": "true",
        }

        if customer_id:
            # Reuse the existing Stripe Customer so invoices, portal and
            # subscriptions stay on one record; let Checkout refresh its
            # legal name and address.
            payload["customer"] = customer_id
            payload["customer_update[name]"] = "auto"
            payload["customer_update[address]"] = "auto"
        else:
            payload["customer_creation"] = "always"
            if customer_email:
                payload["customer_email"] = customer_email

        trial_days = int(getattr(settings, "STRIPE_TRIAL_DAYS", 0) or 0)
        if trial_days > 0:
            payload["subscription_data[trial_period_days]"] = str(trial_days)
            # Card-free trial: the admin can connect systems and forward the
            # readiness report to an approver before any payment method exists.
            payload["payment_method_collection"] = "if_required"

        if getattr(settings, "STRIPE_AUTOMATIC_TAX", False):
            payload["automatic_tax[enabled]"] = "true"

        if price_id:
            payload["line_items[0][price]"] = price_id
            payload["line_items[0][quantity]"] = "1"
        elif allow_price_data_fallback:
            unit_amount = self._FALLBACK_UNIT_AMOUNT[plan]
            payload["line_items[0][price_data][currency]"] = "usd"
            payload["line_items[0][price_data][product_data][name]"] = f"ResilAI {plan.replace('-', ' ').title()} Subscription"
            payload["line_items[0][price_data][unit_amount]"] = str(unit_amount)
            payload["line_items[0][price_data][recurring][interval]"] = "month"
            payload["line_items[0][quantity]"] = "1"
        else:
            raise ValueError(
                f"{self._PRICE_SETTING_FOR_PLAN[plan]} is not configured; dynamic price_data is disabled in production"
            )
        return payload

    async def create_checkout_session(
        self,
        org_id: str,
        plan: str,
        success_url: str,
        cancel_url: str,
        customer_email: Optional[str] = None,
        org=None,
    ) -> dict:
        """Create a Stripe Checkout Session for subscription purchase.

        ``org`` may be passed by the route (already ownership-checked) to avoid
        a second lookup; otherwise it is loaded here.

        In production with STRIPE_SECRET_KEY, creates an authentic Stripe checkout session.
        In staging/local without keys, returns a mock checkout session structure for testing.
        """
        from app.core.config import settings, Environment
        import httpx

        if plan not in PLAN_ENTITLEMENTS or plan == "free":
            return {
                "success": False,
                "error": f"Invalid plan for checkout: {plan}. Valid paid plans: founding-sysadmin, design-partner, growth, enterprise",
            }

        if org is None:
            try:
                org = self._entitlements._get_org(org_id)
            except Exception as exc:
                logger.warning("Org lookup failed during checkout for %s: %s", org_id, exc)
                org = None
        if org is None:
            return {"success": False, "error": "Organization not found"}

        # One subscription per organization: an active org manages its plan
        # through the billing portal instead of creating a second subscription.
        current_status = getattr(org, "subscription_status", "unpaid") or "unpaid"
        if current_status in ("active", "trialing", "past_due") and getattr(org, "subscription_id", None):
            return {
                "success": False,
                "error": "This organization already has a subscription. Use the billing portal to change plans or update payment details.",
                "code": "SUBSCRIPTION_EXISTS",
            }

        # Founding seats are capped; enforce from the database, never from UI copy.
        if plan in FOUNDING_PLANS:
            seats = self._entitlements.founding_seats()
            if seats["sold_out"]:
                return {
                    "success": False,
                    "error": "All founding-sysadmin seats are claimed. Choose the Growth plan or contact us.",
                    "code": "FOUNDING_SOLD_OUT",
                }

        is_prod = (settings.ENV == Environment.PROD) or (settings.ENVIRONMENT == "production")

        # Production with Stripe Secret Key
        if settings.STRIPE_SECRET_KEY:
            try:
                payload = self.build_checkout_payload(
                    org_id=org_id,
                    plan=plan,
                    success_url=success_url,
                    cancel_url=cancel_url,
                    customer_email=customer_email,
                    customer_id=getattr(org, "customer_id", None),
                    allow_price_data_fallback=not is_prod,
                )
            except ValueError as exc:
                logger.error("Checkout misconfiguration: %s", exc)
                return {"success": False, "error": str(exc)}

            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        "https://api.stripe.com/v1/checkout/sessions",
                        data=payload,
                        headers={
                            "Authorization": f"Bearer {settings.STRIPE_SECRET_KEY}",
                        },
                    )

                if resp.status_code not in (200, 201):
                    err_json = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                    err_msg = err_json.get("error", {}).get("message", resp.text)
                    logger.error("Stripe Checkout creation failed: %s", err_msg)
                    return {"success": False, "error": f"Stripe checkout creation failed: {err_msg}"}

                session_data = resp.json()
                return {
                    "success": True,
                    "checkout_url": session_data.get("url"),
                    "session_id": session_data.get("id"),
                    "plan": plan,
                    "org_id": org_id,
                }
            except Exception as exc:
                logger.exception("Error calling Stripe Checkout API: %s", exc)
                return {"success": False, "error": f"Failed to contact Stripe: {str(exc)}"}

        # Staging / Local fallback when STRIPE_SECRET_KEY is not configured
        if is_prod:
            return {
                "success": False,
                "error": "STRIPE_SECRET_KEY is not configured in production environment.",
            }

        mock_session_id = f"mock-cs-{org_id}-{plan}-{int(datetime.now(timezone.utc).timestamp())}"
        mock_checkout_url = f"{success_url}?session_id={mock_session_id}&plan={plan}&mock=true"
        return {
            "success": True,
            "checkout_url": mock_checkout_url,
            "session_id": mock_session_id,
            "plan": plan,
            "org_id": org_id,
            "mock": True,
        }

    async def create_portal_session(self, org_id: str, return_url: str) -> dict:
        """Create a Stripe Customer Portal session (invoices, card update,
        cancel, plan change). Requires the org to have a Stripe customer."""
        from app.core.config import settings
        import httpx

        org = self._entitlements._get_org(org_id)
        if org is None:
            return {"success": False, "error": "Organization not found"}
        customer_id = getattr(org, "customer_id", None)
        if not customer_id:
            return {
                "success": False,
                "error": "No billing account exists for this organization yet. Start a plan first.",
                "code": "NO_CUSTOMER",
            }
        if not settings.STRIPE_SECRET_KEY:
            return {
                "success": False,
                "error": "Billing portal is not configured (STRIPE_SECRET_KEY missing).",
                "code": "PORTAL_NOT_CONFIGURED",
            }

        payload = {"customer": customer_id, "return_url": return_url}
        if getattr(settings, "STRIPE_PORTAL_CONFIGURATION", None):
            payload["configuration"] = settings.STRIPE_PORTAL_CONFIGURATION
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    "https://api.stripe.com/v1/billing_portal/sessions",
                    data=payload,
                    headers={"Authorization": f"Bearer {settings.STRIPE_SECRET_KEY}"},
                )
            if resp.status_code not in (200, 201):
                err_json = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                err_msg = err_json.get("error", {}).get("message", resp.text)
                logger.error("Stripe portal session failed: %s", err_msg)
                return {"success": False, "error": f"Stripe portal session failed: {err_msg}"}
            data = resp.json()
            return {"success": True, "url": data.get("url"), "org_id": org_id}
        except Exception as exc:
            logger.exception("Error calling Stripe billing portal API: %s", exc)
            return {"success": False, "error": f"Failed to contact Stripe: {str(exc)}"}

    @staticmethod
    def verify_stripe_signature(
        payload_bytes: bytes,
        sig_header: str,
        secret: str,
        tolerance: int = 300,
    ) -> bool:
        """Verify Stripe webhook signature according to Stripe's HMAC-SHA256 specification.

        Header format: t=timestamp,v1=signature[,v0=signature]
        Payload: f"{timestamp}.{payload_str}"
        """
        import hmac
        import hashlib
        import time

        if not sig_header or not secret:
            return False

        try:
            elements = sig_header.split(",")
            timestamp = None
            signatures = []
            for item in elements:
                parts = item.strip().split("=", 1)
                if len(parts) == 2:
                    k, v = parts[0].strip(), parts[1].strip()
                    if k == "t":
                        timestamp = v
                    elif k == "v1":
                        signatures.append(v)

            if not timestamp or not signatures:
                logger.warning("Stripe signature header missing timestamp or v1 signatures")
                return False

            # Check timestamp freshness to prevent replay attacks
            ts_int = int(timestamp)
            current_time = int(time.time())
            if abs(current_time - ts_int) > tolerance:
                logger.warning("Stripe signature timestamp outside tolerance window: %s vs %s", ts_int, current_time)
                return False

            # Compute expected HMAC-SHA256 signature
            signed_payload = f"{timestamp}.".encode("utf-8") + payload_bytes
            expected_sig = hmac.new(
                secret.encode("utf-8"),
                signed_payload,
                hashlib.sha256,
            ).hexdigest()

            # Compare against all v1 signatures in header
            for sig in signatures:
                if hmac.compare_digest(sig, expected_sig):
                    return True

            logger.warning("Stripe signature verification failed: no signature matched expected digest")
            return False
        except Exception as exc:
            logger.error("Exception during Stripe signature verification: %s", exc)
            return False

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
        org_id = data.get("metadata", {}).get("org_id") or data.get("client_reference_id")
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
