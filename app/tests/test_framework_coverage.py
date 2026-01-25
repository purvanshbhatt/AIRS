from unittest.mock import MagicMock
from app.services.assessment import AssessmentService
from app.core.frameworks import TOTAL_MITRE_TECHNIQUES, FINDING_FRAMEWORK_MAPPINGS, OWASP_REFS
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
    assert coverage["owasp_referenced"] == 0


def test_owasp_coverage_calculation():
    """Test that OWASP coverage metrics are calculated correctly."""
    service = AssessmentService(MagicMock())
    
    # Create a finding that maps to OWASP (iv_01 maps to OWASP A01:2021)
    findings = [
        Finding(
            id="f1",
            title="Test Gap",
            severity=Severity.HIGH,
            question_id="iv_01",
            domain_name="Identity",
            description="Test"
        )
    ]
    
    result = service._build_framework_mapping(findings)
    coverage = result["coverage"]
    
    # Verify OWASP coverage
    assert "owasp_referenced" in coverage
    assert "owasp_total" in coverage
    assert coverage["owasp_total"] == len(OWASP_REFS)
    assert isinstance(coverage["owasp_coverage_pct"], (int, float))
    assert "owasp_referenced_list" in coverage


def test_framework_mapping_includes_all_refs():
    """Test that each mapped finding includes all framework ref arrays."""
    service = AssessmentService(MagicMock())
    
    # Use a finding that has known mappings
    findings = [
        Finding(
            id="f1",
            title="Test Gap",
            severity=Severity.HIGH,
            question_id="iv_01",
            domain_name="Identity",
            description="Test"
        )
    ]
    
    result = service._build_framework_mapping(findings)
    
    # Check that findings structure has all ref arrays
    for finding in result["findings"]:
        assert "mitre_refs" in finding
        assert "cis_refs" in finding
        assert "owasp_refs" in finding
        assert isinstance(finding["mitre_refs"], list)
        assert isinstance(finding["cis_refs"], list)
        assert isinstance(finding["owasp_refs"], list)


def test_mitre_ref_structure():
    """Test that MITRE refs include all required fields (id, name, tactic, url)."""
    service = AssessmentService(MagicMock())
    
    # tl_01 has known MITRE mappings
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
    
    result = service._build_framework_mapping(findings)
    
    # Find a finding with MITRE refs
    for finding in result["findings"]:
        for mitre_ref in finding["mitre_refs"]:
            assert "id" in mitre_ref, "MITRE ref missing 'id'"
            assert "name" in mitre_ref, "MITRE ref missing 'name'"
            assert "tactic" in mitre_ref, "MITRE ref missing 'tactic'"
            assert "url" in mitre_ref, "MITRE ref missing 'url'"
            # Verify URL format
            assert mitre_ref["url"].startswith("https://attack.mitre.org/")


def test_seeded_assessment_has_nonzero_mitre():
    """For a seeded assessment with mapped question_ids, MITRE count > 0."""
    service = AssessmentService(MagicMock())
    
    # Create multiple findings with known mapped question_ids
    mapped_question_ids = []
    for qid in FINDING_FRAMEWORK_MAPPINGS.keys():
        if FINDING_FRAMEWORK_MAPPINGS[qid].get("mitre"):
            mapped_question_ids.append(qid)
            if len(mapped_question_ids) >= 3:
                break
    
    findings = [
        Finding(
            id=f"f{i}",
            title=f"Finding {i}",
            severity=Severity.HIGH,
            question_id=qid,
            domain_name="Test",
            description="Test"
        )
        for i, qid in enumerate(mapped_question_ids)
    ]
    
    result = service._build_framework_mapping(findings)
    coverage = result["coverage"]
    
    # Assert MITRE referenced count is > 0
    assert coverage["mitre_techniques_referenced"] > 0, \
        f"Expected MITRE count > 0 for mapped questions {mapped_question_ids}, got {coverage['mitre_techniques_referenced']}"
    assert len(coverage["mitre_techniques_referenced_list"]) > 0
