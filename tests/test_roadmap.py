"""
Tests for the roadmap service.
"""

import pytest
from app.services.roadmap import (
    generate_roadmap,
    calculate_priority,
    create_roadmap_item,
    Priority,
    Effort,
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
    remediation_effort: str = "medium",
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
        remediation_effort=remediation_effort,
    )


class TestPriorityCalculation:
    """Test priority calculation logic."""

    def test_critical_always_immediate(self):
        """Critical findings should always be immediate priority."""
        finding = make_finding(
            rule_id="test_01",
            title="Critical finding",
            severity=Severity.CRITICAL,
            domain_id="test",
            domain_name="Test",
            remediation_effort="high",  # Even with high effort
        )
        
        priority = calculate_priority(finding)
        assert priority == Priority.IMMEDIATE

    def test_high_low_effort_immediate(self):
        """High severity with low effort should be immediate."""
        finding = make_finding(
            rule_id="test_01",
            title="High finding",
            severity=Severity.HIGH,
            domain_id="test",
            domain_name="Test",
            remediation_effort="low",
        )
        
        priority = calculate_priority(finding)
        assert priority == Priority.IMMEDIATE

    def test_high_medium_effort_short_term(self):
        """High severity with medium effort should be short term."""
        finding = make_finding(
            rule_id="test_01",
            title="High finding",
            severity=Severity.HIGH,
            domain_id="test",
            domain_name="Test",
            remediation_effort="medium",
        )
        
        priority = calculate_priority(finding)
        assert priority == Priority.SHORT_TERM

    def test_high_high_effort_medium_term(self):
        """High severity with high effort should be medium term."""
        finding = make_finding(
            rule_id="test_01",
            title="High finding",
            severity=Severity.HIGH,
            domain_id="test",
            domain_name="Test",
            remediation_effort="high",
        )
        
        priority = calculate_priority(finding)
        assert priority == Priority.MEDIUM_TERM

    def test_medium_low_effort_short_term(self):
        """Medium severity with low effort should be short term."""
        finding = make_finding(
            rule_id="test_01",
            title="Medium finding",
            severity=Severity.MEDIUM,
            domain_id="test",
            domain_name="Test",
            remediation_effort="low",
        )
        
        priority = calculate_priority(finding)
        assert priority == Priority.SHORT_TERM

    def test_medium_medium_effort_medium_term(self):
        """Medium severity with medium effort should be medium term."""
        finding = make_finding(
            rule_id="test_01",
            title="Medium finding",
            severity=Severity.MEDIUM,
            domain_id="test",
            domain_name="Test",
            remediation_effort="medium",
        )
        
        priority = calculate_priority(finding)
        assert priority == Priority.MEDIUM_TERM

    def test_low_is_long_term(self):
        """Low severity should always be long term."""
        finding = make_finding(
            rule_id="test_01",
            title="Low finding",
            severity=Severity.LOW,
            domain_id="test",
            domain_name="Test",
            remediation_effort="low",
        )
        
        priority = calculate_priority(finding)
        assert priority == Priority.LONG_TERM


class TestRoadmapItemCreation:
    """Test roadmap item creation."""

    def test_create_roadmap_item_basic(self):
        """Test creating a basic roadmap item."""
        finding = make_finding(
            rule_id="test_01",
            title="Test finding",
            severity=Severity.HIGH,
            domain_id="test",
            domain_name="Test Domain",
            recommendation="Fix this issue",
        )
        
        item = create_roadmap_item(finding)
        
        assert item.finding_id == "test_01"
        assert item.title == "Test finding"
        assert item.severity == "high"
        assert item.domain == "Test Domain"
        assert item.owner_suggestion == "Security Team"  # Default

    def test_create_roadmap_item_with_template(self):
        """Test creating roadmap item with known template."""
        finding = make_finding(
            rule_id="IV-001",  # Should match template
            title="No MFA for admins",
            severity=Severity.CRITICAL,
            domain_id="identity_visibility",
            domain_name="Identity Visibility",
        )
        
        item = create_roadmap_item(finding)
        
        # Should have milestones from template
        assert isinstance(item.milestones, list)


