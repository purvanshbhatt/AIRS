"""
Tests for AIRS Framework Mapping functionality.

Verifies that:
1. Every finding has framework_refs with mitre, cis, owasp arrays
2. Known findings have non-empty MITRE technique mappings
3. Analytics generate properly from findings
4. Roadmap generates correctly from findings
"""

import pytest
from app.core.frameworks import (
    get_framework_refs,
    get_all_unique_techniques,
    FRAMEWORK_MAPPINGS,
    MITRE_TECHNIQUES,
    CIS_CONTROLS,
    OWASP_TOP10
)
from app.services.findings import FindingsEngine, Finding, Severity, FrameworkRefs
from app.services.analytics import (
    generate_analytics,
    analyze_attack_paths,
    analyze_detection_gaps,
    analyze_response_gaps,
    analyze_identity_gaps
)
from app.services.roadmap import (
    generate_detailed_roadmap,
    generate_simple_roadmap,
    get_phase_for_finding
)


class TestFrameworkMappings:
    """Tests for framework mapping data."""
    
    def test_all_finding_rules_have_mapping(self):
        """Every finding rule_id should have a framework mapping entry."""
        known_rules = [
            "TL-001", "TL-002", "TL-003", "TL-004", "TL-005",
            "DC-001", "DC-002", "DC-003", "DC-004", "DC-005", "DC-006",
            "IV-001", "IV-002", "IV-003", "IV-004", "IV-005",
            "IR-001", "IR-002", "IR-003", "IR-004",
            "RS-001", "RS-002", "RS-003", "RS-004", "RS-005", "RS-006",
            "AGG-001", "AGG-002", "AGG-003"
        ]
        
        for rule_id in known_rules:
            assert rule_id in FRAMEWORK_MAPPINGS, f"Missing mapping for {rule_id}"
            mapping = FRAMEWORK_MAPPINGS[rule_id]
            assert "mitre" in mapping, f"Missing mitre key for {rule_id}"
            assert "cis" in mapping, f"Missing cis key for {rule_id}"
            assert "owasp" in mapping, f"Missing owasp key for {rule_id}"
    
    def test_identity_findings_have_mitre_refs(self):
        """Identity-related findings should have non-empty MITRE refs."""
        identity_rules = ["IV-001", "IV-002", "IV-003", "IV-004", "IV-005"]
        
        for rule_id in identity_rules:
            refs = get_framework_refs(rule_id)
            assert len(refs["mitre"]) > 0, f"{rule_id} should have MITRE refs"
            # Check for T1078 or any of its sub-techniques
            mitre_ids = [r["id"] for r in refs["mitre"]]
            has_valid_accounts_ref = any(
                mid == "T1078" or mid.startswith("T1078.") 
                for mid in mitre_ids
            )
            assert has_valid_accounts_ref, f"{rule_id} should reference T1078 or sub-technique (Valid Accounts)"
    
    def test_mfa_finding_has_auth_failure_owasp(self):
        """MFA findings should reference OWASP A07:2021 (Authentication Failures)."""
        mfa_rules = ["IV-001", "IV-002"]
        
        for rule_id in mfa_rules:
            refs = get_framework_refs(rule_id)
            owasp_ids = [r["id"] for r in refs["owasp"]]
            assert "A07:2021" in owasp_ids, f"{rule_id} should reference OWASP A07:2021"
    
    def test_logging_findings_have_log_monitoring_owasp(self):
        """Logging findings should reference OWASP A09:2021 (Logging/Monitoring Failures)."""
        logging_rules = ["TL-001", "TL-002", "TL-003", "TL-004", "TL-005"]
        
        for rule_id in logging_rules:
            refs = get_framework_refs(rule_id)
            owasp_ids = [r["id"] for r in refs["owasp"]]
            assert "A09:2021" in owasp_ids, f"{rule_id} should reference OWASP A09:2021"
    
    def test_backup_findings_have_ransomware_techniques(self):
        """Backup/resilience findings should reference ransomware MITRE techniques."""
        backup_rules = ["RS-002", "RS-003"]
        ransomware_techniques = ["T1486", "T1490", "T1485"]  # Encryption, Inhibit Recovery, Destruction
        
        for rule_id in backup_rules:
            refs = get_framework_refs(rule_id)
            mitre_ids = [r["id"] for r in refs["mitre"]]
            has_ransomware_ref = any(t in mitre_ids for t in ransomware_techniques)
            assert has_ransomware_ref, f"{rule_id} should reference ransomware techniques"
    
    def test_get_framework_refs_returns_valid_structure(self):
        """get_framework_refs should return dict with mitre, cis, owasp arrays."""
        refs = get_framework_refs("TL-001")
        
        assert "mitre" in refs
        assert "cis" in refs
        assert "owasp" in refs
        assert isinstance(refs["mitre"], list)
        assert isinstance(refs["cis"], list)
        assert isinstance(refs["owasp"], list)
        
        # Check MITRE ref structure
        if refs["mitre"]:
            mitre_ref = refs["mitre"][0]
            assert "id" in mitre_ref
            assert "name" in mitre_ref
            assert "tactic" in mitre_ref
            assert "url" in mitre_ref
    
    def test_unknown_rule_returns_empty_arrays(self):
        """Unknown rule_id should return empty arrays (not None or error)."""
        refs = get_framework_refs("UNKNOWN-999")
        
        assert refs["mitre"] == []
        assert refs["cis"] == []
        assert refs["owasp"] == []
    
    def test_get_all_unique_techniques(self):
        """get_all_unique_techniques should aggregate across multiple findings."""
        rule_ids = ["TL-001", "IV-001", "RS-002"]
        result = get_all_unique_techniques(rule_ids)
        
        assert "mitre_techniques_total" in result
        assert "cis_controls_total" in result
        assert "owasp_total" in result
        assert result["mitre_techniques_total"] > 0
        assert result["cis_controls_total"] > 0


