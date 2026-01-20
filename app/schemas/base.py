from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    class Config:
        from_attributes = True


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""
    
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


# ----- Standardized Error Response -----

class ErrorDetail(BaseModel):
    """Structured error detail for API responses."""
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    """Standardized error response wrapper."""
    error: ErrorDetail