class TestRoadmapGeneration:
    """Test full roadmap generation."""

    def test_generate_roadmap_empty(self):
        """Test with no findings."""
        result = generate_roadmap([])
        
        assert "summary" in result
        assert "phases" in result
        assert result["summary"]["total_items"] == 0

    def test_generate_roadmap_structure(self):
        """Test roadmap structure with findings."""
        findings = [
            make_finding(
                rule_id="test_01",
                title="Critical issue",
                severity=Severity.CRITICAL,
                domain_id="test",
                domain_name="Test",
            ),
            make_finding(
                rule_id="test_02",
                title="High issue",
                severity=Severity.HIGH,
                domain_id="test",
                domain_name="Test",
                remediation_effort="medium",
            ),
            make_finding(
                rule_id="test_03",
                title="Medium issue",
                severity=Severity.MEDIUM,
                domain_id="test",
                domain_name="Test",
            ),
        ]
        
        result = generate_roadmap(findings)
        
        # Check summary
        assert result["summary"]["total_items"] == 3
        
        # Check phases exist
        assert "day30" in result["phases"]
        assert "day60" in result["phases"]
        assert "day90" in result["phases"]
        assert "beyond" in result["phases"]

    def test_generate_roadmap_phase_fields(self):
        """Test phase structure."""
        findings = [
            make_finding(
                rule_id="test_01",
                title="Critical issue",
                severity=Severity.CRITICAL,
                domain_id="test",
                domain_name="Test",
            ),
        ]
        
        result = generate_roadmap(findings)
        
        day30 = result["phases"]["day30"]
        assert "name" in day30
        assert "description" in day30
        assert "item_count" in day30
        assert "effort_hours" in day30
        assert "risk_reduction" in day30
        assert "items" in day30

    def test_critical_in_day30(self):
        """Test that critical findings go to day 30."""
        findings = [
            make_finding(
                rule_id="test_01",
                title="Critical issue",
                severity=Severity.CRITICAL,
                domain_id="test",
                domain_name="Test",
            ),
        ]
        
        result = generate_roadmap(findings)
        
        day30_items = result["phases"]["day30"]["items"]
        assert len(day30_items) == 1
        assert day30_items[0]["severity"] == "critical"

    def test_roadmap_item_fields(self):
        """Test roadmap item structure."""
        findings = [
            make_finding(
                rule_id="test_01",
                title="Test issue",
                severity=Severity.HIGH,
                domain_id="test",
                domain_name="Test Domain",
                recommendation="Fix it",
            ),
        ]
        
        result = generate_roadmap(findings)
        
        # Find the item
        all_items = []
        for phase in result["phases"].values():
            all_items.extend(phase["items"])
        
        assert len(all_items) == 1
        item = all_items[0]
        
        assert "finding_id" in item
        assert "title" in item
        assert "action" in item
        assert "effort" in item
        assert "severity" in item
        assert "domain" in item
        assert "owner" in item
        assert "milestones" in item
        assert "success_criteria" in item

    def test_summary_counts(self):
        """Test summary statistics."""
        findings = [
            make_finding(
                rule_id="test_01",
                title="Critical issue",
                severity=Severity.CRITICAL,
                domain_id="test",
                domain_name="Test",
            ),
            make_finding(
                rule_id="test_02",
                title="Quick win",
                severity=Severity.HIGH,
                domain_id="test",
                domain_name="Test",
                remediation_effort="low",
            ),
            make_finding(
                rule_id="test_03",
                title="Another quick win",
                severity=Severity.MEDIUM,
                domain_id="test",
                domain_name="Test",
                remediation_effort="low",
            ),
        ]
        
        result = generate_roadmap(findings)
        
        summary = result["summary"]
        assert summary["total_items"] == 3
        assert summary["critical_items"] >= 1
        assert summary["quick_wins"] >= 2
        assert summary["total_effort_hours"] > 0
        assert summary["total_risk_reduction"] > 0

    def test_sorting_within_priority(self):
        """Test that items are sorted by severity within each priority level."""
        findings = [
            make_finding(
                rule_id="test_01",
                title="Medium effort critical",
                severity=Severity.CRITICAL,
                domain_id="test",
                domain_name="Test",
                remediation_effort="medium",
            ),
            make_finding(
                rule_id="test_02",
                title="Low effort critical",
                severity=Severity.CRITICAL,
                domain_id="test",
                domain_name="Test",
                remediation_effort="low",
            ),
        ]
        
        result = generate_roadmap(findings)
        
        day30_items = result["phases"]["day30"]["items"]
        # Both should be in day30 (critical)
        assert len(day30_items) == 2
        
        # Low effort should come first
        efforts = [i["effort"] for i in day30_items]
        assert efforts == ["low", "medium"]
