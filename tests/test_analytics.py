"""
Tests for the analytics service.
"""

import pytest
from app.services.analytics import (
    analyze_attack_paths,
    analyze_detection_gaps,
    analyze_response_gaps,
    analyze_identity_gaps,
    get_full_analytics,
)
from app.services.findings import Finding, Severity


def make_finding(
    rule_id: str,
    title: str,
    severity: Severity,
    domain_id: str,
    domain_name: str,
    evidence: str = "Test evidence",
    recommendation: str = "Test recommendation",
) -> Finding:
    """Helper to create a Finding with all required fields."""
    return Finding(
        rule_id=rule_id,
        title=title,
        severity=severity,
        domain_id=domain_id,
        domain_name=domain_name,
        evidence=evidence,
        recommendation=recommendation,
    )


class TestAttackPathAnalysis:
    """Test attack path analysis."""

    def test_analyze_attack_paths_empty(self):
        """Test with no findings."""
        result = analyze_attack_paths([])
        assert isinstance(result, list)
        assert len(result) == 0

    def test_analyze_attack_paths_credential_compromise(self):
        """Test credential compromise attack path detection."""
        findings = [
            make_finding(
                rule_id="IV-001",  # Matches required_findings in attack path
                title="No MFA for admins",
                severity=Severity.CRITICAL,
                domain_id="identity_visibility",
                domain_name="Identity Visibility",
            ),
            make_finding(
                rule_id="IV-002",
                title="No MFA for users",
                severity=Severity.HIGH,
                domain_id="identity_visibility",
                domain_name="Identity Visibility",
            ),
        ]
        
        result = analyze_attack_paths(findings)
        
        # Should detect credential compromise path
        path_ids = [p["id"] for p in result]
        assert "credential_compromise_to_domain_takeover" in path_ids

    def test_analyze_attack_paths_ransomware(self):
        """Test ransomware attack path detection."""
        findings = [
            make_finding(
                rule_id="RS-001",
                title="No backup testing",
                severity=Severity.HIGH,
                domain_id="resilience",
                domain_name="Resilience",
            ),
            make_finding(
                rule_id="RS-002",
                title="No immutable backups",
                severity=Severity.CRITICAL,
                domain_id="resilience",
                domain_name="Resilience",
            ),
        ]
        
        result = analyze_attack_paths(findings)
        
        path_ids = [p["id"] for p in result]
        assert "ransomware_with_no_recovery" in path_ids

    def test_attack_path_has_required_fields(self):
        """Test that attack paths have all required fields."""
        findings = [
            make_finding(
                rule_id="IV-001",
                title="No MFA",
                severity=Severity.CRITICAL,
                domain_id="identity_visibility",
                domain_name="Identity Visibility",
            ),
        ]
        
        result = analyze_attack_paths(findings)
        
        if result:
            path = result[0]
            assert "id" in path
            assert "name" in path
            assert "risk_level" in path
            assert "impact" in path
            assert "description" in path
            assert "enabling_findings" in path
            assert "techniques" in path


class TestDetectionGapAnalysis:
    """Test detection gap analysis."""

    def test_analyze_detection_gaps_empty(self):
        """Test with no findings."""
        result = analyze_detection_gaps([])
        assert isinstance(result, dict)
        assert result["total_gaps"] == 0
        assert result["categories"] == []

    def test_analyze_detection_gaps_edr(self):
        """Test EDR gap detection."""
        findings = [
            make_finding(
                rule_id="DC-001",
                title="Low EDR coverage",
                severity=Severity.HIGH,
                domain_id="detection_coverage",
                domain_name="Detection Coverage",
            ),
            make_finding(
                rule_id="DC-002",
                title="Critical EDR gap",
                severity=Severity.CRITICAL,
                domain_id="detection_coverage",
                domain_name="Detection Coverage",
            ),
        ]
        
        result = analyze_detection_gaps(findings)
        
        # Should have endpoint_visibility category
        category_names = [c["category"] for c in result["categories"]]
        assert "Endpoint Visibility" in category_names
        
        # Should have gaps
        assert result["total_gaps"] >= 1

    def test_detection_gap_has_required_fields(self):
        """Test detection gaps have required fields."""
        findings = [
            make_finding(
                rule_id="DC-001",
                title="Low EDR coverage",
                severity=Severity.HIGH,
                domain_id="detection_coverage",
                domain_name="Detection Coverage",
            ),
        ]
        
        result = analyze_detection_gaps(findings)
        
        assert "total_gaps" in result
        assert "critical_categories" in result
        assert "categories" in result
        assert "coverage_score" in result
        
        for category in result["categories"]:
            assert "category" in category
            assert "description" in category
            assert "gap_count" in category
            assert "findings" in category


