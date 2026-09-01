"""
Intelligence API Router — Version drift monitoring and manual sync triggers.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import User, require_auth, get_user_org_id
from app.core.demo_guard import require_writable
from app.db.database import get_db
from app.services.intelligence import IntelligenceService

logger = logging.getLogger("airs.api.v1.intelligence")

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


# =============================================================================
# Schemas
# =============================================================================

class SoftwareCatalogResponse(BaseModel):
    """Catalog entry representing a monitored package's version drift status."""
    id: str
    org_id: str
    vendor: Optional[str] = None
    product: str
    current_version: Optional[str] = None
    latest_version: Optional[str] = None
    latest_release_date: Optional[str] = None
    advisory_url: Optional[str] = None
    source: Optional[str] = None
    severity: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SyncResponse(BaseModel):
    """Response returned after executing an on-demand drift audit sweep."""
    status: str
    drift_detected: int


# =============================================================================
# Routes
# =============================================================================

@router.get(
    "/latest-versions",
    response_model=List[SoftwareCatalogResponse],
    summary="Get latest versions and version drift",
    description="Returns the software drift inventory for the authenticated user's organization.",
)
async def get_latest_versions(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = get_user_org_id(user, db)
    service = IntelligenceService(db, org_id)
    try:
        items = service.get_latest_versions()
        return items
    except Exception as exc:
        logger.error("Failed retrieving software version drift: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed retrieving software catalog versions.",
        )


@router.post(
    "/sync",
    response_model=SyncResponse,
    summary="Trigger intelligence sync",
    description="Triggers an immediate software version intelligence fetch and drift check.",
)
async def trigger_sync(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
    _: None = Depends(require_writable),
):
    org_id = get_user_org_id(user, db)
    service = IntelligenceService(db, org_id)
    try:
        drift_count = await service.sync_intelligence_and_detect_drift()
        return SyncResponse(status="success", drift_detected=drift_count)
    except Exception as exc:
        logger.error("Failed running manual intelligence sync: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync execution failed: {str(exc)}",
        )
