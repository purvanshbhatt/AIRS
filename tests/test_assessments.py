"""
Tests for assessment API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class TestOrganizations:
    """Tests for organization endpoints."""
    
    def test_create_organization(self, client):
        response = client.post("/api/orgs", json={
            "name": "Test Company",
            "industry": "Technology",
            "size": "51-200",
            "contact_email": "test@example.com"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Company"
        assert "id" in data
    
    def test_list_organizations(self, client):
        # Create one first
        client.post("/api/orgs", json={"name": "Org 1"})
        
        response = client.get("/api/orgs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_organization(self, client):
        # Create
        create_resp = client.post("/api/orgs", json={"name": "Get Test Org"})
        org_id = create_resp.json()["id"]
        
        # Get
        response = client.get(f"/api/orgs/{org_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Get Test Org"
    
    def test_get_organization_not_found(self, client):
        response = client.get("/api/orgs/non-existent-id")
        assert response.status_code == 404
    
    def test_delete_organization(self, client):
        # Create
        create_resp = client.post("/api/orgs", json={"name": "Delete Test"})
        org_id = create_resp.json()["id"]
        
        # Delete
        response = client.delete(f"/api/orgs/{org_id}")
        assert response.status_code == 204
        
        # Verify deleted
        response = client.get(f"/api/orgs/{org_id}")
        assert response.status_code == 404


class TestAssessments:
    """Tests for assessment endpoints."""
    
    @pytest.fixture
    def org_id(self, client):
        response = client.post("/api/orgs", json={"name": "Assessment Test Org"})
        return response.json()["id"]
    
    def test_create_assessment(self, client, org_id):
        response = client.post("/api/assessments", json={
            "organization_id": org_id,
            "title": "Q1 2026 Assessment"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["organization_id"] == org_id
        assert data["status"] == "draft"
    
    def test_create_assessment_invalid_org(self, client):
        response = client.post("/api/assessments", json={
            "organization_id": "invalid-org-id"
        })
        assert response.status_code == 400
    
    def test_submit_answers(self, client, org_id):
        # Create assessment
        assess_resp = client.post("/api/assessments", json={
            "organization_id": org_id
        })
        assessment_id = assess_resp.json()["id"]
        
        # Submit answers
        response = client.post(f"/api/assessments/{assessment_id}/answers", json={
            "answers": [
                {"question_id": "tl_01", "value": "true"},
                {"question_id": "tl_02", "value": "true"},
                {"question_id": "tl_05", "value": "90"}
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
    
    def test_compute_score(self, client, org_id):
        # Create assessment
        assess_resp = client.post("/api/assessments", json={
            "organization_id": org_id
        })
        assessment_id = assess_resp.json()["id"]
        
        # Submit all answers
        answers = [
            {"question_id": "tl_01", "value": "true"},
            {"question_id": "tl_02", "value": "true"},
            {"question_id": "tl_03", "value": "false"},
            {"question_id": "tl_04", "value": "true"},
            {"question_id": "tl_05", "value": "90"},
            {"question_id": "tl_06", "value": "true"},
            {"question_id": "dc_01", "value": "85"},
            {"question_id": "dc_02", "value": "true"},
            {"question_id": "dc_03", "value": "true"},
            {"question_id": "dc_04", "value": "false"},
            {"question_id": "dc_05", "value": "true"},
            {"question_id": "dc_06", "value": "true"},
            {"question_id": "iv_01", "value": "false"},
            {"question_id": "iv_02", "value": "true"},
            {"question_id": "iv_03", "value": "true"},
            {"question_id": "iv_04", "value": "false"},
            {"question_id": "iv_05", "value": "false"},
            {"question_id": "iv_06", "value": "true"},
            {"question_id": "ir_01", "value": "true"},
            {"question_id": "ir_02", "value": "false"},
            {"question_id": "ir_03", "value": "true"},
            {"question_id": "ir_04", "value": "true"},
            {"question_id": "ir_05", "value": "true"},
            {"question_id": "ir_06", "value": "false"},
            {"question_id": "rs_01", "value": "true"},
            {"question_id": "rs_02", "value": "true"},
            {"question_id": "rs_03", "value": "false"},
            {"question_id": "rs_04", "value": "true"},
            {"question_id": "rs_05", "value": "24"},
            {"question_id": "rs_06", "value": "true"},
        ]
        client.post(f"/api/assessments/{assessment_id}/answers", json={"answers": answers})
        
        # Compute score
        response = client.post(f"/api/assessments/{assessment_id}/score")
        assert response.status_code == 200
        data = response.json()
        
        assert "overall_score" in data
        assert 0 <= data["overall_score"] <= 100
        assert "maturity_level" in data
        assert len(data["domain_scores"]) == 5
        assert "findings_count" in data
    
    def test_get_assessment_detail(self, client, org_id):
        # Create and score assessment
        assess_resp = client.post("/api/assessments", json={
            "organization_id": org_id
        })
        assessment_id = assess_resp.json()["id"]
        
        # Get detail
        response = client.get(f"/api/assessments/{assessment_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert "answers" in data
        assert "scores" in data
        assert "findings" in data
    
    def test_get_findings(self, client, org_id):
        # Create assessment
        assess_resp = client.post("/api/assessments", json={
            "organization_id": org_id
        })
        assessment_id = assess_resp.json()["id"]
        
        # Submit partial answers and score
        answers = [{"question_id": "tl_01", "value": "false"}]
        client.post(f"/api/assessments/{assessment_id}/answers", json={"answers": answers})
        client.post(f"/api/assessments/{assessment_id}/score")
        
        # Get findings
        response = client.get(f"/api/assessments/{assessment_id}/findings")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_add_manual_finding(self, client, org_id):
        # Create assessment
        assess_resp = client.post("/api/assessments", json={
            "organization_id": org_id
        })
        assessment_id = assess_resp.json()["id"]
        
        # Add finding
        response = client.post(f"/api/assessments/{assessment_id}/findings", json={
            "title": "Manual Finding",
            "severity": "high",
            "description": "This was observed manually",
            "recommendation": "Fix this issue"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Manual Finding"
        assert data["severity"] == "high"


class TestReports:
    """Tests for report generation."""
    
    @pytest.fixture
    def scored_assessment(self, client):
        # Create org
        org_resp = client.post("/api/orgs", json={"name": "Report Test Org"})
        org_id = org_resp.json()["id"]
        
        # Create assessment
        assess_resp = client.post("/api/assessments", json={
            "organization_id": org_id,
            "title": "Report Test Assessment"
        })
        assessment_id = assess_resp.json()["id"]
        
        # Submit all 30 answers explicitly
        answers = [
            {"question_id": "tl_01", "value": "true"},
            {"question_id": "tl_02", "value": "true"},
            {"question_id": "tl_03", "value": "true"},
            {"question_id": "tl_04", "value": "true"},
            {"question_id": "tl_05", "value": "90"},
            {"question_id": "tl_06", "value": "true"},
            {"question_id": "dc_01", "value": "85"},
            {"question_id": "dc_02", "value": "true"},
            {"question_id": "dc_03", "value": "true"},
            {"question_id": "dc_04", "value": "true"},
            {"question_id": "dc_05", "value": "true"},
            {"question_id": "dc_06", "value": "true"},
            {"question_id": "iv_01", "value": "true"},
            {"question_id": "iv_02", "value": "true"},
            {"question_id": "iv_03", "value": "true"},
            {"question_id": "iv_04", "value": "true"},
            {"question_id": "iv_05", "value": "true"},
            {"question_id": "iv_06", "value": "true"},
            {"question_id": "ir_01", "value": "true"},
            {"question_id": "ir_02", "value": "true"},
            {"question_id": "ir_03", "value": "true"},
            {"question_id": "ir_04", "value": "true"},
            {"question_id": "ir_05", "value": "true"},
            {"question_id": "ir_06", "value": "true"},
            {"question_id": "rs_01", "value": "true"},
            {"question_id": "rs_02", "value": "true"},
            {"question_id": "rs_03", "value": "true"},
            {"question_id": "rs_04", "value": "true"},
            {"question_id": "rs_05", "value": "4"},
            {"question_id": "rs_06", "value": "true"},
        ]
        
        client.post(f"/api/assessments/{assessment_id}/answers", json={"answers": answers})
        
        # Score
        client.post(f"/api/assessments/{assessment_id}/score")
        
        return assessment_id
    
    def test_generate_report_not_scored(self, client):
        # Create org and assessment
        org_resp = client.post("/api/orgs", json={"name": "Unscored Org"})
        org_id = org_resp.json()["id"]
        assess_resp = client.post("/api/assessments", json={"organization_id": org_id})
        assessment_id = assess_resp.json()["id"]
        
        # Try to generate report without scoring
        response = client.get(f"/api/assessments/{assessment_id}/report")
        assert response.status_code == 400
    
    def test_generate_report_success(self, client, scored_assessment):
        response = client.get(f"/api/assessments/{scored_assessment}/report")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers.get("content-disposition", "")
