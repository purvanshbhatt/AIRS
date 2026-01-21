"""
Tenant isolation tests.

These tests verify that users can only access their own data.
User A should not be able to read/update/delete User B's organizations or assessments.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, MagicMock

from app.main import app
from app.db.database import Base, get_db
from app.core.auth import User, require_auth, get_current_user


# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Mock users for testing
USER_A = User(uid="user-a-uid-12345", email="user_a@example.com", name="User A")
USER_B = User(uid="user-b-uid-67890", email="user_b@example.com", name="User B")


def make_auth_override(user: User):
    """Create an auth override for the given user."""
    async def override():
        return user
    return override


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client_user_a(db_session):
    """Create a test client authenticated as User A."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_auth] = make_auth_override(USER_A)
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_user_b(db_session):
    """Create a test client authenticated as User B."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_auth] = make_auth_override(USER_B)
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


class TestOrganizationIsolation:
    """Test that organizations are isolated per user."""
    
    def test_user_a_cannot_see_user_b_organizations(self, db_session):
        """User A should not see User B's organizations in list."""
        # Setup: Override for User A
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create org as User A
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client_a:
            resp = client_a.post("/api/orgs", json={"name": "User A Org"})
            assert resp.status_code == 201
            org_a = resp.json()
        
        # Create org as User B
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client_b:
            resp = client_b.post("/api/orgs", json={"name": "User B Org"})
            assert resp.status_code == 201
            org_b = resp.json()
        
        # User A lists orgs - should only see their own
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client_a:
            resp = client_a.get("/api/orgs")
            assert resp.status_code == 200
            orgs = resp.json()
            assert len(orgs) == 1
            assert orgs[0]["id"] == org_a["id"]
            assert orgs[0]["name"] == "User A Org"
        
        # User B lists orgs - should only see their own
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client_b:
            resp = client_b.get("/api/orgs")
            assert resp.status_code == 200
            orgs = resp.json()
            assert len(orgs) == 1
            assert orgs[0]["id"] == org_b["id"]
            assert orgs[0]["name"] == "User B Org"
        
        app.dependency_overrides.clear()
    
    def test_user_a_cannot_get_user_b_organization_by_id(self, db_session):
        """User A should get 404 when trying to access User B's org by ID."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create org as User B
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client_b:
            resp = client_b.post("/api/orgs", json={"name": "User B Org"})
            assert resp.status_code == 201
            org_b_id = resp.json()["id"]
        
        # User A tries to access User B's org - should get 404
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client_a:
            resp = client_a.get(f"/api/orgs/{org_b_id}")
            assert resp.status_code == 404
        
        app.dependency_overrides.clear()
    
    def test_user_a_cannot_update_user_b_organization(self, db_session):
        """User A should get 404 when trying to update User B's org."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create org as User B
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client_b:
            resp = client_b.post("/api/orgs", json={"name": "User B Org"})
            assert resp.status_code == 201
            org_b_id = resp.json()["id"]
        
        # User A tries to update User B's org - should get 404
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client_a:
            resp = client_a.patch(f"/api/orgs/{org_b_id}", json={"name": "Hacked!"})
            assert resp.status_code == 404
        
        # Verify org was not modified
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client_b:
            resp = client_b.get(f"/api/orgs/{org_b_id}")
            assert resp.status_code == 200
            assert resp.json()["name"] == "User B Org"
        
        app.dependency_overrides.clear()
    
    def test_user_a_cannot_delete_user_b_organization(self, db_session):
        """User A should get 404 when trying to delete User B's org."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create org as User B
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client_b:
            resp = client_b.post("/api/orgs", json={"name": "User B Org"})
            assert resp.status_code == 201
            org_b_id = resp.json()["id"]
        
        # User A tries to delete User B's org - should get 404
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client_a:
            resp = client_a.delete(f"/api/orgs/{org_b_id}")
            assert resp.status_code == 404
        
        # Verify org still exists for User B
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client_b:
            resp = client_b.get(f"/api/orgs/{org_b_id}")
            assert resp.status_code == 200
        
        app.dependency_overrides.clear()


class TestAssessmentIsolation:
    """Test that assessments are isolated per user."""
    
    def test_user_a_cannot_see_user_b_assessments(self, db_session):
        """User A should not see User B's assessments in list."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create org and assessment as User A
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client_a:
            resp = client_a.post("/api/orgs", json={"name": "User A Org"})
            org_a_id = resp.json()["id"]
            resp = client_a.post("/api/assessments", json={
                "organization_id": org_a_id,
                "title": "User A Assessment"
            })
            assert resp.status_code == 201
            assessment_a = resp.json()
        
        # Create org and assessment as User B
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client_b:
            resp = client_b.post("/api/orgs", json={"name": "User B Org"})
            org_b_id = resp.json()["id"]
            resp = client_b.post("/api/assessments", json={
                "organization_id": org_b_id,
                "title": "User B Assessment"
            })
            assert resp.status_code == 201
            assessment_b = resp.json()
        
        # User A lists assessments - should only see their own
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client_a:
            resp = client_a.get("/api/assessments")
            assert resp.status_code == 200
            assessments = resp.json()
            assert len(assessments) == 1
            assert assessments[0]["id"] == assessment_a["id"]
        
        # User B lists assessments - should only see their own
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client_b:
            resp = client_b.get("/api/assessments")
            assert resp.status_code == 200
            assessments = resp.json()
            assert len(assessments) == 1
            assert assessments[0]["id"] == assessment_b["id"]
        
        app.dependency_overrides.clear()
    
    def test_user_a_cannot_get_user_b_assessment_by_id(self, db_session):
        """User A should get 404 when trying to access User B's assessment."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create org and assessment as User B
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client_b:
            resp = client_b.post("/api/orgs", json={"name": "User B Org"})
            org_b_id = resp.json()["id"]
            resp = client_b.post("/api/assessments", json={
                "organization_id": org_b_id,
                "title": "User B Assessment"
            })
            assessment_b_id = resp.json()["id"]
        
        # User A tries to access User B's assessment - should get 404
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client_a:
            resp = client_a.get(f"/api/assessments/{assessment_b_id}")
            assert resp.status_code == 404
        
        app.dependency_overrides.clear()
    
    def test_user_a_cannot_create_assessment_for_user_b_org(self, db_session):
        """User A should get 400 when trying to create assessment for User B's org."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create org as User B
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client_b:
            resp = client_b.post("/api/orgs", json={"name": "User B Org"})
            org_b_id = resp.json()["id"]
        
        # User A tries to create assessment for User B's org - should fail
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client_a:
            resp = client_a.post("/api/assessments", json={
                "organization_id": org_b_id,
                "title": "Malicious Assessment"
            })
            # Should get 400 because org not found (for this user)
            assert resp.status_code == 400
        
        app.dependency_overrides.clear()
    
    def test_user_a_cannot_get_user_b_assessment_summary(self, db_session):
        """User A should get 404 when trying to access User B's assessment summary."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create org and assessment as User B
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client_b:
            resp = client_b.post("/api/orgs", json={"name": "User B Org"})
            org_b_id = resp.json()["id"]
            resp = client_b.post("/api/assessments", json={
                "organization_id": org_b_id,
                "title": "User B Assessment"
            })
            assessment_b_id = resp.json()["id"]
        
        # User A tries to access User B's assessment summary - should get 404
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client_a:
            resp = client_a.get(f"/api/assessments/{assessment_b_id}/summary")
            assert resp.status_code == 404
        
        app.dependency_overrides.clear()
    
    def test_user_a_cannot_download_user_b_report(self, db_session):
        """User A should get 404 when trying to download User B's report."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create org and assessment as User B
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client_b:
            resp = client_b.post("/api/orgs", json={"name": "User B Org"})
            org_b_id = resp.json()["id"]
            resp = client_b.post("/api/assessments", json={
                "organization_id": org_b_id,
                "title": "User B Assessment"
            })
            assessment_b_id = resp.json()["id"]
        
        # User A tries to download User B's report - should get 404
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client_a:
            resp = client_a.get(f"/api/assessments/{assessment_b_id}/report")
            assert resp.status_code == 404
        
        app.dependency_overrides.clear()
    
    def test_user_a_cannot_submit_answers_for_user_b_assessment(self, db_session):
        """User A should get 404 when trying to submit answers for User B's assessment."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create org and assessment as User B
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client_b:
            resp = client_b.post("/api/orgs", json={"name": "User B Org"})
            org_b_id = resp.json()["id"]
            resp = client_b.post("/api/assessments", json={
                "organization_id": org_b_id,
                "title": "User B Assessment"
            })
            assessment_b_id = resp.json()["id"]
        
        # User A tries to submit answers for User B's assessment - should get 404
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client_a:
            resp = client_a.post(f"/api/assessments/{assessment_b_id}/answers", json={
                "answers": [
                    {"question_id": "go_01", "value": "yes"}
                ]
            })
            assert resp.status_code == 404
        
        app.dependency_overrides.clear()
    
    def test_user_a_cannot_compute_score_for_user_b_assessment(self, db_session):
        """User A should get 404 when trying to compute score for User B's assessment."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create org and assessment as User B
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client_b:
            resp = client_b.post("/api/orgs", json={"name": "User B Org"})
            org_b_id = resp.json()["id"]
            resp = client_b.post("/api/assessments", json={
                "organization_id": org_b_id,
                "title": "User B Assessment"
            })
            assessment_b_id = resp.json()["id"]
        
        # User A tries to compute score for User B's assessment - should get 404
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client_a:
            resp = client_a.post(f"/api/assessments/{assessment_b_id}/score")
            assert resp.status_code == 404
        
        app.dependency_overrides.clear()


