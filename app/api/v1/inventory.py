"""
AI Asset Inventory API — CRUD, versioning, and dependency graph.

Provides full lifecycle management of AI assets including models, agents,
RAG pipelines, datasets, and inference endpoints. Supports version history
for audit reconstruction and relationship tracking for supply chain mapping.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import User, require_auth
from app.db.database import get_db
from app.models.ai_asset import (
    AIAsset,
    AIAssetRelationship,
    AIAssetVersion,
)
from app.schemas.ai_asset import (
    AIAssetCreateRequest,
    AIAssetGraphResponse,
    AIAssetListResponse,
    AIAssetRelationshipRequest,
    AIAssetRelationshipResponse,
    AIAssetResponse,
    AIAssetUpdateRequest,
    AIAssetVersionResponse,
)

logger = logging.getLogger("airs.api.inventory")

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _get_org_id(user: User) -> str:
    return getattr(user, "org_id", "default-org")


# =============================================================================
# Asset CRUD
# =============================================================================

@router.post(
    "/assets",
    response_model=AIAssetResponse,
    status_code=201,
    summary="Register a new AI asset",
    description="Add an AI asset to the organization's inventory with classification metadata.",
)
async def create_asset(
    body: AIAssetCreateRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user)

    asset = AIAsset(
        org_id=org_id,
        name=body.name,
        asset_type=body.asset_type,
        description=body.description,
        owner=body.owner,
        business_criticality=body.business_criticality,
        exposure_level=body.exposure_level,
        deployment_environment=body.deployment_environment,
        lifecycle_stage=body.lifecycle_stage,
        risk_tags=body.risk_tags,
        associated_controls=body.associated_controls,
        metadata_extra=body.metadata_extra,
        created_by=user.uid,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    # Create initial version record
    version = AIAssetVersion(
        asset_id=asset.id,
        version_number=1,
        change_summary="Initial registration",
        changed_by=user.uid,
        snapshot=_asset_snapshot(asset),
    )
    db.add(version)
    db.commit()

    return AIAssetResponse.model_validate(asset)


@router.get(
    "/assets",
    response_model=AIAssetListResponse,
    summary="List AI assets",
    description="Paginated listing of AI assets with optional type and lifecycle filters.",
)
async def list_assets(
    asset_type: Optional[str] = Query(None),
    lifecycle_stage: Optional[str] = Query(None),
    is_active: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user)
    query = db.query(AIAsset).filter(
        AIAsset.org_id == org_id,
        AIAsset.is_active == is_active,
    )
    if asset_type:
        query = query.filter(AIAsset.asset_type == asset_type)
    if lifecycle_stage:
        query = query.filter(AIAsset.lifecycle_stage == lifecycle_stage)

    total = query.count()
    assets = query.order_by(AIAsset.created_at.desc()).offset(skip).limit(limit).all()

    return AIAssetListResponse(
        assets=[AIAssetResponse.model_validate(a) for a in assets],
        total=total,
    )


@router.get(
    "/assets/{asset_id}",
    response_model=AIAssetResponse,
    summary="Get asset details",
)
async def get_asset(
    asset_id: str,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user)
    asset = (
        db.query(AIAsset)
        .filter(AIAsset.id == asset_id, AIAsset.org_id == org_id)
        .first()
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AIAssetResponse.model_validate(asset)


@router.patch(
    "/assets/{asset_id}",
    response_model=AIAssetResponse,
    summary="Update asset (creates version record)",
)
async def update_asset(
    asset_id: str,
    body: AIAssetUpdateRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user)
    asset = (
        db.query(AIAsset)
        .filter(AIAsset.id == asset_id, AIAsset.org_id == org_id)
        .first()
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Track changes for version summary
    changes = []
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        old_value = getattr(asset, field, None)
        if old_value != value:
            changes.append(f"{field}: {old_value!r} → {value!r}")
            setattr(asset, field, value)

    if changes:
        asset.version += 1
        db.commit()
        db.refresh(asset)

        # Create version record
        version = AIAssetVersion(
            asset_id=asset.id,
            version_number=asset.version,
            change_summary="; ".join(changes),
            changed_by=user.uid,
            snapshot=_asset_snapshot(asset),
        )
        db.add(version)
        db.commit()

    return AIAssetResponse.model_validate(asset)


@router.delete(
    "/assets/{asset_id}",
    status_code=204,
    summary="Deactivate asset (soft-delete)",
)
async def deactivate_asset(
    asset_id: str,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user)
    asset = (
        db.query(AIAsset)
        .filter(AIAsset.id == asset_id, AIAsset.org_id == org_id)
        .first()
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset.is_active = False
    asset.lifecycle_stage = "retired"
    asset.version += 1
    db.commit()


# =============================================================================
# Version History
# =============================================================================

@router.get(
    "/assets/{asset_id}/versions",
    response_model=list[AIAssetVersionResponse],
    summary="Asset version history",
)
async def get_versions(
    asset_id: str,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user)
    # Verify ownership
    asset = (
        db.query(AIAsset)
        .filter(AIAsset.id == asset_id, AIAsset.org_id == org_id)
        .first()
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    versions = (
        db.query(AIAssetVersion)
        .filter(AIAssetVersion.asset_id == asset_id)
        .order_by(AIAssetVersion.version_number.desc())
        .all()
    )
    return [AIAssetVersionResponse.model_validate(v) for v in versions]


# =============================================================================
# Relationships (Supply Chain Graph)
# =============================================================================

@router.post(
    "/assets/{asset_id}/relationships",
    response_model=AIAssetRelationshipResponse,
    status_code=201,
    summary="Create asset relationship",
)
async def create_relationship(
    asset_id: str,
    body: AIAssetRelationshipRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user)
    # Verify source asset ownership
    source = (
        db.query(AIAsset)
        .filter(AIAsset.id == asset_id, AIAsset.org_id == org_id)
        .first()
    )
    if not source:
        raise HTTPException(status_code=404, detail="Source asset not found")

    # Verify target asset exists in same org
    target = (
        db.query(AIAsset)
        .filter(AIAsset.id == body.target_asset_id, AIAsset.org_id == org_id)
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="Target asset not found")

    rel = AIAssetRelationship(
        source_asset_id=asset_id,
        target_asset_id=body.target_asset_id,
        relationship_type=body.relationship_type,
        metadata_extra=body.metadata_extra,
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)

    return AIAssetRelationshipResponse.model_validate(rel)


@router.get(
    "/graph",
    response_model=AIAssetGraphResponse,
    summary="AI asset dependency graph",
    description="Returns the full asset inventory graph with nodes and edges for visualization.",
)
async def get_asset_graph(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user)

    assets = (
        db.query(AIAsset)
        .filter(AIAsset.org_id == org_id, AIAsset.is_active == True)
        .all()
    )
    asset_ids = {a.id for a in assets}

    relationships = (
        db.query(AIAssetRelationship)
        .filter(AIAssetRelationship.source_asset_id.in_(asset_ids))
        .all()
    )

    return AIAssetGraphResponse(
        nodes=[AIAssetResponse.model_validate(a) for a in assets],
        edges=[AIAssetRelationshipResponse.model_validate(r) for r in relationships],
    )


# =============================================================================
# Helpers
# =============================================================================

def _asset_snapshot(asset: AIAsset) -> dict:
    """Create a JSON-serializable snapshot of an asset for version history."""
    return {
        "name": asset.name,
        "asset_type": asset.asset_type if isinstance(asset.asset_type, str) else asset.asset_type.value,
        "description": asset.description,
        "owner": asset.owner,
        "business_criticality": asset.business_criticality if isinstance(asset.business_criticality, str) else asset.business_criticality.value,
        "exposure_level": asset.exposure_level if isinstance(asset.exposure_level, str) else asset.exposure_level.value,
        "deployment_environment": asset.deployment_environment,
        "lifecycle_stage": asset.lifecycle_stage if isinstance(asset.lifecycle_stage, str) else asset.lifecycle_stage.value,
        "risk_tags": asset.risk_tags,
        "associated_controls": asset.associated_controls,
        "version": asset.version,
        "is_active": asset.is_active,
    }
