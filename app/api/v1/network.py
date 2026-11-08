"""
Network topology API — the real map of what is connected.

GET /api/v1/network/topology?org_id=...

Builds nodes and edges from the organization's connectors, discovered host
assets and recent telemetry (see ``app.services.network_topology``). Explicit
demo organizations replay the recorded demo telemetry and are readable
without a token, exactly like the clinic readiness endpoint; real
organizations require the signed-in owner.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import User, get_optional_user
from app.core.config import settings
from app.db.database import get_db
from app.services.clinic_engine.v2.pilot import OrgMode, PilotService
from app.services.network_topology import build_topology_for_org

logger = logging.getLogger("airs.api.network")

router = APIRouter(prefix="/network", tags=["network"])


def _is_explicit_demo(db: Session, org_id: str) -> bool:
    if org_id.startswith("demo-"):
        return True
    try:
        return PilotService(db).get_mode(org_id) == OrgMode.DEMO
    except Exception as exc:
        logger.debug("Org mode lookup failed for %s: %s", org_id, exc)
        return False


@router.get(
    "/topology",
    summary="Interactive network topology for an organization",
    description=(
        "Nodes and edges derived from connected systems, discovered assets and recent "
        "telemetry. Never synthetic for real organizations; empty when nothing is connected."
    ),
)
async def get_network_topology(
    org_id: str = Query(..., min_length=1, description="Organization ID (active workspace)"),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    org_id = org_id.strip()
    if not org_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Organization ID is required.")

    is_demo = _is_explicit_demo(db, org_id)

    if settings.is_auth_required and user is None and not is_demo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    if user is not None and not is_demo:
        from app.services.organization import OrganizationService
        try:
            org = OrganizationService(db, owner_uid=user.uid).get(org_id)
        except Exception as exc:
            logger.error("Organization access check failed for user=%s org=%s: %s", user.uid, org_id, exc)
            org = None
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "ORGANIZATION_NOT_FOUND",
                    "message": f"Organization '{org_id}' not found or access not authorized.",
                    "organization_id": org_id,
                },
            )

    topology = build_topology_for_org(db, org_id, demo=is_demo)
    topology["org_id"] = org_id
    topology["demo"] = is_demo
    return topology
