"""
Continuous Scoring Engine

Calculates telemetry-weighted, evidence-fresh deterministic scoring.
Provides functionality to calculate current score, take snapshots,
detect score drift, and retrieve score history.
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.organization import Organization
from app.models.assessment import Assessment, AssessmentStatus
from app.models.score_snapshot import ScoreSnapshot, SnapshotTrigger
from app.models.connector import Connector, ConnectorStatus
from app.models.telemetry_event import TelemetryEvent
from app.schemas.score_snapshot import ScoreDriftResponse
from app.services.scoring import calculate_scores
import logging

logger = logging.getLogger("airs.scoring.continuous")


class ContinuousScoringEngine:
    """Telemetry-weighted, evidence-fresh deterministic scoring."""

    def __init__(self, db: Session):
        self.db = db

    def _get_latest_assessment_answers(self, org_id: str) -> Dict[str, Any]:
        """Fetch answers from the most recent completed assessment."""
        assessment = (
            self.db.query(Assessment)
            .filter(
                Assessment.organization_id == org_id,
                Assessment.status == AssessmentStatus.COMPLETED,
            )
            .order_by(desc(Assessment.completed_at))
            .first()
        )
        if not assessment:
            return {}
        
        # Build answers dict
        answers = {}
        for ans in assessment.answers:
            answers[ans.question_id] = ans.get_typed_value()
        return answers

    def _calculate_evidence_freshness(self, org_id: str) -> float:
        """Calculate evidence freshness factor (0.5 to 1.0).
        
        Decays linearly over a 90-day window from the last active telemetry event
        or assessment completion.
        """
        # Get most recent assessment
        assessment = (
            self.db.query(Assessment)
            .filter(
                Assessment.organization_id == org_id,
                Assessment.status == AssessmentStatus.COMPLETED,
            )
            .order_by(desc(Assessment.completed_at))
            .first()
        )
        
        last_activity_date = None
        if assessment and assessment.completed_at:
            last_activity_date = assessment.completed_at
            
        # Check most recent telemetry event
        latest_event = (
            self.db.query(TelemetryEvent)
            .filter(TelemetryEvent.org_id == org_id)
            .order_by(desc(TelemetryEvent.created_at))
            .first()
        )
        
        if latest_event and latest_event.created_at:
            if not last_activity_date or latest_event.created_at > last_activity_date:
                last_activity_date = latest_event.created_at
                
        if not last_activity_date:
            return 0.5  # Min freshness if no data

        # Make last_activity_date timezone aware if it isn't
        if last_activity_date.tzinfo is None:
            last_activity_date = last_activity_date.replace(tzinfo=timezone.utc)
            
        now = datetime.now(timezone.utc)
        age_days = (now - last_activity_date).days
        
        if age_days <= 0:
            return 1.0
        if age_days >= 90:
            return 0.5
            
        # Linear decay from 1.0 to 0.5 over 90 days
        decay_per_day = 0.5 / 90.0
        return 1.0 - (age_days * decay_per_day)

    def _calculate_stale_penalty(self, org_id: str, base_score: float) -> float:
        """Calculate stale penalty: -5 points per 30 days without fresh evidence."""
        # Get most recent activity
        latest_event = (
            self.db.query(TelemetryEvent)
            .filter(TelemetryEvent.org_id == org_id)
            .order_by(desc(TelemetryEvent.created_at))
            .first()
        )
        
        assessment = (
            self.db.query(Assessment)
            .filter(
                Assessment.organization_id == org_id,
                Assessment.status == AssessmentStatus.COMPLETED,
            )
            .order_by(desc(Assessment.completed_at))
            .first()
        )
        
        last_activity_date = None
        if assessment and assessment.completed_at:
            last_activity_date = assessment.completed_at
            
        if latest_event and latest_event.created_at:
            if not last_activity_date or latest_event.created_at > last_activity_date:
                last_activity_date = latest_event.created_at
                
        if not last_activity_date:
            return 0.0

        if last_activity_date.tzinfo is None:
            last_activity_date = last_activity_date.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age_days = (now - last_activity_date).days
        
        if age_days < 30:
            return 0.0
            
        penalty_intervals = int(age_days / 30)
        penalty = penalty_intervals * 5.0
        
        # Penalty cannot exceed 20 points, and cannot drop score below 20.0
        penalty = min(penalty, 20.0)
        if base_score - penalty < 20.0:
            penalty = max(0.0, base_score - 20.0)
            
        return penalty

    def _calculate_telemetry_bonus(self, org_id: str) -> float:
        """Calculate telemetry bonus: 0-5 points based on active connectors."""
        active_connectors = (
            self.db.query(Connector)
            .filter(
                Connector.org_id == org_id,
                Connector.status == ConnectorStatus.active
            )
            .count()
        )
        
        # 1 point per active connector, max 5 points
        return min(float(active_connectors), 5.0)

    def _calculate_confidence(self, org_id: str, answers: Dict[str, Any]) -> float:
        """Calculate data completeness confidence (0.0 - 1.0)."""
        if not answers:
            return 0.0
            
        # Simplified: Check active connectors to boost confidence
        active_connectors = (
            self.db.query(Connector)
            .filter(
                Connector.org_id == org_id,
                Connector.status == ConnectorStatus.active
            )
            .count()
        )
        
        base_confidence = 0.6  # Base for SELF_ATTESTED
        if active_connectors > 0:
            bonus = min(0.4, active_connectors * 0.1)
            return base_confidence + bonus
            
        return base_confidence

    def calculate_continuous_score(self, org_id: str) -> Dict[str, Any]:
        """Calculate the continuous governance score for an organization."""
        
        answers = self._get_latest_assessment_answers(org_id)
        if not answers:
            return {
                "overall_score": 0.0,
                "ghi_score": 0.0,
                "ghi_grade": "F",
                "domain_scores": {},
                "framework_coverage": {},
                "evidence_freshness_score": 0.0,
                "confidence_score": 0.0,
                "telemetry_weight": 0.0,
                "stale_penalty_applied": 0.0,
                "score_components": {}
            }
            
        # 1. Base score from latest assessment
        base_scores = calculate_scores(answers)
        base_overall = base_scores.get("overall_score", 0.0)
        
        # 2. Evidence freshness factor (0.5 - 1.0)
        freshness_factor = self._calculate_evidence_freshness(org_id)
        
        # 3. Telemetry bonus (0-5 points)
        telemetry_bonus = self._calculate_telemetry_bonus(org_id)
        
        # 4. Apply formula: base * freshness + bonus
        intermediate_score = (base_overall * freshness_factor) + telemetry_bonus
        
        # 5. Stale penalty (0-20 points)
        stale_penalty = self._calculate_stale_penalty(org_id, intermediate_score)
        
        final_score = intermediate_score - stale_penalty
        final_score = max(0.0, min(100.0, round(final_score, 2)))
        
        # Calculate Confidence
        confidence = self._calculate_confidence(org_id, answers)
        
        # Determine Grade
        if final_score >= 90:
            grade = "A"
        elif final_score >= 80:
            grade = "B"
        elif final_score >= 70:
            grade = "C"
        elif final_score >= 60:
            grade = "D"
        else:
            grade = "F"
            
        # Extract domain scores mapping
        domain_scores = {}
        for d in base_scores.get("domains", []):
            domain_scores[d["domain_name"]] = d["score"]

        active_connectors = (
            self.db.query(Connector)
            .filter(
                Connector.org_id == org_id,
                Connector.status == ConnectorStatus.active
            )
            .count()
        )

        return {
            "current_score": final_score,
            "ghi_score": final_score,
            "ghi_grade": grade,
            "domain_scores": domain_scores,
            "framework_coverage": {},
            "evidence_freshness": freshness_factor,
            "confidence": confidence,
            "telemetry_bonus": telemetry_bonus,
            "stale_penalty": stale_penalty,
            "active_connectors": active_connectors,
            "score_components": {
                "base_assessment_score": base_overall,
                "freshness_multiplier": freshness_factor,
                "telemetry_added": telemetry_bonus,
                "penalty_subtracted": stale_penalty,
            }
        }

    def take_snapshot(self, org_id: str, trigger: SnapshotTrigger, triggered_by: Optional[str] = None) -> ScoreSnapshot:
        """Create an immutable point-in-time score record."""
        score_data = self.calculate_continuous_score(org_id)
        
        snapshot = ScoreSnapshot(
            org_id=org_id,
            snapshot_trigger=trigger,
            overall_score=score_data["current_score"],
            ghi_score=score_data["ghi_score"],
            ghi_grade=score_data["ghi_grade"],
            domain_scores=score_data["domain_scores"],
            framework_coverage=score_data["framework_coverage"],
            evidence_freshness_score=score_data["evidence_freshness"],
            confidence_score=score_data["confidence"],
            telemetry_weight=score_data["telemetry_bonus"],
            stale_penalty_applied=score_data["stale_penalty"],
            triggered_by=triggered_by
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def get_score_timeline(self, org_id: str, limit: int = 10) -> List[ScoreSnapshot]:
        """Fetch historical score progression."""
        return (
            self.db.query(ScoreSnapshot)
            .filter(ScoreSnapshot.org_id == org_id)
            .order_by(desc(ScoreSnapshot.created_at))
            .limit(limit)
            .all()
        )

    def detect_score_drift(self, org_id: str) -> ScoreDriftResponse:
        """Compare current continuous score vs last snapshot."""
        current_score_data = self.calculate_continuous_score(org_id)
        current_score = current_score_data["current_score"]
        
        last_snapshot = (
            self.db.query(ScoreSnapshot)
            .filter(ScoreSnapshot.org_id == org_id)
            .order_by(desc(ScoreSnapshot.created_at))
            .first()
        )
        
        if not last_snapshot:
            return ScoreDriftResponse(
                current_score=current_score,
                previous_score=current_score,
                delta=0.0,
                drift_detected=False,
                drift_severity=None,
                contributing_factors=[]
            )
            
        previous_score = last_snapshot.overall_score
        delta = current_score - previous_score
        drift_detected = abs(delta) >= 5.0
        
        severity = None
        if drift_detected:
            if delta <= -15.0:
                severity = "critical"
            elif delta <= -5.0:
                severity = "high"
            else:
                severity = "medium"
                
        factors = []
        if current_score_data["stale_penalty"] > last_snapshot.stale_penalty_applied:
            factors.append(f"Stale penalty increased by {current_score_data['stale_penalty'] - last_snapshot.stale_penalty_applied:.1f} points")
        if current_score_data["evidence_freshness"] < last_snapshot.evidence_freshness_score:
            factors.append("Evidence freshness decayed")
            
        return ScoreDriftResponse(
            current_score=current_score,
            previous_score=previous_score,
            delta=delta,
            drift_detected=drift_detected,
            drift_severity=severity,
            contributing_factors=factors
        )
