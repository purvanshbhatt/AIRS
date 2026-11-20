"""
EU AI Act system inventory API.

An owner records the AI systems the organisation uses or supplies, answers a
fixed questionnaire for each, and gets a first risk class with the duties that
follow. Every route needs sign-in and ownership of the organisation. The class
is computed by fixed rules from the stored answers; nothing here is verified
by ResilAI and nothing is a compliance result.
"""

import json
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.auth import User, require_auth, require_org_access
from app.core.demo_guard import require_writable
from app.db.database import get_db
from app.models.ai_act_system import AIActSystem
from app.services.governance import eu_ai_act

router = APIRouter(prefix="/ai-act", tags=["EU AI Act"])

Role = Literal["deployer", "provider"]
ObligationStatus = Literal["not_answered", "in_place", "not_in_place"]


def _clean(value: str) -> str:
    return " ".join(value.split())


class SystemInput(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    purpose: str = Field(..., min_length=1, max_length=1000)
    vendor: Optional[str] = Field(None, max_length=120)
    role: Role
    answers: Dict[str, bool] = Field(default_factory=dict)

    @field_validator("name", "purpose")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        value = _clean(value)
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("vendor")
    @classmethod
    def _blank_vendor_is_none(cls, value: Optional[str]) -> Optional[str]:
        value = _clean(value) if value else ""
        return value or None

    @field_validator("answers")
    @classmethod
    def _known_keys_only(cls, value: Dict[str, bool]) -> Dict[str, bool]:
        unknown = set(value) - eu_ai_act.ANSWER_KEYS
        if unknown:
            raise ValueError(f"unknown answer keys: {sorted(unknown)}")
        return value


class ObligationStatusInput(BaseModel):
    status: ObligationStatus


def _load_json(text: Optional[str]) -> Dict[str, Any]:
    try:
        data = json.loads(text or "{}")
    except (json.JSONDecodeError, TypeError):
        return {}
    return data if isinstance(data, dict) else {}


def _present(system: AIActSystem) -> Dict[str, Any]:
    answers = {k: v for k, v in _load_json(system.answers).items() if k in eu_ai_act.ANSWER_KEYS and v is True}
    result = eu_ai_act.classify(system.role, answers)
    recorded = _load_json(system.obligation_status)
    for duty in result["obligations"]:
        stored = recorded.get(duty["id"])
        # A status is the owner's own statement. It is never treated as verified.
        duty["status"] = stored if stored in eu_ai_act.OBLIGATION_STATUSES else "not_answered"
    return {
        "id": system.id,
        "org_id": system.org_id,
        "name": system.name,
        "purpose": system.purpose,
        "vendor": system.vendor,
        "role": system.role,
        "answers": answers,
        "created_at": system.created_at.isoformat() if system.created_at else None,
        "updated_at": system.updated_at.isoformat() if system.updated_at else None,
        **result,
    }


def _get_system(db: Session, org_id: str, system_id: str) -> AIActSystem:
    system = (
        db.query(AIActSystem)
        .filter(AIActSystem.id == system_id, AIActSystem.org_id == org_id)
        .first()
    )
    if not system:
        raise HTTPException(status_code=404, detail="AI system not found")
    return system


@router.get("/questionnaire")
def get_questionnaire(user: User = Depends(require_auth)) -> Dict[str, Any]:
    """The questions and their wording."""
    return eu_ai_act.questionnaire()


@router.get("/{org_id}/systems")
def list_systems(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
) -> Dict[str, Any]:
    require_org_access(db, user, org_id)
    systems = (
        db.query(AIActSystem)
        .filter(AIActSystem.org_id == org_id)
        .order_by(AIActSystem.created_at, AIActSystem.id)
        .all()
    )
    items: List[Dict[str, Any]] = [_present(s) for s in systems]
    counts = {key: 0 for key in eu_ai_act.RISK_LABELS}
    for item in items:
        counts[item["risk_class"]] += 1
    return {
        "org_id": org_id,
        "systems": items,
        "total": len(items),
        "by_risk_class": counts,
        "disclaimer": eu_ai_act.DISCLAIMER,
    }


@router.post("/{org_id}/systems", status_code=status.HTTP_201_CREATED)
def create_system(
    org_id: str,
    payload: SystemInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
) -> Dict[str, Any]:
    require_org_access(db, user, org_id)
    system = AIActSystem(
        org_id=org_id,
        name=payload.name,
        purpose=payload.purpose,
        vendor=payload.vendor,
        role=payload.role,
        answers=json.dumps({k: True for k, v in payload.answers.items() if v}, sort_keys=True),
        obligation_status="{}",
        created_by=user.uid,
    )
    db.add(system)
    db.commit()
    db.refresh(system)
    return _present(system)


@router.put("/{org_id}/systems/{system_id}")
def update_system(
    org_id: str,
    system_id: str,
    payload: SystemInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
) -> Dict[str, Any]:
    require_org_access(db, user, org_id)
    system = _get_system(db, org_id, system_id)
    system.name = payload.name
    system.purpose = payload.purpose
    system.vendor = payload.vendor
    system.role = payload.role
    system.answers = json.dumps({k: True for k, v in payload.answers.items() if v}, sort_keys=True)
    # Keep only statements for duties that still apply after the change.
    still_applies = {d["id"] for d in eu_ai_act.classify(payload.role, _load_json(system.answers))["obligations"]}
    kept = {k: v for k, v in _load_json(system.obligation_status).items() if k in still_applies}
    system.obligation_status = json.dumps(kept, sort_keys=True)
    db.commit()
    db.refresh(system)
    return _present(system)


@router.put("/{org_id}/systems/{system_id}/obligations/{obligation_id}")
def set_obligation_status(
    org_id: str,
    system_id: str,
    obligation_id: str,
    payload: ObligationStatusInput,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
) -> Dict[str, Any]:
    """Record the owner's own statement about one duty."""
    require_org_access(db, user, org_id)
    system = _get_system(db, org_id, system_id)
    applies = {d["id"] for d in eu_ai_act.classify(system.role, _load_json(system.answers))["obligations"]}
    if obligation_id not in applies:
        raise HTTPException(status_code=404, detail="This duty does not apply to the system")
    recorded = {k: v for k, v in _load_json(system.obligation_status).items() if k in applies}
    recorded[obligation_id] = payload.status
    system.obligation_status = json.dumps(recorded, sort_keys=True)
    db.commit()
    db.refresh(system)
    return _present(system)


@router.delete("/{org_id}/systems/{system_id}")
def delete_system(
    org_id: str,
    system_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
    _: None = Depends(require_writable),
) -> Dict[str, str]:
    require_org_access(db, user, org_id)
    system = _get_system(db, org_id, system_id)
    db.delete(system)
    db.commit()
    return {"status": "deleted", "id": system_id}
