"""
AI Asset Inventory Pydantic Schemas — CRUD, versioning, and relationship models.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Request Schemas
# =============================================================================

class AIAssetCreateRequest(BaseModel):
    """Register a new AI asset in the inventory."""
    name: str = Field(..., description="Human-readable asset name")
    asset_type: str = Field(..., description="Asset type (model, agent, rag_pipeline, etc.)")
    description: Optional[str] = Field(None, description="Asset description")
    owner: Optional[str] = Field(None, description="Owner team or individual")
    business_criticality: str = Field("medium", description="Business impact tier")
    exposure_level: str = Field("internal", description="Data exposure classification")
    deployment_environment: Optional[str] = Field(None, description="Deployment target")
    lifecycle_stage: str = Field("development", description="Lifecycle stage")
    risk_tags: List[str] = Field(default_factory=list, description="Risk classification tags")
    associated_controls: List[str] = Field(default_factory=list, description="Mapped control IDs")
    metadata_extra: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AIAssetUpdateRequest(BaseModel):
    """Partial update of an AI asset (creates a version record)."""
    name: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    business_criticality: Optional[str] = None
    exposure_level: Optional[str] = None
    deployment_environment: Optional[str] = None
    lifecycle_stage: Optional[str] = None
    risk_tags: Optional[List[str]] = None
    associated_controls: Optional[List[str]] = None
    metadata_extra: Optional[Dict[str, Any]] = None


class AIAssetRelationshipRequest(BaseModel):
    """Create a directed relationship between two AI assets."""
    target_asset_id: str = Field(..., description="Target asset UUID")
    relationship_type: str = Field(..., description="Relationship type (feeds_into, depends_on, monitors)")
    metadata_extra: Optional[Dict[str, Any]] = None


# =============================================================================
# Response Schemas
# =============================================================================

class AIAssetResponse(BaseModel):
    """Full AI asset representation."""
    id: str
    org_id: str
    name: str
    asset_type: str
    description: Optional[str] = None
    owner: Optional[str] = None
    business_criticality: str
    exposure_level: str
    deployment_environment: Optional[str] = None
    lifecycle_stage: str
    risk_tags: List[str] = Field(default_factory=list)
    associated_controls: List[str] = Field(default_factory=list)
    last_validated_at: Optional[datetime] = None
    version: int = 1
    is_active: bool = True
    metadata_extra: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    model_config = {"from_attributes": True}


class AIAssetVersionResponse(BaseModel):
    """Single version history entry."""
    id: str
    asset_id: str
    version_number: int
    change_summary: Optional[str] = None
    changed_by: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AIAssetRelationshipResponse(BaseModel):
    """Asset relationship edge."""
    id: str
    source_asset_id: str
    target_asset_id: str
    relationship_type: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AIAssetListResponse(BaseModel):
    """Paginated AI asset listing."""
    assets: List[AIAssetResponse]
    total: int


class AIAssetGraphResponse(BaseModel):
    """Asset inventory graph with nodes and edges."""
    nodes: List[AIAssetResponse]
    edges: List[AIAssetRelationshipResponse]
