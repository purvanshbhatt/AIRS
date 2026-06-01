"""
Governance Policy API Routes.

Provides endpoints for creating, evaluating, and managing governance
policies. All policy evaluation is 100% deterministic.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import User, require_auth
from app.db.database import get_db
from app.models.governance_policy import PolicyType, EnforcementMode
from app.schemas.policy import (
    PolicyCreateRequest,
    PolicyUpdateRequest,
    PolicyResponse,
    PolicyEvaluationResponse,
    PolicyEvaluateAllResponse,
    PolicyViolationResponse,
    PolicyEvaluationLogResponse,
)
from app.governance.policies.engine import PolicyEngine

router = APIRouter(prefix="/policies", tags=["policies"])


def _get_org_id(user: User) -> str:
    return getattr(user, "org_id", "default-org")


@router.post(
    "",
    response_model=PolicyResponse,
    status_code=201,
    summary="Create a governance policy",
    description="Define a new governance policy with JSON rule definitions.",
)
async def create_policy(
    body: PolicyCreateRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user)

    # Validate policy type
    try:
        policy_type = PolicyType(body.policy_type)
    except ValueError:
        valid = [t.value for t in PolicyType]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid policy_type '{body.policy_type}'. Valid: {valid}",
        )

    # Validate enforcement mode
    try:
        enforcement_mode = EnforcementMode(body.enforcement_mode)
    except ValueError:
        valid = [m.value for m in EnforcementMode]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid enforcement_mode '{body.enforcement_mode}'. Valid: {valid}",
        )

    # Validate policy definition structure
    definition = body.policy_definition
    if "rules" not in definition:
        raise HTTPException(
            status_code=400,
            detail="policy_definition must contain a 'rules' array",
        )

    engine = PolicyEngine(db)
    policy = engine.create_policy(
        org_id=org_id,
        name=body.name,
        description=body.description,
        policy_type=policy_type,
        policy_definition=definition,
        enforcement_mode=enforcement_mode,
        created_by=user.uid,
    )
    return PolicyResponse.model_validate(policy)


@router.get(
    "",
    response_model=List[PolicyResponse],
    summary="List governance policies",
)
async def list_policies(
    active_only: bool = Query(True),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user)
    engine = PolicyEngine(db)
    policies = engine.list_policies(org_id, active_only=active_only)
    return [PolicyResponse.model_validate(p) for p in policies]


@router.get(
    "/{policy_id}",
    response_model=PolicyResponse,
    summary="Get policy details",
)
async def get_policy(
    policy_id: str,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    from app.models.governance_policy import GovernancePolicy

    org_id = _get_org_id(user)
    policy = db.query(GovernancePolicy).filter(
        GovernancePolicy.id == policy_id,
        GovernancePolicy.org_id == org_id,
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return PolicyResponse.model_validate(policy)


@router.patch(
    "/{policy_id}",
    response_model=PolicyResponse,
    summary="Update a governance policy",
)
async def update_policy(
    policy_id: str,
    body: PolicyUpdateRequest,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user)
    engine = PolicyEngine(db)
    updates = body.model_dump(exclude_unset=True)

    # Validate enforcement mode if provided
    if "enforcement_mode" in updates:
        try:
            updates["enforcement_mode"] = EnforcementMode(updates["enforcement_mode"])
        except ValueError:
            valid = [m.value for m in EnforcementMode]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid enforcement_mode. Valid: {valid}",
            )

    policy = engine.update_policy(policy_id, org_id, updates)
    return PolicyResponse.model_validate(policy)


@router.post(
    "/{policy_id}/evaluate",
    response_model=PolicyEvaluationResponse,
    summary="Evaluate a single policy",
    description="Run policy evaluation against the organization's current AI asset inventory.",
)
async def evaluate_policy(
    policy_id: str,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user)
    engine = PolicyEngine(db)
    result = engine.evaluate_policy(policy_id, org_id, evaluated_by=user.uid)

    return PolicyEvaluationResponse(
        policy_id=result.policy_id,
        policy_name=result.policy_name,
        result=result.result,
        violations=[
            PolicyViolationResponse(**v.to_dict()) for v in result.violations
        ],
        assets_evaluated=result.assets_evaluated,
        enforcement_mode=result.enforcement_mode,
    )


@router.post(
    "/evaluate-all",
    response_model=PolicyEvaluateAllResponse,
    summary="Evaluate all active policies",
    description="Run all active governance policies against the organization's AI asset inventory.",
)
async def evaluate_all_policies(
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user)
    engine = PolicyEngine(db)
    results = engine.evaluate_all_policies(org_id, evaluated_by=user.uid)

    response_results = []
    total_violations = 0
    passing = 0
    failing = 0
    warning = 0

    for r in results:
        total_violations += len(r.violations)
        if r.result == "pass":
            passing += 1
        elif r.result == "fail":
            failing += 1
        elif r.result == "warn":
            warning += 1

        response_results.append(PolicyEvaluationResponse(
            policy_id=r.policy_id,
            policy_name=r.policy_name,
            result=r.result,
            violations=[
                PolicyViolationResponse(**v.to_dict()) for v in r.violations
            ],
            assets_evaluated=r.assets_evaluated,
            enforcement_mode=r.enforcement_mode,
        ))

    return PolicyEvaluateAllResponse(
        results=response_results,
        total_policies=len(results),
        total_violations=total_violations,
        passing=passing,
        failing=failing,
        warning=warning,
    )


@router.get(
    "/violations/{org_id}",
    response_model=List[PolicyViolationResponse],
    summary="Get current policy violations",
    description="Fresh evaluation of all active policies, returning only violations.",
)
async def get_policy_violations(
    org_id: str,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    engine = PolicyEngine(db)
    violations = engine.get_policy_violations(org_id)
    return [PolicyViolationResponse(**v) for v in violations]


@router.get(
    "/{policy_id}/history",
    response_model=List[PolicyEvaluationLogResponse],
    summary="Get policy evaluation history",
)
async def get_evaluation_history(
    policy_id: str,
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    org_id = _get_org_id(user)
    engine = PolicyEngine(db)
    logs = engine.get_evaluation_history(policy_id, org_id, limit=limit)
    return [PolicyEvaluationLogResponse.model_validate(log) for log in logs]
