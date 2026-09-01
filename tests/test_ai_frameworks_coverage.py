import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.framework_mapping import FrameworkMappingRegistry, FrameworkType
from app.models.finding import Finding
from app.models.assessment import Assessment
from app.services.ai_frameworks import calculate_ai_framework_coverage, AI_FRAMEWORK_TOTALS

# Use in-memory SQLite for tests
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_calculate_ai_framework_coverage_empty(db):
    org_id = "org_empty"
    result = calculate_ai_framework_coverage(db, org_id)
    
    assert len(result) == 2
    
    nist = next(f for f in result if f["framework"] == "NIST_AI_RMF")
    assert nist["covered_controls"] == 0
    assert nist["total_controls"] == AI_FRAMEWORK_TOTALS[FrameworkType.NIST_AI_RMF]
    assert nist["coverage_percent"] == 0.0
    
    atlas = next(f for f in result if f["framework"] == "MITRE_ATLAS")
    assert atlas["covered_controls"] == 0
    assert atlas["total_controls"] == AI_FRAMEWORK_TOTALS[FrameworkType.MITRE_ATLAS]
    assert atlas["coverage_percent"] == 0.0

def test_calculate_ai_framework_coverage_with_data(db):
    org_id = "org_with_data"
    
    # Create Assessment
    assessment = Assessment(id="assess_1", organization_id=org_id)
    db.add(assessment)
    
    # Create Finding
    finding1 = Finding(id="find_1", assessment_id="assess_1", title="EDR", severity="low")
    db.add(finding1)
    
    # Create another finding
    finding2 = Finding(id="find_2", assessment_id="assess_1", title="Another", severity="low")
    db.add(finding2)
    
    # Map controls to NIST AI RMF
    db.add(FrameworkMappingRegistry(
        finding_id="find_1", 
        framework_type=FrameworkType.NIST_AI_RMF, 
        control_id="MAP 1.1"
    ))
    db.add(FrameworkMappingRegistry(
        finding_id="find_1", 
        framework_type=FrameworkType.NIST_AI_RMF, 
        control_id="MAP 1.2"
    ))
    # Duplicate control mapped to a different finding shouldn't increase unique count
    db.add(FrameworkMappingRegistry(
        finding_id="find_2", 
        framework_type=FrameworkType.NIST_AI_RMF, 
        control_id="MAP 1.2"
    ))
    
    # Map controls to MITRE ATLAS
    db.add(FrameworkMappingRegistry(
        finding_id="find_2", 
        framework_type=FrameworkType.MITRE_ATLAS, 
        control_id="TA0043"
    ))
    
    db.commit()
    
    result = calculate_ai_framework_coverage(db, org_id)
    
    nist = next(f for f in result if f["framework"] == "NIST_AI_RMF")
    assert nist["covered_controls"] == 2
    assert nist["total_controls"] == 72
    assert nist["coverage_percent"] == round((2 / 72) * 100, 1)
    
    atlas = next(f for f in result if f["framework"] == "MITRE_ATLAS")
    assert atlas["covered_controls"] == 1
    assert atlas["total_controls"] == 14
    assert atlas["coverage_percent"] == round((1 / 14) * 100, 1)
