"""Schemas for audit log APIs."""

from datetime import datetime

from pydantic import BaseModel


class AuditEventResponse(BaseModel):
    id: str
    org_id: str
    action: str
    actor: str
    timestamp: datetime

    class Config:
        from_attributes = True

