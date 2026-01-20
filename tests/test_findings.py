"""Tests for the AIRS Findings Rules Engine."""

import pytest
from app.services.findings import (
    FindingsEngine,
    generate_findings,
    get_findings_summary,
    Finding,
    Severity,
    get_bool,
    get_numeric,
    get_domain_score,
    FINDING_RULES,
)
from app.services.scoring import calculate_scores


class TestHelperFunctions:
    """Test helper functions for answer parsing."""
    
    def test_get_bool_true_values(self):
        answers = {
            "q1": True,
            "q2": "true",
            "q3": "yes",
            "q4": "1",
            "q5": 1,
        }
        assert get_bool(answers, "q1") is True
        assert get_bool(answers, "q2") is True
        assert get_bool(answers, "q3") is True
        assert get_bool(answers, "q4") is True
        assert get_bool(answers, "q5") is True
    
    def test_get_bool_false_values(self):
        answers = {
            "q1": False,
            "q2": "false",
            "q3": "no",
            "q4": "0",
            "q5": 0,
        }
        assert get_bool(answers, "q1") is False
        assert get_bool(answers, "q2") is False
        assert get_bool(answers, "q3") is False
        assert get_bool(answers, "q4") is False
        assert get_bool(answers, "q5") is False
    
    def test_get_bool_missing_key(self):
        answers = {}
        assert get_bool(answers, "missing") is False
    
    def test_get_numeric_valid_values(self):
        answers = {
            "q1": 42,
            "q2": "85.5",
            "q3": 0,
        }
        assert get_numeric(answers, "q1") == 42
        assert get_numeric(answers, "q2") == 85.5
        assert get_numeric(answers, "q3") == 0
    
    def test_get_numeric_invalid_values(self):
        answers = {
            "q1": "invalid",
            "q2": None,
        }
        assert get_numeric(answers, "q1", default=0) == 0
        assert get_numeric(answers, "q2", default=50) == 50
        assert get_numeric(answers, "missing", default=100) == 100
    
    def test_get_domain_score(self):
        scores = {
            "domains": [
                {"domain_id": "telemetry_logging", "score": 3.5},
                {"domain_id": "detection_coverage", "score": 4.0},
            ]
        }
        assert get_domain_score(scores, "telemetry_logging") == 3.5
        assert get_domain_score(scores, "detection_coverage") == 4.0
        assert get_domain_score(scores, "nonexistent") == 0.0


class TestTelemetryLoggingRules:
    """Test Telemetry & Logging domain rules."""
    
    def test_insufficient_retention_triggers_finding(self):
        """TL-001: Log retention < 30 days should trigger."""
        answers = {"tl_05": 14}  # 14 days retention
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "TL-001" in rule_ids
        
        finding = next(f for f in findings if f.rule_id == "TL-001")
        assert finding.severity == Severity.HIGH
        assert "14" in finding.evidence
        assert "retention" in finding.title.lower()
    
    def test_sufficient_retention_no_finding(self):
        """TL-001: Log retention >= 30 days should not trigger."""
        answers = {"tl_05": 90}  # 90 days retention
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "TL-001" not in rule_ids
    
    def test_missing_siem_triggers_finding(self):
        """TL-002: No centralized SIEM should trigger."""
        answers = {"tl_04": False}
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "TL-002" in rule_ids
        
        finding = next(f for f in findings if f.rule_id == "TL-002")
        assert finding.severity == Severity.HIGH
    
    def test_no_auth_logging_triggers_finding(self):
        """TL-005: No auth event logging should trigger."""
        answers = {"tl_06": False}
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "TL-005" in rule_ids


