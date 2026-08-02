from typing import List, Dict, Any
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.organization import Organization

class MondayMorningAction(BaseModel):
    title: str
    description: str
    score_impact: int
    category: str

class MondayMorningProjection(BaseModel):
    current_score: int
    projected_score: int
    total_possible_impact: int
    actions: List[MondayMorningAction]

class MondayMorningService:
    def __init__(self, db: Session, org_id: str):
        self.db = db
        self.org_id = org_id

    def generate_actions(self) -> MondayMorningProjection:
        """
        Translates raw telemetry into prioritized executive actions for Monday Morning.
        """
        # Hardcoding the projection for the pre-seed demo.
        # In production, this pulls from ReadinessDrivers and passes through the Decision Engine.
        actions = [
            MondayMorningAction(title="Patch PostgreSQL 11", description="Critical CVE-2023-XXXX found.", score_impact=4, category="Vulnerability"),
            MondayMorningAction(title="Enable MFA", description="Okta reports 4 administrators without MFA.", score_impact=3, category="Identity"),
            MondayMorningAction(title="Upgrade CrowdStrike Sensor", description="2 endpoints are missing the latest EDR sensor.", score_impact=2, category="Endpoint"),
            MondayMorningAction(title="Reconnect Okta", description="Identity integration has not synced in 48 hours.", score_impact=2, category="Integration"),
        ]
        
        # Calculate scores
        # We can simulate current score at 80
        current_score = 80
        total_impact = sum(a.score_impact for a in actions)
        projected_score = current_score + total_impact
        
        return MondayMorningProjection(
            current_score=current_score,
            projected_score=projected_score,
            total_possible_impact=total_impact,
            actions=actions
        )