class TestFindingsEngine:
    """Tests for findings engine with framework refs."""
    
    def test_finding_includes_framework_refs(self):
        """Generated findings should include framework_refs attribute."""
        # Create test answers that trigger a known finding
        answers = {
            "tl_05": 10,  # Low retention triggers TL-001
            "tl_04": False,  # No SIEM triggers TL-002
            "iv_02": False,  # No admin MFA triggers IV-001
        }
        
        engine = FindingsEngine()
        findings = engine.evaluate(answers, {})
        
        assert len(findings) > 0
        
        for finding in findings:
            assert hasattr(finding, 'framework_refs'), f"Finding {finding.rule_id} missing framework_refs"
            assert finding.framework_refs is not None
            fw_dict = finding.framework_refs.to_dict()
            assert "mitre" in fw_dict
            assert "cis" in fw_dict
            assert "owasp" in fw_dict
    
    def test_iv001_finding_has_mfa_techniques(self):
        """IV-001 (Admin MFA) should have T1078 and T1556 techniques."""
        answers = {
            "iv_02": False,  # No admin MFA triggers IV-001
        }
        
        engine = FindingsEngine()
        findings = engine.evaluate(answers, {})
        
        iv001 = next((f for f in findings if f.rule_id == "IV-001"), None)
        assert iv001 is not None, "IV-001 should be triggered"
        
        mitre_ids = [r["id"] for r in iv001.framework_refs.mitre]
        assert "T1078" in mitre_ids, "Should reference T1078 (Valid Accounts)"


class TestAnalytics:
    """Tests for analytics generation."""
    
    def test_attack_paths_enabled_by_findings(self):
        """Attack paths should be identified based on enabling gaps."""
        # Findings that enable credential compromise path
        finding_ids = ["IV-001", "IV-002", "DC-005"]  # MFA gaps + email security
        
        paths = analyze_attack_paths(finding_ids)
        
        assert len(paths) > 0
        credential_path = next((p for p in paths if "credential" in p["name"].lower()), None)
        assert credential_path is not None, "Should identify credential compromise path"
    
    def test_detection_gaps_analysis(self):
        """Detection gaps should be categorized correctly."""
        finding_ids = ["DC-001", "DC-003", "TL-002"]
        
        gaps = analyze_detection_gaps(finding_ids)
        
        assert "categories" in gaps
        assert gaps["total_gaps"] > 0
        
        category_names = [c["name"] for c in gaps["categories"]]
        assert "Endpoint Detection" in category_names or "Network Detection" in category_names
    
    def test_response_gaps_analysis(self):
        """Response gaps should be categorized correctly."""
        finding_ids = ["IR-001", "RS-002", "RS-003"]
        
        gaps = analyze_response_gaps(finding_ids)
        
        assert "categories" in gaps
        assert gaps["total_gaps"] > 0
    
    def test_identity_gaps_analysis(self):
        """Identity gaps should be categorized correctly."""
        finding_ids = ["IV-001", "IV-003", "IV-005"]
        
        gaps = analyze_identity_gaps(finding_ids)
        
        assert "categories" in gaps
        assert gaps["total_gaps"] >= 3
    
    def test_generate_analytics_complete(self):
        """generate_analytics should return complete analytics package."""
        finding_ids = ["IV-001", "DC-001", "RS-002", "TL-001"]
        
        analytics = generate_analytics(finding_ids)
        
        assert "attack_paths" in analytics
        assert "detection_gaps" in analytics
        assert "response_gaps" in analytics
        assert "identity_gaps" in analytics
        assert "risk_distribution" in analytics
        assert "risk_summary" in analytics
        assert "improvement_recommendations" in analytics


