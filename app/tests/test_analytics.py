import pytest
from app.services.analytics import get_full_analytics, ATTACK_PATH_PATTERNS
from app.services.findings import Finding, Severity

def test_analytics_empty_findings():
    """Test analytics with no findings."""
    analytics = get_full_analytics([])
    assert analytics["attack_paths"] == []
    assert analytics["risk_summary"]["findings_count"] == 0
    assert analytics["risk_summary"]["total_risk_score"] == 0

def test_analytics_ransomware_path():
    """Test that Ransomware attack path is triggered by specific findings."""
    # Create findings that trigger the Ransomware path (need RS-001, RS-002, RS-003)
    findings = [
        Finding(
            rule_id="RS-001", title="Backups Not Tested", severity=Severity.HIGH, 
            domain_id="resilience", domain_name="Resilience", 
            evidence="Ev 1", recommendation="Rec 1"
        ),
        Finding(
            rule_id="RS-002", title="Backups Not Immutable", severity=Severity.HIGH, 
            domain_id="resilience", domain_name="Resilience", 
            evidence="Ev 2", recommendation="Rec 2"
        ),
        Finding(
            rule_id="RS-003", title="Critical Systems Not Backed Up", severity=Severity.CRITICAL, 
            domain_id="resilience", domain_name="Resilience", 
            evidence="Ev 3", recommendation="Rec 3"
        ),
    ]
    
    analytics = get_full_analytics(findings)
    
    # Check Attack Paths
    paths = analytics["attack_paths"]
    assert len(paths) >= 1
    ransomware_path = next((p for p in paths if "ransomware" in p["id"]), None)
    assert ransomware_path is not None
    assert ransomware_path["enablement_percentage"] == 100
    
    # Check Risk Summary
    risk = analytics["risk_summary"]
    assert risk["severity_counts"]["critical"] == 1
    assert risk["severity_counts"]["high"] == 2
    assert len(risk["top_risks"]) == 3
    assert risk["total_risk_score"] > 0

def test_risk_summary_sorting():
    """Test that risk summary accurately picks top risks."""
    findings = [
        Finding(
            rule_id="1", title="Low Risk", severity=Severity.LOW, 
            domain_id="d1", domain_name="Domain 1", 
            evidence="e", recommendation="r"
        ),
        Finding(
            rule_id="2", title="Critical Risk", severity=Severity.CRITICAL, 
            domain_id="d1", domain_name="Domain 1", 
            evidence="e", recommendation="r"
        ),
        Finding(
            rule_id="3", title="Medium Risk", severity=Severity.MEDIUM, 
            domain_id="d1", domain_name="Domain 1", 
            evidence="e", recommendation="r"
        ),
    ]
    
    analytics = get_full_analytics(findings)
    top_risks = analytics["risk_summary"]["top_risks"]
    
    assert top_risks[0] == "Critical Risk"
    assert top_risks[1] == "Medium Risk"
    assert top_risks[2] == "Low Risk"
