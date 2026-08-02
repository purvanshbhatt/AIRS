import pytest
from app.models.organization import Organization
from sqlalchemy.orm import Session

def test_organization_clone_fields_defaults(db_session: Session):
    org = Organization(name="Test Org")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    assert org.is_clone is False
    assert org.source_org_id is None

def test_organization_clone_fields_set(db_session: Session):
    org1 = Organization(name="Source Org")
    db_session.add(org1)
    db_session.commit()
    db_session.refresh(org1)

    org2 = Organization(name="Clone Org", is_clone=True, source_org_id=org1.id)
    db_session.add(org2)
    db_session.commit()
    db_session.refresh(org2)

    assert org2.is_clone is True
    assert org2.source_org_id == org1.id
