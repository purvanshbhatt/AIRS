"""
Threat Simulation API Routes.

Provides endpoints for running adversarial AI threat simulations,
executing full assessments, and retrieving historical results.
All simulation scoring is 100% deterministic.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import User, require_auth, get_user_org_id
from app.db.database import get_db
from app.models.simulation_result import SimulationCategory
from app.schemas.simulation import (
    SimulationRunRequest,
    SimulationResultResponse,
    SimulationResultListResponse,
    FullAssessmentResponse,
)
from app.simulation.engine import ThreatSimulationEngine

router = APIRouter(prefix="/simulations", tags=["simulations"])


def _get_org_id(user: User, db: Session) -> str:
    return get_user_org_id(user, db)


@router.post(
    "/run",
    response_model=SimulationResultResponse,
    status_code=201,
    summary="Run a threat simulation",
    description="Execute a single-category adversarial simulation against the organization's AI assets.",
)
async def run_simulation(
    body: SimulationRunRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user, db)

    # Validate category
    try:
        category = SimulationCategory(body.category)
    except ValueError:
        valid = [c.value for c in SimulationCategory]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category '{body.category}'. Valid: {valid}",
        )

    engine = ThreatSimulationEngine(db)
    result = engine.run_simulation(
        org_id=org_id,
        category=category,
        target_asset_id=body.target_asset_id,
        executed_by=user.uid,
    )
    
    # Event-driven broadcast upon simulation completion
    from app.core.websocket_manager import telemetry_ws_manager
    import asyncio
    asyncio.create_task(telemetry_ws_manager.broadcast_org_update(org_id))
    
    return SimulationResultResponse.model_validate(result)


@router.post(
    "/trigger",
    response_model=SimulationResultResponse,
    status_code=201,
    summary="Trigger a threat simulation (Alias)",
    description="Alias for /run to fulfill event-driven architectural constraints.",
)
async def trigger_simulation(
    body: SimulationRunRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    return await run_simulation(body, user, db)


@router.post(
    "/full-assessment",
    response_model=FullAssessmentResponse,
    status_code=201,
    summary="Run full threat assessment",
    description="Execute all simulation categories against all applicable AI assets in the organization.",
)
async def run_full_assessment(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user, db)
    engine = ThreatSimulationEngine(db)
    results = engine.run_full_assessment(org_id=org_id, executed_by=user.uid)

    result_responses = [SimulationResultResponse.model_validate(r) for r in results]

    # Aggregate summary
    total = len(result_responses)
    avg_blast = (
        sum(r.blast_radius_score for r in result_responses) / max(total, 1)
    )
    critical_findings = sum(
        1 for r in result_responses if r.blast_radius_score > 75
    )
    most_vulnerable = max(
        result_responses, key=lambda r: r.blast_radius_score, default=None
    )

    summary = {
        "total_simulations": total,
        "avg_blast_radius": round(avg_blast, 2),
        "critical_findings": critical_findings,
        "most_vulnerable_category": (
            most_vulnerable.category if most_vulnerable else None
        ),
    }

    # Event-driven broadcast upon simulation completion
    from app.core.websocket_manager import telemetry_ws_manager
    import asyncio
    asyncio.create_task(telemetry_ws_manager.broadcast_org_update(org_id))

    return FullAssessmentResponse(results=result_responses, summary=summary)


@router.get(
    "/results/{org_id}",
    response_model=SimulationResultListResponse,
    summary="Get simulation history",
    description="Retrieve historical simulation results for an organization.",
)
async def get_simulation_history(
    org_id: str,
    category: Optional[str] = Query(None, description="Filter by simulation category"),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    engine = ThreatSimulationEngine(db)

    cat_enum = None
    if category:
        try:
            cat_enum = SimulationCategory(category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

    results = engine.get_simulation_history(
        org_id=org_id, category=cat_enum, limit=limit
    )

    return SimulationResultListResponse(
        results=[SimulationResultResponse.model_validate(r) for r in results],
        total=len(results),
    )


@router.get(
    "/results/detail/{result_id}",
    response_model=SimulationResultResponse,
    summary="Get simulation result detail",
)
async def get_simulation_detail(
    result_id: str,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    from app.models.simulation_result import SimulationResult

    result = db.query(SimulationResult).filter(
        SimulationResult.id == result_id,
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Simulation result not found")
    return SimulationResultResponse.model_validate(result)
