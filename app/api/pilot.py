"""Public pilot request API endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.pilot_request import PilotRequest
from app.schemas.pilot import PilotRequestCreate, PilotRequestResponse

router = APIRouter()


@router.post("/pilot-request", response_model=PilotRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_pilot_request(
    data: PilotRequestCreate,
    db: Session = Depends(get_db),
):
    request_row = PilotRequest(
        company_name=data.company_name,
        team_size=data.team_size,
        current_security_tools=data.current_security_tools,
        email=str(data.email),
    )
    db.add(request_row)
    db.commit()
    db.refresh(request_row)
    return request_row

