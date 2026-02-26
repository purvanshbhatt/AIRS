"""
Pilot Program Service — 30-Day Readiness Sprint.

Manages the lifecycle of a pilot program for an organization:
  - Activate a 30-day readiness sprint
  - Track milestone completion
  - Calculate Pre-Audit Confidence Score

Milestones are predefined governance readiness checkpoints that
measure audit preparedness across key security domains.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("airs.pilot_program")


# ── Predefined Milestones ──────────────────────────────────────────

PILOT_MILESTONES = [
    {
        "id": "m1_governance_profile",
        "title": "Complete Governance Profile",
        "description": "Fill in industry, tier, regulatory bodies, and geo-regions.",
        "category": "foundation",
        "weight": 15,
        "day_target": 3,
    },
    {
        "id": "m2_first_assessment",
        "title": "Run First Assessment",
        "description": "Complete an initial AI risk assessment using NIST CSF 2.0.",
        "category": "assessment",
        "weight": 20,
        "day_target": 7,
    },
    {
        "id": "m3_siem_integration",
        "title": "Connect SIEM Integration",
        "description": "Configure Splunk or another SIEM for evidence-based verification.",
        "category": "integration",
        "weight": 10,
        "day_target": 10,
    },
    {
        "id": "m4_remediation_roadmap",
        "title": "Generate Remediation Roadmap",
        "description": "Create a prioritized roadmap from assessment findings.",
        "category": "remediation",
        "weight": 15,
        "day_target": 14,
    },
    {
        "id": "m5_second_assessment",
        "title": "Reassess After Remediation",
        "description": "Run second assessment to measure improvement.",
        "category": "assessment",
        "weight": 15,
        "day_target": 21,
    },
    {
        "id": "m6_executive_report",
        "title": "Generate Executive Report",
        "description": "Produce a board-ready PDF report with executive summary.",
        "category": "reporting",
        "weight": 10,
        "day_target": 25,
    },
    {
        "id": "m7_audit_calendar",
        "title": "Set Up Audit Calendar",
        "description": "Configure audit schedule with internal/external review dates.",
        "category": "audit",
        "weight": 10,
        "day_target": 28,
    },
    {
        "id": "m8_team_onboard",
        "title": "Onboard Team Members",
        "description": "Invite at least 2 additional team members for collaborative review.",
        "category": "team",
        "weight": 5,
        "day_target": 30,
    },
]

# ── In-Memory Pilot State (staging-only) ──────────────────────────
# In production, this would be stored in Firestore/database.
_active_pilots: Dict[str, Dict[str, Any]] = {}


def activate_pilot(org_id: str, org_name: str = "") -> Dict[str, Any]:
    """Activate a 30-day readiness sprint for an organization."""
    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=30)

    pilot = {
        "org_id": org_id,
        "org_name": org_name,
        "status": "active",
        "started_at": now.isoformat(),
        "ends_at": end_date.isoformat(),
        "days_remaining": 30,
        "milestones": [
            {
                **m,
                "status": "not_started",
                "completed_at": None,
            }
            for m in PILOT_MILESTONES
        ],
        "confidence_score": 0,
        "confidence_grade": "F",
    }
    _active_pilots[org_id] = pilot
    logger.info("Pilot activated for org %s", org_id)
    return pilot


def get_pilot(org_id: str) -> Optional[Dict[str, Any]]:
    """Get the current pilot program state for an organization."""
    pilot = _active_pilots.get(org_id)
    if not pilot:
        return None

    # Recalculate days remaining
    now = datetime.now(timezone.utc)
    ends_at = datetime.fromisoformat(pilot["ends_at"])
    days_remaining = max(0, (ends_at - now).days)
    pilot["days_remaining"] = days_remaining

    if days_remaining == 0 and pilot["status"] == "active":
        pilot["status"] = "completed"

    # Recalculate confidence score
    score, grade = _calculate_confidence(pilot["milestones"])
    pilot["confidence_score"] = score
    pilot["confidence_grade"] = grade

    return pilot


def complete_milestone(org_id: str, milestone_id: str) -> Optional[Dict[str, Any]]:
    """Mark a milestone as completed."""
    pilot = _active_pilots.get(org_id)
    if not pilot:
        return None

    for m in pilot["milestones"]:
        if m["id"] == milestone_id:
            m["status"] = "completed"
            m["completed_at"] = datetime.now(timezone.utc).isoformat()
            break

    # Recalculate
    score, grade = _calculate_confidence(pilot["milestones"])
    pilot["confidence_score"] = score
    pilot["confidence_grade"] = grade

    return pilot


def reset_milestone(org_id: str, milestone_id: str) -> Optional[Dict[str, Any]]:
    """Reset a milestone to not_started."""
    pilot = _active_pilots.get(org_id)
    if not pilot:
        return None

    for m in pilot["milestones"]:
        if m["id"] == milestone_id:
            m["status"] = "not_started"
            m["completed_at"] = None
            break

    score, grade = _calculate_confidence(pilot["milestones"])
    pilot["confidence_score"] = score
    pilot["confidence_grade"] = grade

    return pilot


def deactivate_pilot(org_id: str) -> bool:
    """Deactivate a pilot program."""
    if org_id in _active_pilots:
        _active_pilots[org_id]["status"] = "cancelled"
        return True
    return False


def _calculate_confidence(milestones: List[Dict[str, Any]]) -> Tuple[float, str]:
    """
    Calculate Pre-Audit Confidence Score (0-100).

    Each milestone has a weight. Sum of completed milestone weights = score.
    Grade thresholds: A >= 90, B >= 75, C >= 60, D >= 40, F < 40.
    """
    total_weight = sum(m["weight"] for m in milestones)
    completed_weight = sum(m["weight"] for m in milestones if m["status"] == "completed")

    if total_weight == 0:
        return 0.0, "F"

    score = round((completed_weight / total_weight) * 100, 1)

    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 60:
        grade = "C"
    elif score >= 40:
        grade = "D"
    else:
        grade = "F"

    return score, grade


def get_confidence_breakdown(org_id: str) -> Optional[Dict[str, Any]]:
    """Return detailed confidence score breakdown by category."""
    pilot = _active_pilots.get(org_id)
    if not pilot:
        return None

    categories: Dict[str, Dict[str, Any]] = {}
    for m in pilot["milestones"]:
        cat = m["category"]
        if cat not in categories:
            categories[cat] = {"total_weight": 0, "completed_weight": 0, "milestones": []}
        categories[cat]["total_weight"] += m["weight"]
        if m["status"] == "completed":
            categories[cat]["completed_weight"] += m["weight"]
        categories[cat]["milestones"].append({
            "id": m["id"],
            "title": m["title"],
            "status": m["status"],
            "weight": m["weight"],
        })

    score, grade = _calculate_confidence(pilot["milestones"])

    return {
        "org_id": org_id,
        "confidence_score": score,
        "confidence_grade": grade,
        "categories": {
            k: {
                "score": round((v["completed_weight"] / v["total_weight"]) * 100, 1) if v["total_weight"] > 0 else 0,
                "milestones": v["milestones"],
            }
            for k, v in categories.items()
        },
        "completed": sum(1 for m in pilot["milestones"] if m["status"] == "completed"),
        "total": len(pilot["milestones"]),
    }
