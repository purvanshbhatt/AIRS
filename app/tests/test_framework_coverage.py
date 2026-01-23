from unittest.mock import MagicMock
from app.services.assessment import AssessmentService
from app.core.frameworks import TOTAL_MITRE_TECHNIQUES, FINDING_FRAMEWORK_MAPPINGS
from app.models.finding import Finding, Severity

def test_mitre_coverage_calculation():
    """Test that MITRE coverage metrics are calculated correctly."""
    # Setup mock service
    service = AssessmentService(MagicMock())
    
    # Create findings that map to MITRE techniques
    # tl_01 maps to T1059, T1071
    findings = [
        Finding(
            id="f1",
            title="Test Gap",
            severity=Severity.HIGH,
            question_id="tl_01",
            domain_name="Telemetry",
            description="Test"
        )
    ]
    
    # Calculate mapping
    result = service._build_framework_mapping(findings)
    coverage = result["coverage"]
    
    # Assertions
    assert coverage["mitre_techniques_total"] == TOTAL_MITRE_TECHNIQUES
    assert coverage["mitre_techniques_referenced"] > 0
    assert len(coverage["mitre_techniques_referenced_list"]) > 0
    
    # Verify exact references for tl_01
    expected_techniques = {"T1059", "T1071"}
    actual_techniques = set(coverage["mitre_techniques_referenced_list"])
    assert expected_techniques.issubset(actual_techniques)

def test_empty_findings_coverage():
    """Test coverage with no findings."""
    service = AssessmentService(MagicMock())
    result = service._build_framework_mapping([])
    
    coverage = result["coverage"]
    assert coverage["mitre_techniques_referenced"] == 0
    assert coverage["mitre_coverage_pct"] == 0.0
    assert coverage["mitre_techniques_referenced_list"] == []
