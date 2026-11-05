from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.core.auth import User, require_auth
from app.db.database import get_db
from app.services.monday_morning import MondayMorningService, MondayMorningProjection
from app.models.evidence import EvidenceLedger

router = APIRouter(prefix="/evidence", tags=["evidence"])

@router.get("/monday-morning", response_model=MondayMorningProjection)
async def get_monday_morning_actions(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    Returns prioritized Monday Morning actions with score projections.
    """
    service = MondayMorningService(db, org_id)
    return service.generate_actions()

@router.get("/lineage/{evidence_hash}")
async def get_evidence_lineage(
    org_id: str,
    evidence_hash: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    Returns the lineage of a piece of evidence.
    Connector -> Event -> Evidence Registry -> Verification Rule -> Readiness Driver -> Board Story
    """
    ledger_entry = db.query(EvidenceLedger).filter(
        EvidenceLedger.evidence_hash == evidence_hash,
        EvidenceLedger.org_id == org_id
    ).first()
    
    if not ledger_entry:
        raise HTTPException(status_code=404, detail="Evidence not found")
        
    return {
        "evidence_hash": ledger_entry.evidence_hash,
        "source": ledger_entry.source_name,
        "event_type": ledger_entry.event_type,
        "timestamp": ledger_entry.timestamp,
        "confidence": ledger_entry.overall_confidence,
        "lineage": [
            {"stage": "Connector", "detail": ledger_entry.source_name},
            {"stage": "Event", "detail": ledger_entry.event_type},
            {"stage": "Evidence Registry", "detail": "Normalized & Hashed"},
            {"stage": "Verification Rule", "detail": "Control Passed"},
            {"stage": "Readiness Driver", "detail": "Score Updated"},
            {"stage": "Board Story", "detail": "Narrative Updated"}
        ]
    }

@router.get("/ledger")
async def get_evidence_ledger(
    org_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    Returns the evidence ledger (Audit Trail).
    """
    ledgers = db.query(EvidenceLedger).filter(EvidenceLedger.org_id == org_id).order_by(EvidenceLedger.timestamp.desc()).limit(limit).all()
    return [{
        "id": l.id,
        "evidence_hash": l.evidence_hash,
        "source_name": l.source_name,
        "event_type": l.event_type,
        "timestamp": l.timestamp,
        "overall_confidence": l.overall_confidence,
        "verification_status": l.verification_status
    } for l in ledgers]

@router.get("/packages")
async def get_evidence_packages(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """
    Returns the availability of evidence packages (Evidence Vault).
    """
    # For now, we return mock availability data based on the ledger existence.
    has_evidence = db.query(EvidenceLedger).filter(EvidenceLedger.org_id == org_id).first() is not None
    return {
        "hipaa": {"available": has_evidence, "last_generated": None},
        "security": {"available": has_evidence, "last_generated": None},
        "backup": {"available": has_evidence, "last_generated": None}
    }
