"""
Report tests.

Tests for persistent report generation, listing, retrieval, and tenant isolation.
"""

import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.database import Base, get_db
from app.core.auth import User, require_auth


# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Mock users for testing
USER_A = User(uid="user-a-uid-reports", email="user_a@example.com", name="User A")
USER_B = User(uid="user-b-uid-reports", email="user_b@example.com", name="User B")


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
def setup_user_a_assessment(db_session):
    """Create an organization and scored assessment for User A."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_auth] = make_auth_override(USER_A)
    
    with TestClient(app) as client:
        # Create org
        org_resp = client.post("/api/orgs", json={"name": "User A Org"})
        assert org_resp.status_code == 201
        org = org_resp.json()
        
        # Create assessment
        assessment_resp = client.post("/api/assessments", json={
            "organization_id": org["id"],
            "title": "User A Assessment"
        })
        assert assessment_resp.status_code == 201
        assessment = assessment_resp.json()
        
        # Submit answers (minimal set)
        answers = [
            {"question_id": "tl_01", "value": "yes"},
            {"question_id": "tl_02", "value": "75"},
            {"question_id": "dc_01", "value": "yes"},
            {"question_id": "id_01", "value": "yes"},
            {"question_id": "ir_01", "value": "yes"},
            {"question_id": "rs_01", "value": "yes"},
        ]
        client.post(f"/api/assessments/{assessment['id']}/answers", json={"answers": answers})
        
        # Compute score
        score_resp = client.post(f"/api/assessments/{assessment['id']}/score")
        assert score_resp.status_code == 200
        
        yield {"org": org, "assessment": assessment}
    
    app.dependency_overrides.clear()


class TestReportCreation:
    """Test report creation endpoints."""
    
    def test_create_report_success(self, db_session, setup_user_a_assessment):
        """Successfully create a report for a scored assessment."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        
        with TestClient(app) as client:
            assessment_id = setup_user_a_assessment["assessment"]["id"]
            
            # Create report
            resp = client.post(f"/api/assessments/{assessment_id}/reports", json={
                "report_type": "executive_pdf",
                "title": "Q1 2026 Assessment Report"
            })
            
            assert resp.status_code == 201
            report = resp.json()
            assert report["id"] is not None
            assert report["assessment_id"] == assessment_id
            assert report["title"] == "Q1 2026 Assessment Report"
            assert report["report_type"] == "executive_pdf"
            assert report["overall_score"] is not None
        
        app.dependency_overrides.clear()
    
    def test_create_report_unscored_assessment_fails(self, db_session):
        """Creating a report for an unscored assessment should fail."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        
        with TestClient(app) as client:
            # Create org
            org_resp = client.post("/api/orgs", json={"name": "Test Org"})
            org = org_resp.json()
            
            # Create assessment (no scoring)
            assessment_resp = client.post("/api/assessments", json={
                "organization_id": org["id"],
                "title": "Unscored Assessment"
            })
            assessment = assessment_resp.json()
            
            # Try to create report - should fail
            resp = client.post(f"/api/assessments/{assessment['id']}/reports", json={})
            assert resp.status_code == 400
            # The error response could have 'detail' key or contain error info differently
            response_data = resp.json()
            assert "detail" in response_data or "error" in response_data
            if "detail" in response_data:
                assert "not been scored" in response_data["detail"].lower()
        
        app.dependency_overrides.clear()
    
    def test_create_report_assessment_not_found(self, db_session):
        """Creating a report for non-existent assessment should fail."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        
        with TestClient(app) as client:
            resp = client.post("/api/assessments/nonexistent-id/reports", json={})
            assert resp.status_code == 404
        
        app.dependency_overrides.clear()


