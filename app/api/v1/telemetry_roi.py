"""
Telemetry ROI Metrics API router.

Exposes:
  GET /api/v1/telemetry/roi-metrics
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.auth import require_auth, User
from app.services.telemetry import TelemetryVerificationService

router = APIRouter(prefix="/telemetry", tags=["telemetry-roi"])
logger = logging.getLogger("airs.api.telemetry_roi")


@router.get(
    "/roi-metrics",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get Telemetry ROI Metrics",
    description="Calculate base audit hours, automated hours, audit hours saved, and revenue protected based on continuous telemetry sync.",
)
async def get_telemetry_roi_metrics(
    org_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
) -> Dict[str, Any]:
    """Calculate and return live telemetry ROI metrics for the organization."""
    from app.models.organization import Organization

    resolved_org_id = org_id
    if not resolved_org_id:
        try:
            # Fallback to the first organization owned or in the system
            org = db.query(Organization).first()
            if org:
                resolved_org_id = org.id
        except Exception as exc:
            logger.error(f"Error resolving default organization for ROI metrics: {exc}")

    if not resolved_org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No organization found. Please configure an organization first.",
        )

    service = TelemetryVerificationService(db)
    try:
        metrics = service.calculate_roi_metrics(resolved_org_id)
        return metrics
    except Exception as exc:
        logger.error(f"Failed to calculate ROI metrics for org {resolved_org_id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error while calculating telemetry ROI metrics.",
        )
