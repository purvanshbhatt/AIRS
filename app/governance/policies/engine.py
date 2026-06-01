"""
PolicyEngine — Deterministic Governance Policy Evaluation.

Evaluates organizational governance policies against the current state of
AI assets, connectors, and assessments. Policies are JSON-defined rule sets
that can operate in three enforcement modes:

  - enforce:  Violations block deployment gates and produce critical alerts.
  - audit:    Violations are logged but do not block operations.
  - disabled: Policy is inactive and not evaluated.

Policy Definition Schema (JSON):
  {
    "rules": [
      {
        "condition": "<field> <operator> <value>",
        "require": "<field> <operator> <value>",
        "severity": "critical|high|medium|low"
      }
    ]
  }

Supported condition operators:
  ==, !=, IN, NOT_IN, IS_NULL, IS_NOT_NULL, >, <, >=, <=

All evaluation is 100% deterministic — no LLM involvement.
Staging-only module — not deployed to production/demo.
"""

from __future__ import annotations

import logging
import operator
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.ai_asset import AIAsset
from app.models.governance_policy import (
    GovernancePolicy,
    PolicyEvaluationLog,
    PolicyType,
    EnforcementMode,
)

logger = logging.getLogger("airs.policy_engine")


# ═══════════════════════════════════════════════════════════════════════
# Condition Evaluator (Deterministic)
# ═══════════════════════════════════════════════════════════════════════

# Mapping of operator strings to comparison functions
OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    "<": operator.lt,
    ">=": operator.ge,
    "<=": operator.le,
}


def _resolve_field(obj: Any, field_path: str) -> Any:
    """Resolve a dotted field path on an object or dict.

    Examples:
      _resolve_field(asset, "asset_type")          -> asset.asset_type
      _resolve_field(asset, "business_criticality") -> asset.business_criticality
    """
    current = obj
    for part in field_path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
        if current is None:
            return None
    # Resolve enum values
    if hasattr(current, "value"):
        current = current.value
    return current


def _parse_value(raw: str) -> Any:
    """Parse a string value from a policy condition into a typed value."""
    stripped = raw.strip().strip("'\"")
    if stripped.lower() == "null" or stripped.lower() == "none":
        return None
    if stripped.lower() == "true":
        return True
    if stripped.lower() == "false":
        return False
    # Time expressions like NOW() - 30d
    if "NOW()" in stripped.upper():
        return _parse_time_expression(stripped)
    try:
        return int(stripped)
    except ValueError:
        pass
    try:
        return float(stripped)
    except ValueError:
        pass
    return stripped


def _parse_time_expression(expr: str) -> datetime:
    """Parse time expressions like 'NOW() - 30d' into a datetime."""
    now = datetime.now(timezone.utc)
    expr_upper = expr.upper().strip()

    if expr_upper == "NOW()":
        return now

    # Parse "NOW() - Xd" pattern
    if "-" in expr_upper:
        parts = expr_upper.split("-")
        delta_str = parts[1].strip()
        if delta_str.endswith("D"):
            days = int(delta_str[:-1])
            return now - timedelta(days=days)
        elif delta_str.endswith("H"):
            hours = int(delta_str[:-1])
            return now - timedelta(hours=hours)

    return now


def _evaluate_condition(obj: Any, condition_str: str) -> bool:
    """Evaluate a single condition string against an object.

    Supports: ==, !=, IN, NOT_IN, IS_NULL, IS_NOT_NULL, >, <, >=, <=
    """
    condition = condition_str.strip()

    # IS_NOT_NULL check
    if "IS NOT NULL" in condition.upper() or "IS_NOT_NULL" in condition.upper():
        field = condition.split()[0].strip()
        value = _resolve_field(obj, field)
        return value is not None

    # IS_NULL check
    if "IS NULL" in condition.upper() or "IS_NULL" in condition.upper():
        field = condition.split()[0].strip()
        value = _resolve_field(obj, field)
        return value is None

    # NOT IN check
    if " NOT IN " in condition.upper() or " NOT_IN " in condition.upper():
        parts = condition.upper().split(" NOT IN " if " NOT IN " in condition.upper() else " NOT_IN ")
        field = condition[:len(parts[0])].strip()
        values_str = condition[len(parts[0]):].upper().replace("NOT IN", "").replace("NOT_IN", "").strip()
        # Parse list: (val1, val2, val3)
        values_str = values_str.strip("()")
        values = [v.strip().strip("'\"").lower() for v in values_str.split(",")]
        field_val = _resolve_field(obj, field)
        if field_val is None:
            return True  # None is not in any list
        return str(field_val).lower() not in values

    # IN check
    if " IN " in condition.upper():
        idx = condition.upper().index(" IN ")
        field = condition[:idx].strip()
        values_str = condition[idx + 4:].strip().strip("()")
        values = [v.strip().strip("'\"").lower() for v in values_str.split(",")]
        field_val = _resolve_field(obj, field)
        if field_val is None:
            return False
        return str(field_val).lower() in values

    # Comparison operators (>= and <= before > and <)
    for op_str in [">=", "<=", "!=", "==", ">", "<"]:
        if op_str in condition:
            parts = condition.split(op_str, 1)
            field = parts[0].strip()
            raw_value = parts[1].strip()
            field_val = _resolve_field(obj, field)
            target_val = _parse_value(raw_value)

            if field_val is None or target_val is None:
                return False

            op_func = OPERATORS.get(op_str)
            if op_func:
                try:
                    return op_func(field_val, target_val)
                except TypeError:
                    return False
            break

    logger.warning(f"Could not parse condition: {condition}")
    return True  # Default to passing if condition can't be parsed