class TestReportListing:
    """Test report listing endpoint."""
    
    def test_list_reports_empty(self, db_session):
        """Listing reports when none exist should return empty list."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        
        with TestClient(app) as client:
            resp = client.get("/api/reports")
            assert resp.status_code == 200
            data = resp.json()
            assert data["reports"] == []
            assert data["total"] == 0
        
        app.dependency_overrides.clear()
    
    def test_list_reports_with_filters(self, db_session, setup_user_a_assessment):
        """List reports with organization filter."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        
        with TestClient(app) as client:
            assessment_id = setup_user_a_assessment["assessment"]["id"]
            org_id = setup_user_a_assessment["org"]["id"]
            
            # Create a report
            client.post(f"/api/assessments/{assessment_id}/reports", json={})
            
            # List all reports
            resp = client.get("/api/reports")
            assert resp.status_code == 200
            assert resp.json()["total"] == 1
            
            # Filter by org
            resp = client.get(f"/api/reports?organization_id={org_id}")
            assert resp.status_code == 200
            assert resp.json()["total"] == 1
            
            # Filter by non-existent org
            resp = client.get("/api/reports?organization_id=nonexistent")
            assert resp.status_code == 200
            assert resp.json()["total"] == 0
        
        app.dependency_overrides.clear()


class TestReportRetrieval:
    """Test report retrieval endpoints."""
    
    def test_get_report_with_snapshot(self, db_session, setup_user_a_assessment):
        """Get report with full snapshot data."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        
        with TestClient(app) as client:
            assessment_id = setup_user_a_assessment["assessment"]["id"]
            
            # Create report
            create_resp = client.post(f"/api/assessments/{assessment_id}/reports", json={})
            report_id = create_resp.json()["id"]
            
            # Get report
            resp = client.get(f"/api/reports/{report_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == report_id
            assert "snapshot" in data
            assert data["snapshot"]["assessment_id"] == assessment_id
            assert "domain_scores" in data["snapshot"]
            assert "findings" in data["snapshot"]
        
        app.dependency_overrides.clear()
    
    def test_get_report_not_found(self, db_session):
        """Get non-existent report should return 404."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        
        with TestClient(app) as client:
            resp = client.get("/api/reports/nonexistent-id")
            assert resp.status_code == 404
        
        app.dependency_overrides.clear()