class TestResponseGapAnalysis:
    """Test response gap analysis."""

    def test_analyze_response_gaps_empty(self):
        """Test with no findings."""
        result = analyze_response_gaps([])
        assert isinstance(result, dict)
        assert result["total_gaps"] == 0

    def test_analyze_response_gaps_ir_planning(self):
        """Test IR planning gap detection."""
        findings = [
            make_finding(
                rule_id="IR-001",
                title="No IR playbooks",
                severity=Severity.HIGH,
                domain_id="ir_process",
                domain_name="IR Process",
            ),
        ]
        
        result = analyze_response_gaps(findings)
        
        category_names = [c["category"] for c in result["categories"]]
        assert "IR Planning & Documentation" in category_names

    def test_analyze_response_gaps_backup_recovery(self):
        """Test backup/recovery gap detection."""
        findings = [
            make_finding(
                rule_id="RS-001",
                title="No backup restore testing",
                severity=Severity.MEDIUM,
                domain_id="resilience",
                domain_name="Resilience",
            ),
            make_finding(
                rule_id="RS-002",
                title="No immutable backups",
                severity=Severity.CRITICAL,
                domain_id="resilience",
                domain_name="Resilience",
            ),
        ]
        
        result = analyze_response_gaps(findings)
        
        category_names = [c["category"] for c in result["categories"]]
        assert "Backup & Recovery" in category_names


class TestIdentityGapAnalysis:
    """Test identity gap analysis."""

    def test_analyze_identity_gaps_empty(self):
        """Test with no findings."""
        result = analyze_identity_gaps([])
        assert isinstance(result, dict)
        assert result["total_gaps"] == 0

    def test_analyze_identity_gaps_mfa(self):
        """Test MFA gap detection."""
        findings = [
            make_finding(
                rule_id="IV-001",
                title="No MFA for admins",
                severity=Severity.CRITICAL,
                domain_id="identity_visibility",
                domain_name="Identity Visibility",
            ),
        ]
        
        result = analyze_identity_gaps(findings)
        
        # Should have MFA category
        category_names = [c["category"] for c in result["categories"]]
        assert "Multi-Factor Authentication" in category_names


class TestFullAnalytics:
    """Test the full analytics aggregation."""

    def test_get_full_analytics_empty(self):
        """Test with no findings."""
        result = get_full_analytics([])
        
        assert "attack_paths" in result
        assert "detection_gaps" in result
        assert "response_gaps" in result
        assert "identity_gaps" in result
        assert "framework_summary" in result

    def test_get_full_analytics_comprehensive(self):
        """Test with multiple finding types."""
        findings = [
            make_finding(
                rule_id="IV-001",
                title="No MFA for admins",
                severity=Severity.CRITICAL,
                domain_id="identity_visibility",
                domain_name="Identity Visibility",
            ),
            make_finding(
                rule_id="DC-001",
                title="Low EDR coverage",
                severity=Severity.HIGH,
                domain_id="detection_coverage",
                domain_name="Detection Coverage",
            ),
            make_finding(
                rule_id="RS-002",
                title="No immutable backups",
                severity=Severity.CRITICAL,
                domain_id="resilience",
                domain_name="Resilience",
            ),
            make_finding(
                rule_id="IR-001",
                title="No IR playbooks",
                severity=Severity.HIGH,
                domain_id="ir_process",
                domain_name="IR Process",
            ),
        ]
        
        result = get_full_analytics(findings)
        
        # Should have attack paths
        assert len(result["attack_paths"]) > 0
        
        # Should have detection gaps
        assert result["detection_gaps"]["total_gaps"] > 0
        
        # Should have response gaps
        assert result["response_gaps"]["total_gaps"] > 0
        
        # Should have identity gaps
        assert result["identity_gaps"]["total_gaps"] > 0
        
        # Should have framework summary
        assert "mitre" in result["framework_summary"]
        assert "cis" in result["framework_summary"]

    def test_framework_summary_structure(self):
        """Test that framework summary has proper structure."""
        findings = [
            make_finding(
                rule_id="IV-001",
                title="No MFA for admins",
                severity=Severity.CRITICAL,
                domain_id="identity_visibility",
                domain_name="Identity Visibility",
            ),
        ]
        
        result = get_full_analytics(findings)
        
        mitre = result["framework_summary"]["mitre"]
        assert "techniques_enabled" in mitre
        assert "tactics_affected_count" in mitre
        assert "tactics_affected" in mitre
        
        cis = result["framework_summary"]["cis"]
        assert "controls_missing" in cis
        assert "ig1_missing" in cis
        assert "ig2_missing" in cis
        assert "ig3_missing" in cis