# ═══════════════════════════════════════════════════════════════════════
# Policy Engine
# ═══════════════════════════════════════════════════════════════════════

class PolicyViolation:
    """A single policy rule violation."""

    def __init__(
        self,
        rule_index: int,
        condition: str,
        requirement: str,
        severity: str,
        asset_id: Optional[str] = None,
        asset_name: Optional[str] = None,
        details: Optional[str] = None,
    ):
        self.rule_index = rule_index
        self.condition = condition
        self.requirement = requirement
        self.severity = severity
        self.asset_id = asset_id
        self.asset_name = asset_name
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_index": self.rule_index,
            "condition": self.condition,
            "requirement": self.requirement,
            "severity": self.severity,
            "asset_id": self.asset_id,
            "asset_name": self.asset_name,
            "details": self.details,
        }


class PolicyEvaluationResult:
    """Result of evaluating a single policy."""

    def __init__(
        self,
        policy_id: str,
        policy_name: str,
        result: str,  # pass, fail, warn
        violations: List[PolicyViolation],
        assets_evaluated: int,
        enforcement_mode: str,
    ):
        self.policy_id = policy_id
        self.policy_name = policy_name
        self.result = result
        self.violations = violations
        self.assets_evaluated = assets_evaluated
        self.enforcement_mode = enforcement_mode

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "policy_name": self.policy_name,
            "result": self.result,
            "violations": [v.to_dict() for v in self.violations],
            "assets_evaluated": self.assets_evaluated,
            "enforcement_mode": self.enforcement_mode,
        }