class TestReportDownload:
    """Test report download endpoint."""
    
    def test_download_report_pdf(self, db_session, setup_user_a_assessment):
        """Download report as PDF."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        
        with TestClient(app) as client:
            assessment_id = setup_user_a_assessment["assessment"]["id"]
            
            # Create report
            create_resp = client.post(f"/api/assessments/{assessment_id}/reports", json={})
            report_id = create_resp.json()["id"]
            
            # Download
            resp = client.get(f"/api/reports/{report_id}/download")
            assert resp.status_code == 200
            assert resp.headers["content-type"] == "application/pdf"
            assert "attachment" in resp.headers.get("content-disposition", "")
        
        app.dependency_overrides.clear()


class TestReportTenantIsolation:
    """Test that reports are properly isolated per user."""
    
    def test_user_b_cannot_see_user_a_reports(self, db_session, setup_user_a_assessment):
        """User B should not see User A's reports in list."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create report as User A
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client:
            assessment_id = setup_user_a_assessment["assessment"]["id"]
            client.post(f"/api/assessments/{assessment_id}/reports", json={})
        
        # User B lists reports - should be empty
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client:
            resp = client.get("/api/reports")
            assert resp.status_code == 200
            assert resp.json()["total"] == 0
        
        app.dependency_overrides.clear()
    
    def test_user_b_cannot_access_user_a_report_by_id(self, db_session, setup_user_a_assessment):
        """User B should get 404 when trying to access User A's report."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create report as User A
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client:
            assessment_id = setup_user_a_assessment["assessment"]["id"]
            create_resp = client.post(f"/api/assessments/{assessment_id}/reports", json={})
            report_id = create_resp.json()["id"]
        
        # User B tries to access - should get 404
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client:
            resp = client.get(f"/api/reports/{report_id}")
            assert resp.status_code == 404
        
        app.dependency_overrides.clear()
    
    def test_user_b_cannot_download_user_a_report(self, db_session, setup_user_a_assessment):
        """User B should get 404 when trying to download User A's report."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create report as User A
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client:
            assessment_id = setup_user_a_assessment["assessment"]["id"]
            create_resp = client.post(f"/api/assessments/{assessment_id}/reports", json={})
            report_id = create_resp.json()["id"]
        
        # User B tries to download - should get 404
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client:
            resp = client.get(f"/api/reports/{report_id}/download")
            assert resp.status_code == 404
        
        app.dependency_overrides.clear()
    
    def test_user_b_cannot_delete_user_a_report(self, db_session, setup_user_a_assessment):
        """User B should get 404 when trying to delete User A's report."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Create report as User A
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client:
            assessment_id = setup_user_a_assessment["assessment"]["id"]
            create_resp = client.post(f"/api/assessments/{assessment_id}/reports", json={})
            report_id = create_resp.json()["id"]
        
        # User B tries to delete - should get 404
        app.dependency_overrides[require_auth] = make_auth_override(USER_B)
        with TestClient(app) as client:
            resp = client.delete(f"/api/reports/{report_id}")
            assert resp.status_code == 404
        
        # Verify report still exists for User A
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        with TestClient(app) as client:
            resp = client.get(f"/api/reports/{report_id}")
            assert resp.status_code == 200
        
        app.dependency_overrides.clear()


class TestReportDeletion:
    """Test report deletion."""
    
    def test_delete_report_success(self, db_session, setup_user_a_assessment):
        """Successfully delete a report."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        
        with TestClient(app) as client:
            assessment_id = setup_user_a_assessment["assessment"]["id"]
            
            # Create report
            create_resp = client.post(f"/api/assessments/{assessment_id}/reports", json={})
            report_id = create_resp.json()["id"]
            
            # Delete
            resp = client.delete(f"/api/reports/{report_id}")
            assert resp.status_code == 204
            
            # Verify deleted
            resp = client.get(f"/api/reports/{report_id}")
            assert resp.status_code == 404
        
        app.dependency_overrides.clear()


class TestPDFBranding:
    """Test PDF report branding and content."""
    
    def test_pdf_generator_uses_correct_branding(self):
        """Verify ProfessionalPDFGenerator uses 'AI Incident Readiness Score' branding.
        
        This is a unit test that checks the generated PDF contains the correct
        branding by inspecting the title page builder method directly.
        """
        from app.reports.pdf import ProfessionalPDFGenerator
        import inspect
        
        # Get the source code of _build_title_page to verify branding text
        source = inspect.getsource(ProfessionalPDFGenerator._build_title_page)
        
        # Check for new branding
        assert "AI Incident Readiness Score" in source, \
            "PDF generator should contain 'AI Incident Readiness Score' branding"
        
        # Ensure old branding is NOT present
        assert "Artificial Intelligence Readiness Score" not in source, \
            "PDF generator should NOT contain old 'Artificial Intelligence Readiness Score' branding"
    
    def test_pdf_report_generates_successfully(self, db_session, setup_user_a_assessment):
        """Verify PDF report can be generated and has correct content type."""
        def override_get_db():
            try:
                yield db_session
            finally:
                pass
        
        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[require_auth] = make_auth_override(USER_A)
        
        with TestClient(app) as client:
            assessment_id = setup_user_a_assessment["assessment"]["id"]
            
            # Download PDF report (legacy endpoint)
            resp = client.get(f"/api/assessments/{assessment_id}/report")
            assert resp.status_code == 200
            assert resp.headers["content-type"] == "application/pdf"
            
            # Verify it's a valid PDF (starts with %PDF-)
            assert resp.content.startswith(b'%PDF-'), "Response should be a valid PDF"
        
        app.dependency_overrides.clear()
