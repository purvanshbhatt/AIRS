"""
Roadmap schemas.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class RoadmapItemBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: str = Field("todo", pattern="^(todo|in_progress|done)$")
    priority: str = Field("medium", pattern="^(high|medium|low)$")
    effort: str = Field("medium", pattern="^(high|medium|low)$")
    due_date: Optional[datetime] = None
    assessment_id: Optional[str] = None

class RoadmapItemCreate(RoadmapItemBase):
    pass

class RoadmapItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(todo|in_progress|done)$")
    priority: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    effort: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    due_date: Optional[datetime] = None

class RoadmapItemResponse(RoadmapItemBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class RoadmapListResponse(BaseModel):
    items: List[RoadmapItemResponse]
    total: int