class PolicyEngine:
    """Deterministic governance policy evaluation engine.

    Evaluates policy rules against the organization's current AI asset
    inventory. All evaluations are logged to the PolicyEvaluationLog
    table for audit trail compliance.
    """

    def __init__(self, db: Session):
        self.db = db

    # ── Policy CRUD ─────────────────────────────────────────────────────

    def create_policy(
        self,
        org_id: str,
        name: str,
        description: str,
        policy_type: PolicyType,
        policy_definition: Dict[str, Any],
        enforcement_mode: EnforcementMode = EnforcementMode.audit,
        created_by: Optional[str] = None,
    ) -> GovernancePolicy:
        """Create a new governance policy."""
        policy = GovernancePolicy(
            org_id=org_id,
            name=name,
            description=description,
            policy_type=policy_type,
            policy_definition=policy_definition,
            enforcement_mode=enforcement_mode,
            created_by=created_by,
        )
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        logger.info(f"Created policy '{name}' (id={policy.id}) for org {org_id}")
        return policy

    def update_policy(
        self,
        policy_id: str,
        org_id: str,
        updates: Dict[str, Any],
    ) -> GovernancePolicy:
        """Update a policy and increment its version."""
        policy = self._get_policy(policy_id, org_id)
        for key, value in updates.items():
            if hasattr(policy, key) and key not in ("id", "org_id", "created_at"):
                setattr(policy, key, value)
        policy.version += 1
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def list_policies(
        self,
        org_id: str,
        active_only: bool = True,
    ) -> List[GovernancePolicy]:
        """List all policies for an organization."""
        query = self.db.query(GovernancePolicy).filter(
            GovernancePolicy.org_id == org_id,
        )
        if active_only:
            query = query.filter(GovernancePolicy.is_active == True)
        return query.order_by(GovernancePolicy.created_at.desc()).all()

    # ── Policy Evaluation ───────────────────────────────────────────────

    def evaluate_policy(
        self,
        policy_id: str,
        org_id: str,
        evaluated_by: Optional[str] = None,
    ) -> PolicyEvaluationResult:
        """Evaluate a single policy against the organization's assets."""
        policy = self._get_policy(policy_id, org_id)

        if policy.enforcement_mode == EnforcementMode.disabled:
            return PolicyEvaluationResult(
                policy_id=policy.id,
                policy_name=policy.name,
                result="pass",
                violations=[],
                assets_evaluated=0,
                enforcement_mode="disabled",
            )

        # Load org assets
        assets = self.db.query(AIAsset).filter(
            AIAsset.org_id == org_id,
            AIAsset.is_active == True,
        ).all()

        violations = self._evaluate_rules(policy, assets)

        # Determine result
        if not violations:
            result = "pass"
        elif policy.enforcement_mode == EnforcementMode.audit:
            result = "warn"
        else:
            result = "fail"

        eval_result = PolicyEvaluationResult(
            policy_id=policy.id,
            policy_name=policy.name,
            result=result,
            violations=violations,
            assets_evaluated=len(assets),
            enforcement_mode=policy.enforcement_mode.value if hasattr(policy.enforcement_mode, 'value') else str(policy.enforcement_mode),
        )

        # Log evaluation
        log_entry = PolicyEvaluationLog(
            policy_id=policy.id,
            org_id=org_id,
            evaluation_context={
                "assets_evaluated": len(assets),
                "enforcement_mode": eval_result.enforcement_mode,
                "policy_version": policy.version,
            },
            result=result,
            violations=[v.to_dict() for v in violations],
            evaluated_by=evaluated_by,
        )
        self.db.add(log_entry)
        self.db.commit()

        logger.info(
            f"Policy '{policy.name}' evaluated: result={result}, "
            f"violations={len(violations)}, assets={len(assets)}"
        )
        return eval_result

    def evaluate_all_policies(
        self,
        org_id: str,
        evaluated_by: Optional[str] = None,
    ) -> List[PolicyEvaluationResult]:
        """Evaluate all active policies for an organization."""
        policies = self.list_policies(org_id, active_only=True)
        results = []
        for policy in policies:
            result = self.evaluate_policy(
                policy.id, org_id, evaluated_by=evaluated_by
            )
            results.append(result)
        return results

    def get_policy_violations(
        self,
        org_id: str,
    ) -> List[Dict[str, Any]]:
        """Get all current violations across all active policies.

        Runs a fresh evaluation and returns only the violations.
        """
        results = self.evaluate_all_policies(org_id)
        all_violations = []
        for result in results:
            for v in result.violations:
                violation_dict = v.to_dict()
                violation_dict["policy_id"] = result.policy_id
                violation_dict["policy_name"] = result.policy_name
                all_violations.append(violation_dict)
        return all_violations

    def get_evaluation_history(
        self,
        policy_id: str,
        org_id: str,
        limit: int = 50,
    ) -> List[PolicyEvaluationLog]:
        """Retrieve historical evaluation logs for a policy."""
        return (
            self.db.query(PolicyEvaluationLog)
            .filter(
                PolicyEvaluationLog.policy_id == policy_id,
                PolicyEvaluationLog.org_id == org_id,
            )
            .order_by(PolicyEvaluationLog.evaluated_at.desc())
            .limit(limit)
            .all()
        )

    # ── Internal Methods ────────────────────────────────────────────────

    def _get_policy(self, policy_id: str, org_id: str) -> GovernancePolicy:
        """Fetch a policy, raising 404 if not found."""
        from fastapi import HTTPException
        policy = self.db.query(GovernancePolicy).filter(
            GovernancePolicy.id == policy_id,
            GovernancePolicy.org_id == org_id,
        ).first()
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        return policy

    def _evaluate_rules(
        self,
        policy: GovernancePolicy,
        assets: List[AIAsset],
    ) -> List[PolicyViolation]:
        """Evaluate all rules in a policy definition against assets."""
        violations = []
        definition = policy.policy_definition or {}
        rules = definition.get("rules", [])

        for idx, rule in enumerate(rules):
            condition = rule.get("condition", "")
            requirement = rule.get("require", "")
            severity = rule.get("severity", "medium")

            if not condition and not requirement:
                continue

            for asset in assets:
                # Check if the condition matches this asset
                condition_matches = True
                if condition:
                    condition_matches = _evaluate_condition(asset, condition)

                if not condition_matches:
                    continue  # This rule doesn't apply to this asset

                # Check if the requirement is met
                if requirement:
                    requirement_met = _evaluate_condition(asset, requirement)
                    if not requirement_met:
                        violations.append(PolicyViolation(
                            rule_index=idx,
                            condition=condition,
                            requirement=requirement,
                            severity=severity,
                            asset_id=asset.id,
                            asset_name=asset.name,
                            details=f"Asset '{asset.name}' matches condition '{condition}' but fails requirement '{requirement}'",
                        ))

        return violations
