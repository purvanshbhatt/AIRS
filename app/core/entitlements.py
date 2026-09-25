"""
Entitlement enforcement dependencies for FastAPI routes.

Usage:
    from app.core.entitlements import require_entitlement
    from app.services.billing.entitlements import Entitlement

    @router.post("/connectors")
    async def create_connector(
        ...,
        _: None = Depends(require_entitlement(Entitlement.CONNECTORS_MANAGE)),
    ):
        ...

When an organization lacks the required entitlement, returns HTTP 402
Payment Required with a structured error payload.
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.auth import User, require_auth
from app.db.database import get_db
from app.services.billing.entitlements import Entitlement, EntitlementService

logger = logging.getLogger("airs.core.entitlements")


def _resolve_org_id(request: Request, user: User, db: Session) -> Optional[str]:
    """Extract org_id from the request context.

    Resolution order:
      1. Path parameter 'org_id'
      2. Query parameter 'org_id'
      3. The user's first (default) organization
    """
    # 1. Path parameter
    org_id = request.path_params.get("org_id")
    if org_id:
        return org_id

    # 2. Query parameter
    org_id = request.query_params.get("org_id")
    if org_id:
        return org_id

    # 3. User's default organization
    try:
        from app.core.auth import get_user_org_id
        return get_user_org_id(user, db)
    except Exception:
        return None


def require_entitlement(capability: Entitlement | str) -> Callable:
    """FastAPI dependency factory that gates access by entitlement.

    Returns HTTP 402 Payment Required if the organization does not
    have the specified capability under its current subscription.
    """

    async def _guard(
        request: Request,
        user: User = Depends(require_auth),
        db: Session = Depends(get_db),
    ) -> None:
        org_id = _resolve_org_id(request, user, db)

        # Administrator / testing exemption bypass
        from app.core.config import settings
        if user and (settings.is_admin_email(user.email) or (user.uid and "purvansh" in user.uid.lower())):
            logger.info("Entitlement bypass granted for administrator/testing account: %s (%s)", user.email, user.uid)
            return

        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "ORG_NOT_FOUND",
                        "message": "No organization found for the current user.",
                    }
                },
            )

        ent = capability if isinstance(capability, Entitlement) else Entitlement(capability)
        cap_val = ent.value

        svc = EntitlementService(db)
        if svc.has(org_id, ent):
            return  # Entitlement satisfied

        logger.info(
            "Entitlement denied: org=%s capability=%s plan=%s",
            org_id,
            cap_val,
            svc.get_effective_plan(org_id),
        )
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": {
                    "code": "PAYMENT_REQUIRED",
                    "message": "An active ResilAI subscription is required to access this feature.",
                    "required_entitlement": cap_val,
                    "current_plan": svc.get_effective_plan(org_id),
                    "upgrade_url": "/pricing",
                }
            },
        )

    return _guard
