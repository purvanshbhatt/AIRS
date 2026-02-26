"""
Pydantic schemas for Framework Registry.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FrameworkRegistryResponse(BaseModel):
    """Response schema for a canonical framework."""
    id: str
    name: str
    full_name: str
    category: str                  # "regulatory", "contractual", "voluntary"
    version: Optional[str] = None
    description: Optional[str] = None
    reference_url: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FrameworkRegistryListResponse(BaseModel):
    """List response for framework registry."""
    frameworks: List[FrameworkRegistryResponse] = []
    total: int = 0
