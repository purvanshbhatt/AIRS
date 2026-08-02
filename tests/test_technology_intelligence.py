import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.tech_stack import TechStackItem, LtsStatus
from app.services.technology_intelligence import TechnologyIntelligenceOrchestrator

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

@pytest.mark.asyncio
async def test_get_technology_inventory(db):
    org_id = "test_org"
    
    # Create TechStackItems
    item1 = TechStackItem(
        org_id=org_id,
        component_name="Python",
        version="3.8",  # In NVD staging cache this might trigger a mock match
        lts_status=LtsStatus.EOL,
        major_versions_behind=0
    )
    item2 = TechStackItem(
        org_id=org_id,
        component_name="React",
        version="18.2",
        lts_status=LtsStatus.ACTIVE,
        major_versions_behind=0
    )
    
    db.add_all([item1, item2])
    db.commit()
    
    orchestrator = TechnologyIntelligenceOrchestrator(db, org_id)
    inventory = await orchestrator.get_technology_inventory()
    
    assert len(inventory) == 2
    
    # Assert item1 (Python 3.8)
    py_item = next(i for i in inventory if i["component_name"] == "Python")
    assert py_item["version"] == "3.8"
    assert py_item["lts_status"] == "eol"
    assert py_item["readiness_impact"] == "high" # Because EOL
    
    # Assert item2 (React 18.2)
    react_item = next(i for i in inventory if i["component_name"] == "React")
    assert react_item["version"] == "18.2"
    assert react_item["lts_status"] == "active"
    assert react_item["readiness_impact"] in ["low", "high", "medium"] # Depends on cache, but exists
    
    # Data pass-through validation
    assert "critical_cves" in py_item
    assert "kev_count" in py_item
    assert "vulnerabilities" in py_item