class TestRoadmapGenerator:
    """Tests for roadmap generation."""
    
    def test_phase_assignment_by_severity(self):
        """Critical findings should go to 30-day phase."""
        assert get_phase_for_finding("critical", "low") == "30"
        assert get_phase_for_finding("critical", "high") == "30"
        assert get_phase_for_finding("high", "low") == "30"
        assert get_phase_for_finding("high", "high") == "60"
        assert get_phase_for_finding("medium", "medium") == "60"
        assert get_phase_for_finding("low", "low") == "90"
    
    def test_detailed_roadmap_structure(self):
        """Detailed roadmap should have proper structure."""
        findings = [
            {
                "rule_id": "IV-001",
                "title": "MFA Not Enforced for Admins",
                "severity": "critical",
                "domain_name": "Identity Visibility",
                "recommendation": "Enable MFA for all admin accounts",
                "remediation_effort": "low"
            },
            {
                "rule_id": "TL-002",
                "title": "Missing Centralized Logging",
                "severity": "high",
                "domain_name": "Telemetry & Logging",
                "recommendation": "Deploy SIEM solution",
                "remediation_effort": "high"
            }
        ]
        
        roadmap = generate_detailed_roadmap(findings)
        
        assert "phases" in roadmap
        assert "summary" in roadmap
        assert len(roadmap["phases"]) == 3  # 30, 60, 90
        
        # Check phase structure
        for phase in roadmap["phases"]:
            assert "title" in phase
            assert "items" in phase
        
        # Check summary
        assert roadmap["summary"]["total_items"] == 2
    
    def test_simple_roadmap_structure(self):
        """Simple roadmap should have day30, day60, day90."""
        findings = [
            {"title": "Critical Finding", "severity": "critical", "recommendation": "Fix now"},
            {"title": "High Finding", "severity": "high", "recommendation": "Fix soon"},
            {"title": "Medium Finding", "severity": "medium", "recommendation": "Plan fix"},
        ]
        
        roadmap = generate_simple_roadmap(findings)
        
        assert "day30" in roadmap
        assert "day60" in roadmap
        assert "day90" in roadmap
        assert len(roadmap["day30"]) > 0  # Should have critical finding


class TestIntegration:
    """Integration tests for complete flow."""
    
    def test_full_assessment_flow_with_frameworks(self):
        """Test complete flow from answers to framework-enriched findings."""
        # Answers that trigger multiple findings across domains
        answers = {
            "tl_05": 15,    # Low retention
            "tl_04": False, # No SIEM
            "dc_01": 40,    # Low EDR coverage
            "iv_02": False, # No admin MFA
            "iv_01": False, # No org MFA
            "rs_02": False, # No immutable backups
            "ir_01": False, # No IR playbooks
        }
        
        # Generate findings
        engine = FindingsEngine()
        findings = engine.evaluate(answers, {})
        
        assert len(findings) > 5, "Should generate multiple findings"
        
        # All findings should have framework refs
        for finding in findings:
            assert finding.framework_refs is not None
        
        # Extract rule IDs
        rule_ids = [f.rule_id for f in findings]
        
        # Generate analytics
        analytics = generate_analytics(rule_ids)
        
        # Should identify attack paths
        assert len(analytics["attack_paths"]) > 0
        
        # Should have improvement recommendations
        assert len(analytics["improvement_recommendations"]) > 0
        
        # Generate roadmap
        finding_dicts = [
            {
                "rule_id": f.rule_id,
                "title": f.title,
                "severity": f.severity.value,
                "domain_name": f.domain_name,
                "recommendation": f.recommendation,
                "remediation_effort": f.remediation_effort
            }
            for f in findings
        ]
        
        roadmap = generate_detailed_roadmap(finding_dicts)
        
        # Should have items in multiple phases
        total_items = sum(len(p["items"]) for p in roadmap["phases"])
        assert total_items == len(findings)