class TestDetectionCoverageRules:
    """Test Detection Coverage domain rules."""
    
    def test_low_edr_coverage_triggers_high(self):
        """DC-001: EDR < 80% should trigger high severity."""
        answers = {"dc_01": 65}  # 65% coverage
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "DC-001" in rule_ids
        
        finding = next(f for f in findings if f.rule_id == "DC-001")
        assert finding.severity == Severity.HIGH
        assert "65" in finding.evidence
    
    def test_critical_edr_coverage_triggers_critical(self):
        """DC-002: EDR < 50% should trigger critical severity."""
        answers = {"dc_01": 30}  # 30% coverage
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "DC-002" in rule_ids
        
        finding = next(f for f in findings if f.rule_id == "DC-002")
        assert finding.severity == Severity.CRITICAL
    
    def test_good_edr_coverage_no_finding(self):
        """DC-001/DC-002: EDR >= 80% should not trigger."""
        answers = {"dc_01": 95}  # 95% coverage
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "DC-001" not in rule_ids
        assert "DC-002" not in rule_ids
    
    def test_no_email_security_triggers_finding(self):
        """DC-005: No email security should trigger high."""
        answers = {"dc_05": False}
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "DC-005" in rule_ids
        
        finding = next(f for f in findings if f.rule_id == "DC-005")
        assert finding.severity == Severity.HIGH


class TestIdentityVisibilityRules:
    """Test Identity Visibility domain rules."""
    
    def test_no_admin_mfa_triggers_critical(self):
        """IV-001: No admin MFA should trigger critical severity."""
        answers = {"iv_02": False}
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "IV-001" in rule_ids
        
        finding = next(f for f in findings if f.rule_id == "IV-001")
        assert finding.severity == Severity.CRITICAL
        assert "IMMEDIATE" in finding.recommendation
    
    def test_admin_mfa_enabled_no_finding(self):
        """IV-001: Admin MFA enabled should not trigger."""
        answers = {"iv_02": True}
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "IV-001" not in rule_ids
    
    def test_no_org_mfa_triggers_high(self):
        """IV-002: No org-wide MFA should trigger high severity."""
        answers = {"iv_01": False}
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "IV-002" in rule_ids
        
        finding = next(f for f in findings if f.rule_id == "IV-002")
        assert finding.severity == Severity.HIGH
    
    def test_no_priv_account_inventory_triggers_finding(self):
        """IV-003: No privileged account inventory should trigger."""
        answers = {"iv_03": False}
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "IV-003" in rule_ids


class TestIRProcessRules:
    """Test Incident Response Process domain rules."""
    
    def test_no_playbooks_triggers_finding(self):
        """IR-001: No IR playbooks should trigger high severity."""
        answers = {"ir_01": False}
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "IR-001" in rule_ids
        
        finding = next(f for f in findings if f.rule_id == "IR-001")
        assert finding.severity == Severity.HIGH
    
    def test_untested_playbooks_triggers_finding(self):
        """IR-002: Playbooks exist but not tested should trigger."""
        answers = {"ir_01": True, "ir_02": False}
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "IR-002" in rule_ids
        
        finding = next(f for f in findings if f.rule_id == "IR-002")
        assert "tested" in finding.title.lower()
    
    def test_tested_playbooks_no_finding(self):
        """IR-002: Tested playbooks should not trigger."""
        answers = {"ir_01": True, "ir_02": True}
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "IR-002" not in rule_ids
    
    def test_no_tabletop_triggers_finding(self):
        """IR-003: No tabletop exercises should trigger."""
        answers = {"ir_06": False}
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "IR-003" in rule_ids


class TestResilienceRules:
    """Test Resilience domain rules."""
    
    def test_untested_backups_triggers_finding(self):
        """RS-001: Untested backups should trigger high severity."""
        answers = {"rs_03": False}
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "RS-001" in rule_ids
        
        finding = next(f for f in findings if f.rule_id == "RS-001")
        assert finding.severity == Severity.HIGH
        assert "Backup" in finding.title
    
    def test_no_immutable_backups_triggers_critical(self):
        """RS-002: Backups exist but not immutable should trigger critical."""
        answers = {"rs_01": True, "rs_02": False}
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "RS-002" in rule_ids
        
        finding = next(f for f in findings if f.rule_id == "RS-002")
        assert finding.severity == Severity.CRITICAL
        assert "ransomware" in finding.evidence.lower()
    
    def test_no_backups_triggers_critical(self):
        """RS-003: No critical system backups should trigger critical."""
        answers = {"rs_01": False}
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "RS-003" in rule_ids
        
        finding = next(f for f in findings if f.rule_id == "RS-003")
        assert finding.severity == Severity.CRITICAL
    
    def test_high_rto_triggers_finding(self):
        """RS-004: RTO > 72 hours should trigger medium severity."""
        answers = {"rs_05": 120}  # 120 hours RTO
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "RS-004" in rule_ids
        
        finding = next(f for f in findings if f.rule_id == "RS-004")
        assert finding.severity == Severity.MEDIUM
        assert "120" in finding.evidence
    
    def test_acceptable_rto_no_finding(self):
        """RS-004: RTO <= 72 hours should not trigger."""
        answers = {"rs_05": 24}  # 24 hours RTO
        findings = generate_findings(answers)
        
        rule_ids = [f.rule_id for f in findings]
        assert "RS-004" not in rule_ids