class TestOwnerUidAssignment:
    """Test that owner_uid is correctly assigned on create."""
    
    def test_organization_has_owner_uid(self, db_session):
        """Created organization should have owner_uid set."""
        from app.models.organization import Organization
        
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        
        with TestClient(app) as client:
            resp = client.post("/api/orgs", json={"name": "Test Org"})
            assert resp.status_code == 201
            org_id = resp.json()["id"]
        
        # Verify in database
        org = db_session.query(Organization).filter(Organization.id == org_id).first()
        assert org is not None
        assert org.owner_uid == USER_A.uid
        
        app.dependency_overrides.clear()
    
    def test_assessment_has_owner_uid(self, db_session):
        """Created assessment should have owner_uid set."""
        from app.models.assessment import Assessment
        
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        
        with TestClient(app) as client:
            # Create org first
            resp = client.post("/api/orgs", json={"name": "Test Org"})
            org_id = resp.json()["id"]
            
            # Create assessment
            resp = client.post("/api/assessments", json={
                "organization_id": org_id,
                "title": "Test Assessment"
            })
            assert resp.status_code == 201
            assessment_id = resp.json()["id"]
        
        # Verify in database
        assessment = db_session.query(Assessment).filter(Assessment.id == assessment_id).first()
        assert assessment is not None
        assert assessment.owner_uid == USER_A.uid
        
        app.dependency_overrides.clear()
