"""External integration endpoints (API key secured, rate-limited)."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.core.api_key_auth import get_api_key_dependency
from app.db.database import get_db
from app.models.api_key import ApiKey
from app.schemas.integrations import ExternalLatestScoreResponse
from app.services.integrations import build_external_latest_score_payload

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/external/latest-score", response_model=ExternalLatestScoreResponse)
@limiter.limit("30/minute")
async def get_latest_score_for_external(
    request: Request,
    api_key: ApiKey = Depends(get_api_key_dependency(required_scopes=["scores:read"])),
    db: Session = Depends(get_db),
):
    payload = build_external_latest_score_payload(db, api_key.owner_org_id)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No completed assessment found for this organization",
        )
    return payload