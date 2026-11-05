"""
Tests for assessment API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.core.config import settings


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

    def test_demo_mode_auto_seeds_demo_org_and_splunk(self, client, monkeypatch, db_session):
        """Verify ensure_demo_seed_data works when invoked explicitly in demo mode.

        NOTE: ensure_demo_seed_data is no longer called from the org/assessment
        listing endpoints (removed to prevent demo contamination in production).
        This test invokes it directly to confirm the function still works.
        """
        monkeypatch.setattr(settings, "DEMO_MODE", True, raising=False)

        # Call demo seed directly (not via org listing)
        from app.services.demo_seed import ensure_demo_seed_data
        ensure_demo_seed_data(db_session, owner_uid="dev-user")

        response = client.get("/api/orgs")
        assert response.status_code == 200
        orgs = response.json()
        assert len(orgs) >= 1
        org_id = orgs[0]["id"]

        findings_resp = client.get(f"/api/integrations/external-findings?source=splunk&limit=1&org_id={org_id}")
        assert findings_resp.status_code == 200
        findings = findings_resp.json()
        assert len(findings) >= 1

    def test_get_org_remediations_returns_items(self, client):
        org_resp = client.post("/api/orgs", json={"name": "Remediation Org"})
        org_id = org_resp.json()["id"]

        assessment_resp = client.post(
            f"/api/orgs/{org_id}/assessments",
            json={"title": "Remediation Baseline"},
        )
        assessment_id = assessment_resp.json()["id"]

        roadmap_resp = client.post(
            f"/api/assessments/{assessment_id}/roadmap",
            json={
                "title": "Close exposed management port",
                "phase": "30",
                "status": "not_started",
                "priority": "high",
            },
        )
        assert roadmap_resp.status_code == 201

        remediations_resp = client.get(f"/api/orgs/{org_id}/remediations")
        assert remediations_resp.status_code == 200
        data = remediations_resp.json()
        assert data["total"] >= 1
        assert any(item["title"] == "Close exposed management port" for item in data["items"])
        target = next(item for item in data["items"] if item["title"] == "Close exposed management port")
        assert target["status"] == "open"

    def test_patch_remediation_updates_status_and_owner(self, client):
        org_resp = client.post("/api/orgs", json={"name": "Remediation Update Org"})
        org_id = org_resp.json()["id"]

        assessment_resp = client.post(
            f"/api/orgs/{org_id}/assessments",
            json={"title": "Remediation Update Baseline"},
        )
        assessment_id = assessment_resp.json()["id"]

        roadmap_resp = client.post(
            f"/api/assessments/{assessment_id}/roadmap",
            json={
                "title": "Restrict stale service account",
                "phase": "30",
                "status": "not_started",
                "priority": "medium",
            },
        )
        assert roadmap_resp.status_code == 201
        item_id = roadmap_resp.json()["id"]

        patch_resp = client.patch(
            f"/api/remediations/{item_id}",
            json={"status": "resolved", "owner": "secops@example.com", "notes": "Validated in staging"},
        )
        assert patch_resp.status_code == 200
        patched = patch_resp.json()
        assert patched["status"] == "resolved"
        assert patched["owner"] == "secops@example.com"
        assert patched["notes"] == "Validated in staging"


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

    def test_lifecycle_start_submit_history_rerun(self, client, org_id):
        # Start directly into in_progress
        start_resp = client.post(f"/api/assessments/{org_id}/start", json={"title": "Lifecycle Start"})
        assert start_resp.status_code == 201
        started = start_resp.json()
        assert started["status"] == "in_progress"

        assessment_id = started["id"]

        # Cannot submit without answers
        submit_empty_resp = client.post(f"/api/assessments/{assessment_id}/submit")
        assert submit_empty_resp.status_code == 400

        # Add answer then submit
        client.post(
            f"/api/assessments/{assessment_id}/answers",
            json={"answers": [{"question_id": "tl_01", "value": "true"}]},
        )
        submit_resp = client.post(f"/api/assessments/{assessment_id}/submit")
        assert submit_resp.status_code == 200
        submit_data = submit_resp.json()
        assert submit_data["status"] == "submitted"

        # History should include this assessment
        history_resp = client.get(f"/api/assessments/{org_id}/history")
        assert history_resp.status_code == 200
        history_items = history_resp.json()
        assert any(item["id"] == assessment_id for item in history_items)

        # Rerun clones into a new in_progress assessment
        rerun_resp = client.post(f"/api/assessments/{assessment_id}/rerun", json={"clone_answers": True})
        assert rerun_resp.status_code == 201
        rerun_data = rerun_resp.json()
        assert rerun_data["status"] == "in_progress"
        assert rerun_data["id"] != assessment_id
        assert rerun_data["version"] != started["version"]
    
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

    def test_update_finding_tracking_fields(self, client, org_id):
        assess_resp = client.post("/api/assessments", json={"organization_id": org_id})
        assessment_id = assess_resp.json()["id"]

        finding_resp = client.post(
            f"/api/assessments/{assessment_id}/findings",
            json={
                "title": "Tracking Finding",
                "severity": "medium",
                "description": "Needs tracking metadata",
            },
        )
        assert finding_resp.status_code == 201
        finding_id = finding_resp.json()["id"]

        patch_resp = client.patch(
            f"/api/assessments/{assessment_id}/findings/{finding_id}",
            json={
                "status": "in_progress",
                "owner": "secops@company.test",
                "due_date": "2026-06-01",
                "control_id": "AC-2",
                "framework_tag": "SOC2",
            },
        )
        assert patch_resp.status_code == 200
        patch_data = patch_resp.json()
        assert patch_data["status"] == "in_progress"
        assert patch_data["owner"] == "secops@company.test"
        assert patch_data["due_date"] == "2026-06-01"
        assert patch_data["control_id"] == "AC-2"
        assert patch_data["framework_tag"] == "SOC2"


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

    def test_generate_executive_summary_success(self, client, scored_assessment):
        response = client.get(f"/api/assessments/{scored_assessment}/executive-summary")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers.get("content-disposition", "")

    def test_export_for_siem_success(self, client, scored_assessment):
        response = client.get(f"/api/assessments/{scored_assessment}/export")
        assert response.status_code == 200
        data = response.json()
        assert data["assessment_id"] == scored_assessment
        assert "organization" in data
        assert "score" in data
        assert "generated_at" in data
        assert isinstance(data["findings"], list)
        if data["findings"]:
            finding = data["findings"][0]
            assert "severity" in finding
            assert "category" in finding
            assert "title" in finding
            assert "mitre_refs" in finding
            assert "cis_refs" in finding
            assert "owasp_refs" in finding
