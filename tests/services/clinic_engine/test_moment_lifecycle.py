import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.db.database import Base, engine, SessionLocal
from app.models.clinic_moment import ClinicMomentRecord, MomentStatus
from app.services.clinic_engine.v2.schema import ClinicMoment, Verdict, MomentTranslation, ActionIntent
from app.services.clinic_engine.v2.moment_repository import MomentRepository

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()

@pytest.fixture
def client():
    return TestClient(app)

def create_mock_moment_record(db: SessionLocal, moment_id: str, status: MomentStatus = MomentStatus.ACTIVE):
    record = ClinicMomentRecord(
        id=moment_id,
        org_id="test-org",
        question_id="Q1",
        capability_id="unauthorized_access",
        verdict=Verdict.CONCERN.value,
        confidence=1.0,
        severity="medium",
        translation={"what_happened": "Test", "why_care": "Test", "ignore_impact": "Test"},
        actions=[
            {
                "action_id": "disable_account",
                "label": "Suspend Account",
                "can_automate": True,
                "automation_type": "m365_disable_user",
                "automation_params": {"user_id": "u-001"},
                "estimated_minutes": 5
            }
        ],
        evidence_ids=["u-001-stale"],
        status=status,
        generated_at=datetime.now(timezone.utc)
    )
    db.add(record)
    db.commit()
    return record

def test_fix_valid_moment(client, db_session):
    with patch('app.api.clinic.router.ClinicEvaluationEngine') as mock_engine_cls:
        mock_engine_cls.return_value.evaluate.return_value = [
            ClinicMoment(
                id="active-moment-id",
                question_id="Q1",
                capability_id="unauthorized_access",
                verdict=Verdict.CONCERN,
                confidence=1.0,
                translation=MomentTranslation(what_happened="x", why_care="y", ignore_impact="z"),
                actions=[],
                evidence_ids=[]
            )
        ]
        
        create_mock_moment_record(db_session, "active-moment-id")
        
        response = client.post("/api/clinic/problems/active-moment-id/fix")
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        
        # Verify DB updated
        repo = MomentRepository(db_session)
        record = repo.get_moment("active-moment-id")
        assert record.status == MomentStatus.RESOLVED_MANUALLY
        assert len(record.execution_history) == 1
        assert "Execute m365_disable_user" in record.execution_history[0]["action"]

def test_stale_moment_cannot_execute(client, db_session):
    """Proves remediation executes only after validation. If evidence changed, it fails gracefully."""
    with patch('app.api.clinic.router.ClinicEvaluationEngine') as mock_engine_cls:
        # Mock engine returns NO moments (meaning the evidence is gone)
        mock_engine_cls.return_value.evaluate.return_value = []
        
        create_mock_moment_record(db_session, "stale-moment-id")
        
        response = client.post("/api/clinic/problems/stale-moment-id/fix")
        assert response.status_code == 200
        assert response.json()["status"] == "error"
        assert response.json()["message"] == "This issue has already been resolved."
        
        # Verify it auto-resolved
        repo = MomentRepository(db_session)
        record = repo.get_moment("stale-moment-id")
        assert record.status == MomentStatus.RESOLVED_AUTOMATICALLY

def test_duplicate_fix_requests_are_idempotent(client, db_session):
    """Proves a resolved moment cannot be fixed again."""
    create_mock_moment_record(db_session, "resolved-moment-id", status=MomentStatus.RESOLVED_MANUALLY)
    
    response = client.post("/api/clinic/problems/resolved-moment-id/fix")
    assert response.status_code == 200
    assert response.json()["status"] == "error"
    assert response.json()["message"] == "This issue has already been resolved."