class TestAggregateRules:
    """Test aggregate domain-level rules."""
    
    def test_low_telemetry_score_triggers_finding(self):
        """AGG-001: Telemetry score < 2.0 should trigger."""
        answers = {
            "tl_01": False,
            "tl_02": False,
            "tl_03": False,
            "tl_04": False,
            "tl_05": 7,
            "tl_06": False,
        }
        scores = calculate_scores(answers)
        findings = generate_findings(answers, scores)
        
        rule_ids = [f.rule_id for f in findings]
        assert "AGG-001" in rule_ids
    
    def test_low_identity_score_triggers_critical(self):
        """AGG-002: Identity score < 2.0 should trigger critical."""
        answers = {
            "iv_01": False,
            "iv_02": False,
            "iv_03": False,
            "iv_04": False,
            "iv_05": False,
            "iv_06": False,
        }
        scores = calculate_scores(answers)
        findings = generate_findings(answers, scores)
        
        rule_ids = [f.rule_id for f in findings]
        assert "AGG-002" in rule_ids
        
        finding = next(f for f in findings if f.rule_id == "AGG-002")
        assert finding.severity == Severity.CRITICAL


class TestFindingsSorting:
    """Test findings are sorted by severity."""
    
    def test_findings_sorted_by_severity(self):
        """Findings should be sorted: critical > high > medium > low."""
        # Create answers that trigger multiple severities
        answers = {
            "iv_02": False,  # Critical - no admin MFA
            "dc_01": 65,     # High - low EDR
            "ir_06": False,  # Medium - no tabletop
        }
        findings = generate_findings(answers)
        
        severities = [f.severity for f in findings]
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4
        }
        
        # Check that severities are in order
        for i in range(len(severities) - 1):
            assert severity_order[severities[i]] <= severity_order[severities[i + 1]]


class TestFindingsSummary:
    """Test findings summary generation."""
    
    def test_summary_counts(self):
        """Summary should count findings by severity and domain."""
        answers = {
            "iv_02": False,  # Critical
            "rs_01": False,  # Critical
            "dc_01": 65,     # High
            "tl_05": 14,     # High
        }
        findings = generate_findings(answers)
        summary = get_findings_summary(findings)
        
        assert summary["total"] > 0
        assert summary["by_severity"]["critical"] >= 2
        assert summary["by_severity"]["high"] >= 1
    
    def test_summary_top_priorities(self):
        """Summary should identify top priorities (critical/high + low/medium effort)."""
        answers = {
            "iv_02": False,  # Critical, low effort
            "dc_01": 65,     # High, medium effort
        }
        findings = generate_findings(answers)
        summary = get_findings_summary(findings)
        
        assert len(summary["top_priorities"]) > 0
        # Top priorities should have critical or high severity
        for priority in summary["top_priorities"]:
            assert priority["severity"] in ("critical", "high")


class TestFindingsEngine:
    """Test FindingsEngine class."""
    
    def test_engine_initialization(self):
        """Engine should initialize with default rules."""
        engine = FindingsEngine()
        assert len(engine.rules) >= 15
    
    def test_engine_custom_rules(self):
        """Engine should accept custom rules."""
        from app.services.findings import FindingRule
        
        custom_rules = [
            FindingRule(
                rule_id="CUSTOM-001",
                title="Custom Rule",
                domain_id="telemetry_logging",
                severity=Severity.LOW,
                condition=lambda a, s: True,  # Always triggers
                evidence_fn=lambda a, s: "Custom evidence",
                recommendation="Custom recommendation"
            )
        ]
        engine = FindingsEngine(rules=custom_rules)
        findings = engine.evaluate({})
        
        assert len(findings) == 1
        assert findings[0].rule_id == "CUSTOM-001"
    
    def test_engine_handles_errors_gracefully(self):
        """Engine should handle rule evaluation errors gracefully."""
        from app.services.findings import FindingRule
        
        def bad_condition(a, s):
            raise ValueError("Test error")
        
        custom_rules = [
            FindingRule(
                rule_id="BAD-001",
                title="Bad Rule",
                domain_id="telemetry_logging",
                severity=Severity.LOW,
                condition=bad_condition,
                evidence_fn=lambda a, s: "Evidence",
                recommendation="Recommendation"
            )
        ]
        engine = FindingsEngine(rules=custom_rules)
        
        # Should not raise, just skip the bad rule
        findings = engine.evaluate({})
        assert len(findings) == 0


