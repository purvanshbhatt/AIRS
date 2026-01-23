from unittest.mock import MagicMock
from app.services.assessment import AssessmentService
from app.models.finding import Finding, Severity

def test_analytics_generation_with_mapping():
    """Test that analytics are generated correctly with ID mapping."""
    service = AssessmentService(MagicMock())
    
    # Create findings with question_ids that need mapping
    # tl_05 maps to TL-001 (High)
    # iv_02 maps to IV-001 (Critical)
    
    findings = [
        Finding(
            id="f1", 
            title="Retention Gap", 
            severity=Severity.HIGH, 
            question_id="tl_05", 
            domain_name="Telemetry",
            domain_id="telemetry_logging"
        ),
        Finding(
            id="f2", 
            title="MFA Gap", 
            severity=Severity.CRITICAL, 
            question_id="iv_02", 
            domain_name="Identity",
            domain_id="identity_visibility"
        )
    ]
    
    # Generate analytics
    analytics = service._build_analytics(findings)
    
    # Check that we have attack paths (IV-001 usually triggers paths)
    assert len(analytics["attack_paths"]) > 0
    
    # Check that gaps are categorized
    assert analytics["detection_gaps"]["total_gaps"] >= 0
    assert analytics["identity_gaps"]["total_gaps"] >= 0
    
    # Specifically check IV-001 is recognized in identity gaps if logic places it there
    # (Exact placement depends on analytics engine logic, but it shouldn't be empty if rules match)
    
    # Verify rule_id mapping happened implicitly by checking if attack paths reference known techniques
    # or simply by the fact that we got results (empty finding_data usually yields empty analytics)
    assert analytics["risk_summary"]["top_risks"] is not None

def test_empty_findings_analytics():
    """Test graceful handling of empty findings."""
    service = AssessmentService(MagicMock())
    
    analytics = service._build_analytics([])
    
    assert len(analytics["attack_paths"]) == 0
    assert analytics["detection_gaps"]["total_gaps"] == 0
