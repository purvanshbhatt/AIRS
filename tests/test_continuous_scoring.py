import pytest
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from app.models.organization import Organization
from app.models.assessment import Assessment, AssessmentStatus
from app.models.answer import Answer
from app.models.connector import Connector, ConnectorStatus
from app.models.telemetry_event import TelemetryEvent
from app.services.continuous_scoring import ContinuousScoringEngine
from unittest.mock import patch


@pytest.fixture
def org(db_session):
    org = Organization(name="Test Org Continuous")
    db_session.add(org)
    db_session.commit()
    return org


@pytest.fixture
def assessment(db_session, org):
    a = Assessment(organization_id=org.id, status=AssessmentStatus.COMPLETED, completed_at=datetime.now(timezone.utc) - timedelta(days=5))
    db_session.add(a)
    db_session.commit()
    
    # Add some answers
    answers = [
        Answer(assessment_id=a.id, question_id="dc_01", value="true"),
        Answer(assessment_id=a.id, question_id="dc_02", value="true"),
    ]
    db_session.add_all(answers)
    db_session.commit()
    return a


@patch("app.services.continuous_scoring.calculate_scores")
def test_continuous_scoring_fresh_evidence(mock_calc, db_session, org, assessment):
    mock_calc.return_value = {"overall_score": 85.0, "domains": []}
    engine = ContinuousScoringEngine(db_session)
    
    # Add active connector and recent telemetry
    c = Connector(org_id=org.id, connector_type="github", display_name="GitHub", auth_method="api_key", status=ConnectorStatus.active, encrypted_credentials="123")
    db_session.add(c)
    db_session.commit()
    
    t = TelemetryEvent(org_id=org.id, connector_id=c.id, event_type="test", source_system="github", source_event_id="123", payload_hash="abc", payload={}, processed=True)
    db_session.add(t)
    db_session.commit()
    
    result = engine.calculate_continuous_score(org.id)
    
    assert result["evidence_freshness"] == 1.0
    assert result["telemetry_bonus"] == 1.0
    assert result["stale_penalty"] == 0.0
    assert result["active_connectors"] == 1
    assert result["confidence"] > 0.6  # boosted by connector


@patch("app.services.continuous_scoring.calculate_scores")
def test_continuous_scoring_stale_penalty(mock_calc, db_session, org, assessment):
    mock_calc.return_value = {"overall_score": 85.0, "domains": []}
    engine = ContinuousScoringEngine(db_session)
    
    # Set assessment completed_at to 60 days ago
    assessment.completed_at = datetime.now(timezone.utc) - timedelta(days=60)
    db_session.commit()
    
    result = engine.calculate_continuous_score(org.id)
    
    assert result["evidence_freshness"] < 1.0
    assert result["stale_penalty"] == 10.0  # 60 days = 2 intervals of 5 points
    assert result["active_connectors"] == 0


@patch("app.services.continuous_scoring.calculate_scores")
def test_score_drift_detection(mock_calc, db_session, org, assessment):
    mock_calc.return_value = {"overall_score": 85.0, "domains": []}
    engine = ContinuousScoringEngine(db_session)
    
    # Initial score
    result1 = engine.calculate_continuous_score(org.id)
    snapshot1 = engine.take_snapshot(org.id, "manual")
    
    # Now simulate staleness
    assessment.completed_at = datetime.now(timezone.utc) - timedelta(days=90)
    db_session.commit()
    
    drift = engine.detect_score_drift(org.id)
    assert drift.drift_detected is True
    assert drift.delta < 0
    assert drift.drift_severity in ["medium", "high", "critical"]