class TestFullAssessmentScenarios:
    """Test complete assessment scenarios."""
    
    def test_worst_case_scenario(self):
        """All security controls missing should trigger many findings."""
        answers = {
            # Telemetry - all bad
            "tl_01": False, "tl_02": False, "tl_03": False,
            "tl_04": False, "tl_05": 7, "tl_06": False,
            # Detection - all bad
            "dc_01": 20, "dc_02": False, "dc_03": False,
            "dc_04": False, "dc_05": False, "dc_06": False,
            # Identity - all bad
            "iv_01": False, "iv_02": False, "iv_03": False,
            "iv_04": False, "iv_05": False, "iv_06": False,
            # IR - all bad
            "ir_01": False, "ir_02": False, "ir_03": False,
            "ir_04": False, "ir_05": False, "ir_06": False,
            # Resilience - all bad
            "rs_01": False, "rs_02": False, "rs_03": False,
            "rs_04": False, "rs_05": 168, "rs_06": False,
        }
        scores = calculate_scores(answers)
        findings = generate_findings(answers, scores)
        summary = get_findings_summary(findings)
        
        # Should have many findings
        assert len(findings) >= 15
        
        # Should have critical findings
        assert summary["by_severity"]["critical"] >= 3
        
        # Should have findings across all domains
        assert len(summary["by_domain"]) >= 4
    
    def test_best_case_scenario(self):
        """All security controls present should trigger few/no findings."""
        answers = {
            # Telemetry - all good
            "tl_01": True, "tl_02": True, "tl_03": True,
            "tl_04": True, "tl_05": 365, "tl_06": True,
            # Detection - all good
            "dc_01": 98, "dc_02": True, "dc_03": True,
            "dc_04": True, "dc_05": True, "dc_06": True,
            # Identity - all good
            "iv_01": True, "iv_02": True, "iv_03": True,
            "iv_04": True, "iv_05": True, "iv_06": True,
            # IR - all good
            "ir_01": True, "ir_02": True, "ir_03": True,
            "ir_04": True, "ir_05": True, "ir_06": True,
            # Resilience - all good
            "rs_01": True, "rs_02": True, "rs_03": True,
            "rs_04": True, "rs_05": 4, "rs_06": True,
        }
        scores = calculate_scores(answers)
        findings = generate_findings(answers, scores)
        summary = get_findings_summary(findings)
        
        # Should have very few findings
        assert len(findings) <= 2
        
        # Should have no critical findings
        assert summary["by_severity"]["critical"] == 0


class TestRuleCount:
    """Verify minimum rule count requirement."""
    
    def test_at_least_15_rules(self):
        """Should have at least 15 defined rules."""
        assert len(FINDING_RULES) >= 15
    
    def test_rules_cover_all_domains(self):
        """Rules should cover all 5 domains."""
        domains = set(rule.domain_id for rule in FINDING_RULES)
        expected_domains = {
            "telemetry_logging",
            "detection_coverage", 
            "identity_visibility",
            "ir_process",
            "resilience"
        }
        assert expected_domains.issubset(domains)
    
    def test_rules_have_all_severities(self):
        """Rules should include critical, high, and medium severities."""
        severities = set(rule.severity for rule in FINDING_RULES)
        assert Severity.CRITICAL in severities
        assert Severity.HIGH in severities
        assert Severity.MEDIUM in severities
    
    def test_all_rules_have_references(self):
        """Most rules should have framework references."""
        rules_with_refs = sum(1 for r in FINDING_RULES if r.reference)
        # At least 80% should have references
        assert rules_with_refs / len(FINDING_RULES) >= 0.8
