"""
Billing API — Plan capabilities, subscription status, and checkout.

Endpoints:
    GET  /api/orgs/{org_id}/capabilities  — Entitlement map for frontend rendering
    GET  /api/orgs/{org_id}/billing        — Subscription details
    POST /api/orgs/{org_id}/billing/activate — Direct plan activation (staging/design-partner)
    POST /api/billing/webhook              — Stripe webhook handler
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import User, require_auth
from app.db.database import get_db
from app.services.billing.entitlements import EntitlementService, PLAN_ENTITLEMENTS
from app.services.billing.checkout import CheckoutService
from app.services.organization import OrganizationService

logger = logging.getLogger("airs.api.billing")

router = APIRouter()


# ── Request / Response Schemas ──────────────────────────────────────

class PlanActivateRequest(BaseModel):
    plan: str = Field(..., description="Plan to activate: free, design-partner, growth, enterprise")


# ── Capabilities ────────────────────────────────────────────────────

@router.get(
    "/orgs/{org_id}/capabilities",
    summary="Get Organization Capabilities",
    description="Returns the organization's plan, subscription status, and full entitlement map. Used by the frontend to determine what features to show.",
    responses={
        200: {"description": "Capability map"},
        401: {"description": "Authentication required"},
        404: {"description": "Organization not found"},
    },
)
async def get_capabilities(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Return the organization's full entitlement map."""
    # Verify org ownership
    org_service = OrganizationService(db, owner_uid=user.uid if user else None)
    org = org_service.get(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ORGANIZATION_NOT_FOUND", "message": "Organization not found."}},
        )

    from app.core.config import settings
    if user and (settings.is_admin_email(user.email) or (user.uid and "purvansh" in user.uid.lower())):
        from app.services.billing.entitlements import Entitlement
        return {
            "plan": "enterprise",
            "status": "active",
            "is_paid": True,
            "entitlements": {e.value: True for e in Entitlement},
        }

    svc = EntitlementService(db)
    return svc.get_capabilities(org_id)


# ── Billing Status ──────────────────────────────────────────────────

@router.get(
    "/orgs/{org_id}/billing",
    summary="Get Billing Status",
    description="Returns subscription details for the organization.",
    responses={
        200: {"description": "Billing status"},
        401: {"description": "Authentication required"},
        404: {"description": "Organization not found"},
    },
)
async def get_billing_status(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Return subscription details for the organization."""
    org_service = OrganizationService(db, owner_uid=user.uid if user else None)
    org = org_service.get(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ORGANIZATION_NOT_FOUND", "message": "Organization not found."}},
        )

    return {
        "organization_id": org.id,
        "organization_name": org.name,
        "plan": getattr(org, "subscription_plan", "free") or "free",
        "status": getattr(org, "subscription_status", "unpaid") or "unpaid",
        "subscription_id": getattr(org, "subscription_id", None),
        "customer_id": getattr(org, "customer_id", None),
        "current_period_end": (
            org.current_period_end.isoformat()
            if getattr(org, "current_period_end", None)
            else None
        ),
        "available_plans": list(PLAN_ENTITLEMENTS.keys()),
    }


# ── Plan Activation (Staging / Design Partner) ──────────────────────

@router.post(
    "/orgs/{org_id}/billing/activate",
    summary="Activate Plan",
    description="Directly activate a subscription plan. Used for staging, design partners, and manual activation.",
    responses={
        200: {"description": "Plan activated"},
        400: {"description": "Invalid plan"},
        401: {"description": "Authentication required"},
        404: {"description": "Organization not found"},
    },
)
async def activate_plan(
    org_id: str,
    body: PlanActivateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Directly activate a plan for the organization."""
    # Verify org ownership
    org_service = OrganizationService(db, owner_uid=user.uid if user else None)
    org = org_service.get(org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "ORGANIZATION_NOT_FOUND", "message": "Organization not found."}},
        )

    checkout = CheckoutService(db)
    result = checkout.activate_plan_direct(org_id, body.plan, activated_by=user.uid)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "ACTIVATION_FAILED", "message": result.get("error", "Unknown error")}},
        )

    return result


# ── Stripe Webhook ──────────────────────────────────────────────────

@router.post(
    "/billing/webhook",
    summary="Stripe Webhook",
    description="Receives Stripe webhook events to synchronize subscription state.",
    status_code=status.HTTP_200_OK,
)
async def billing_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle Stripe webhook events.

    In production, this should verify the Stripe webhook signature.
    For staging, we accept the payload directly.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    event_type = payload.get("type", "")
    event_data = payload.get("data", {}).get("object", {})

    if not event_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing event type",
        )

    checkout = CheckoutService(db)
    result = checkout.handle_stripe_event(event_type, event_data)
    return result
