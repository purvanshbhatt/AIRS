import pytest
from app.models.organization import Organization
from app.models.assessment import Assessment, AssessmentStatus
from app.models.finding import Finding, Severity, FindingStatus
from app.models.finding_provenance import FindingProvenance, ProvenanceStatus, VerificationSource


def test_telemetry_roi_metrics_endpoint_no_data(client):
    """Test retrieving ROI metrics when no assessment or findings exist."""
    org_resp = client.post("/api/orgs", json={"name": "ROI Org No Data"})
    assert org_resp.status_code == 201
    org_id = org_resp.json()["id"]

    roi_resp = client.get(f"/api/v1/telemetry/roi-metrics?org_id={org_id}")
    assert roi_resp.status_code == 200
    data = roi_resp.json()
    
    # Fallback checks (25 controls * 4 hours = 100)
    assert data["base_manual_hours"] == 100
    assert data["automated_hours"] == 0
    assert data["hours_saved"] == 0
    assert data["revenue_protected"] == 250000
    assert data["total_controls"] == 25
    assert data["automated_controls"] == 0


def test_telemetry_roi_metrics_endpoint_with_findings(client, db_session):
    """Test ROI metrics when an assessment exists with findings and provenances."""
    # 1. Create organization
    org = Organization(name="ROI Org With Findings")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    # 2. Create completed assessment
    assessment = Assessment(
        organization_id=org.id,
        title="Active Assessment",
        status=AssessmentStatus.COMPLETED,
        overall_score=82.0,  # Map to $1.0M revenue protected (>=75)
    )
    db_session.add(assessment)
    db_session.commit()
    db_session.refresh(assessment)

    # 3. Create 5 findings
    findings = []
    for i in range(5):
        finding = Finding(
            assessment_id=assessment.id,
            title=f"Finding {i}",
            severity=Severity.HIGH,
            status=FindingStatus.OPEN,
            nist_category=f"DE.CM-{i}",
        )
        db_session.add(finding)
        findings.append(finding)
    db_session.commit()
    for finding in findings:
        db_session.refresh(finding)

    # 4. Promote 2 findings to SOC_VERIFIED provenance
    prov1 = FindingProvenance(
        finding_id=findings[0].id,
        siem_alert_id="alert-1",
        evidence_hash="hash1",
        verification_source=VerificationSource.SIEM_SPLUNK,
        verification_status=ProvenanceStatus.SOC_VERIFIED,
    )
    prov2 = FindingProvenance(
        finding_id=findings[1].id,
        siem_alert_id="alert-2",
        evidence_hash="hash2",
        verification_source=VerificationSource.SIEM_WAZUH,
        verification_status=ProvenanceStatus.SOC_VERIFIED,
    )
    db_session.add_all([prov1, prov2])
    db_session.commit()

    # 5. Query the ROI metrics API
    # Since we are using client, the test client already uses the shared DB session
    response = client.get(f"/api/v1/telemetry/roi-metrics?org_id={org.id}")
    assert response.status_code == 200
    data = response.json()

    # Math validations:
    # Total findings = 5
    # Automated findings = 2
    # Base manual hours = 5 * 4 = 20
    # Automated hours = 2 * 4 = 8
    # Hours saved = 20 - (20 - 8) = 8
    # Score GHI is 82.0 (from latest completed assessment) -> Revenue Protected = $1,000,000 (>=75)
    assert data["total_controls"] == 5
    assert data["automated_controls"] == 2
    assert data["base_manual_hours"] == 20
    assert data["automated_hours"] == 8
    assert data["hours_saved"] == 8
    assert data["revenue_protected"] == 1000000
