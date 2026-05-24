"""
Test Suite — Governance Engine.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.finding_provenance import FindingProvenance, ProvenanceStatus
from app.models.framework_mapping import FrameworkMappingRegistry
from app.services.scoring import calculate_domain_score, _score_question

@pytest.fixture(scope="function")
def db_session():
    """Create an in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)

def test_multi_framework_mapping_creation(db_session):
    """Test creating a FrameworkMappingRegistry with multiple frameworks including ISO 42001."""
    mapping1 = FrameworkMappingRegistry(
        finding_id="test-finding-1234",
        framework_type="NIST_AI_RMF",
        control_id="MAP 1.1"
    )
    mapping2 = FrameworkMappingRegistry(
        finding_id="test-finding-1234",
        framework_type="ISO_42001",
        control_id="A.8"
    )
    db_session.add_all([mapping1, mapping2])
    db_session.commit()
    
    fetched = db_session.query(FrameworkMappingRegistry).all()
    frameworks = {m.framework_type.value: m.control_id for m in fetched}
    assert frameworks.get("NIST_AI_RMF") == "MAP 1.1"
    assert frameworks.get("ISO_42001") == "A.8"

def test_ghi_score_update_deterministic_reliability():
    """Test that GHI score uses reliability_factor (1.0 vs 0.6)."""
    question = {
        "id": "test_01",
        "type": "boolean",
        "points": 10,
        "text": "Test question"
    }
    
    # PROVISIONAL/SELF_ATTESTED -> 0.6 multiplier
    score_self = _score_question(question, True, "SELF_ATTESTED")
    assert score_self == 6.0
    
    # SOC_VERIFIED -> 1.0 multiplier
    score_verified = _score_question(question, True, "SOC_VERIFIED")
    assert score_verified == 10.0

def test_connection_error_status_enum():
    """Test CONNECTION_ERROR enum is present."""
    assert ProvenanceStatus.CONNECTION_ERROR.value == "CONNECTION_ERROR"
