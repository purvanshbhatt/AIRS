"""
API routes for Continuous Scoring Engine.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.core.auth import require_auth
from app.services.continuous_scoring import ContinuousScoringEngine
from app.schemas.score_snapshot import (
    ContinuousScoreResponse, 
    ScoreTimelineResponse, 
    ScoreSnapshotResponse,
    ScoreDriftResponse
)
from app.models.score_snapshot import SnapshotTrigger

router = APIRouter(prefix="/scoring", tags=["continuous-scoring"])


@router.get("/continuous/{org_id}", response_model=ContinuousScoreResponse)
async def get_continuous_score(
    org_id: str,
    db: Session = Depends(get_db),
    user=Depends(require_auth)
):
    """Get the current live continuous governance score."""
    engine = ContinuousScoringEngine(db)
    result = engine.calculate_continuous_score(org_id)
    return result


@router.get("/timeline/{org_id}", response_model=ScoreTimelineResponse)
async def get_score_timeline(
    org_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    user=Depends(require_auth)
):
    """Get chronological score history for an organization."""
    engine = ContinuousScoringEngine(db)
    snapshots = engine.get_score_timeline(org_id, limit=limit)
    return {"snapshots": snapshots}


@router.post("/snapshot/{org_id}", response_model=ScoreSnapshotResponse)
async def take_score_snapshot(
    org_id: str,
    db: Session = Depends(get_db),
    user=Depends(require_auth)
):
    """Take a manual score snapshot."""
    engine = ContinuousScoringEngine(db)
    snapshot = engine.take_snapshot(
        org_id=org_id, 
        trigger=SnapshotTrigger.manual,
        triggered_by=user.uid
    )
    return snapshot


@router.get("/drift/{org_id}", response_model=ScoreDriftResponse)
async def detect_score_drift(
    org_id: str,
    db: Session = Depends(get_db),
    user=Depends(require_auth)
):
    """Detect score drift between current continuous score and last snapshot."""
    engine = ContinuousScoringEngine(db)
    drift = engine.detect_score_drift(org_id)
    return drift


@router.get("/coverage/{org_id}")
async def get_framework_coverage(
    org_id: str,
    db: Session = Depends(get_db),
    user=Depends(require_auth)
):
    """Get framework coverage matrix (stubbed for now)."""
    return {"status": "Not Implemented Yet"}
