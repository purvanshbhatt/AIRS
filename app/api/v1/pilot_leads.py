"""
Enterprise Pilot Lead intake endpoint.

POST /api/v1/pilot-leads

Accepts the extended Enterprise Pilot Programme intake form and stores
it to the pilot_requests table.  Unlike the legacy /api/pilot-request
endpoint this version captures contact_name, industry, company_size, and
ai_usage_description to support GTM outreach and qualification scoring.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.pilot_request import PilotRequest
from app.schemas.pilot import EnterprisePilotLeadCreate, PilotRequestResponse

router = APIRouter()


@router.post(
    "/pilot-leads",
    response_model=PilotRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Enterprise Pilot Lead",
    description=(
        "Enterprise Pilot Programme intake form.  Stores the lead in the "
        "pilot_requests table and returns the created record.  No auth required "
        "so that it can be called from the public /pilot landing page."
    ),
    tags=["pilot"],
)
async def create_enterprise_pilot_lead(
    data: EnterprisePilotLeadCreate,
    db: Session = Depends(get_db),
):
    """
    POST /api/v1/pilot-leads

    Public endpoint — no authentication required.
    Rate-limited at the Cloud Run / reverse-proxy layer in production.
    """
    lead = PilotRequest(
        company_name=data.company_name,
        contact_name=data.contact_name,
        email=str(data.email),
        team_size=data.team_size or "",
        current_security_tools=data.current_security_tools,
        industry=data.industry,
        company_size=data.company_size,
        ai_usage_description=data.ai_usage_description,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead
