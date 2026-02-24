"""
Tests for LLM Narrative Generator.

Tests cover:
1. Feature flag behavior (disabled by default)
2. Deterministic fallback narratives
3. Score immutability (LLM cannot modify scores)
4. Executive summary generation
5. Roadmap generation
6. Finding rewrites
"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.llm_narrative import (
    LLMNarrativeGenerator,
    ScoreContext,
    FindingContext,
    NarrativeType,
    get_narrative_generator,
)
from app.core.config import settings


class TestFeatureFlag:
    """Tests for AIRS_USE_LLM feature flag."""
    
    def test_llm_disabled_by_default(self):
        """LLM should be disabled by default."""
        # Default setting should be False
        assert settings.AIRS_USE_LLM is False
    
    def test_generator_not_available_when_disabled(self):
        """Generator should not be available when disabled."""
        with patch.object(settings, 'AIRS_USE_LLM', False):
            generator = LLMNarrativeGenerator()
            assert generator.is_available() is False
    
    def test_generator_needs_api_key(self):
        """Generator should require API key even when enabled."""
        with patch.object(settings, 'AIRS_USE_LLM', True):
            with patch.object(settings, 'GEMINI_API_KEY', None):
                generator = LLMNarrativeGenerator()
                assert generator.is_available() is False


class TestScoreImmutability:
    """Tests ensuring LLM cannot modify scores."""
    
    def test_score_context_is_readonly(self):
        """ScoreContext should preserve original values."""
        context = ScoreContext(
            overall_score=75.5,
            maturity_level=3,
            maturity_name="Defined",
            domain_scores=[
                {"domain_id": "gov", "domain_name": "Governance", "score": 80.0}
            ]
        )
        
        # Verify values are preserved
        assert context.overall_score == 75.5
        assert context.maturity_level == 3
        assert context.maturity_name == "Defined"
    
    def test_prompt_context_contains_exact_scores(self):
        """Prompt context should contain exact score values."""
        context = ScoreContext(
            overall_score=72.3,
            maturity_level=2,
            maturity_name="Managed",
            domain_scores=[
                {"domain_id": "gov", "domain_name": "Governance", "score": 85.5}
            ]
        )
        
        prompt = context.to_prompt_context()
        
        # Verify exact values appear in prompt
        assert "72.3" in prompt
        assert "Managed" in prompt
        assert "Governance" in prompt
        assert "85.5" in prompt


class TestDeterministicFallback:
    """Tests for deterministic fallback when LLM is disabled."""
    
    @pytest.fixture
    def sample_scores(self):
        return ScoreContext(
            overall_score=65.0,
            maturity_level=2,
            maturity_name="Managed",
            domain_scores=[
                {"domain_id": "gov", "domain_name": "Governance", "score": 70.0, "weight": 25},
                {"domain_id": "sec", "domain_name": "Security", "score": 60.0, "weight": 20},
            ]
        )
    
    @pytest.fixture
    def sample_findings(self):
        return [
            FindingContext(
                rule_id="GOV-001",
                title="Missing AI Policy",
                domain_name="Governance",
                severity="high",
                evidence="No formal AI policy documented",
                recommendation="Establish formal AI governance policy"
            ),
            FindingContext(
                rule_id="SEC-001",
                title="Weak Access Controls",
                domain_name="Security",
                severity="critical",
                evidence="No MFA enabled",
                recommendation="Implement MFA for all users"
            )
        ]
    
    def test_fallback_executive_summary(self, sample_scores, sample_findings):
        """Fallback should produce valid executive summary."""
        generator = LLMNarrativeGenerator()
        generator.enabled = False  # Force fallback
        
        result = generator.generate_executive_summary(
            sample_scores, sample_findings, "Test Corp"
        )
        
        assert result.llm_generated is False
        assert result.narrative_type == NarrativeType.EXECUTIVE_SUMMARY
        assert "65.0" in result.content  # Exact score preserved
        assert "Test Corp" in result.content
        assert len(result.content) > 100  # Meaningful content
    
    def test_fallback_roadmap(self, sample_scores, sample_findings):
        """Fallback should produce valid roadmap."""
        generator = LLMNarrativeGenerator()
        generator.enabled = False
        
        result = generator.generate_roadmap_narrative(
            sample_scores, sample_findings, "Test Corp"
        )
        
        assert result.llm_generated is False
        assert result.narrative_type == NarrativeType.ROADMAP_30_60_90
        assert "30 Days" in result.content
        assert "60" in result.content
        assert "90" in result.content
    
    def test_fallback_finding_rewrite(self, sample_findings):
        """Fallback should produce valid finding rewrite."""
        generator = LLMNarrativeGenerator()
        generator.enabled = False
        
        result = generator.rewrite_finding_business_tone(sample_findings[1])
        
        assert result.llm_generated is False
        assert "Weak Access Controls" in result.content
        assert "critical" in result.content.lower() or "severe" in result.content.lower()


class TestExecutiveSummaryGeneration:
    """Tests for executive summary generation."""
    
    @pytest.fixture
    def generator(self):
        gen = LLMNarrativeGenerator()
        gen.enabled = False  # Use fallback for deterministic tests
        return gen
    
    def test_high_score_positive_tone(self, generator):
        """High scores should result in positive summary."""
        scores = ScoreContext(
            overall_score=85.0,
            maturity_level=4,
            maturity_name="Quantitatively Managed",
            domain_scores=[]
        )
        
        result = generator.generate_executive_summary(scores, [], "Test Corp")
        
        assert "strong" in result.content.lower()
        assert "85.0" in result.content
    
    def test_low_score_urgent_tone(self, generator):
        """Low scores should result in urgent summary."""
        scores = ScoreContext(
            overall_score=25.0,
            maturity_level=1,
            maturity_name="Initial",
            domain_scores=[]
        )
        
        result = generator.generate_executive_summary(scores, [], "Test Corp")
        
        # Should indicate urgency
        assert any(word in result.content.lower() for word in ["critical", "immediate", "substantial", "gaps"])


class TestRoadmapGeneration:
    """Tests for 30/60/90 day roadmap generation."""
    
    def test_roadmap_phases_present(self):
        """Roadmap should contain all three phases."""
        generator = LLMNarrativeGenerator()
        generator.enabled = False
        
        scores = ScoreContext(
            overall_score=50.0,
            maturity_level=2,
            maturity_name="Managed",
            domain_scores=[]
        )
        
        findings = [
            FindingContext(
                rule_id="TEST-001",
                title="Critical Issue",
                domain_name="Test",
                severity="critical",
                evidence="Test evidence",
                recommendation="Fix immediately"
            )
        ]
        
        result = generator.generate_roadmap_narrative(scores, findings)
        
        assert "30 Days" in result.content
        assert "60" in result.content
        assert "90" in result.content
    
    def test_critical_findings_in_first_phase(self):
        """Critical findings should appear in 30-day phase."""
        generator = LLMNarrativeGenerator()
        generator.enabled = False
        
        findings = [
            FindingContext(
                rule_id="CRIT-001",
                title="Critical Security Gap",
                domain_name="Security",
                severity="critical",
                evidence="Exposed credentials",
                recommendation="Rotate all credentials immediately"
            )
        ]
        
        scores = ScoreContext(
            overall_score=40.0,
            maturity_level=1,
            maturity_name="Initial",
            domain_scores=[]
        )
        
        result = generator.generate_roadmap_narrative(scores, findings)
        
        # Critical finding should be in the content
        assert "Critical Security Gap" in result.content


class TestFindingRewrites:
    """Tests for business-tone finding rewrites."""
    
    def test_severity_preserved(self):
        """Original severity should be preserved in rewrite."""
        generator = LLMNarrativeGenerator()
        generator.enabled = False
        
        finding = FindingContext(
            rule_id="TEST-001",
            title="Technical Vulnerability",
            domain_name="Security",
            severity="high",
            evidence="CVE-2024-1234 detected",
            recommendation="Apply security patch"
        )
        
        result = generator.rewrite_finding_business_tone(finding)
        
        # Severity context should be present
        assert "significant" in result.content.lower() or "high" in result.content.lower()
    
    def test_recommendation_included(self):
        """Recommendation should be included in rewrite."""
        generator = LLMNarrativeGenerator()
        generator.enabled = False
        
        finding = FindingContext(
            rule_id="TEST-001",
            title="Missing Documentation",
            domain_name="Governance",
            severity="medium",
            evidence="No policy documents found",
            recommendation="Create and publish AI governance documentation"
        )
        
        result = generator.rewrite_finding_business_tone(finding)
        
        assert "Recommendation" in result.content or "recommendation" in result.content


class TestNarrativeAPI:
    """Integration tests for narrative API endpoints."""
    
    def test_llm_status_disabled(self, client):
        """Status endpoint should show LLM disabled."""
        response = client.get("/api/narratives/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False
        assert "AIRS_USE_LLM" in data["message"]
    
    def test_narratives_require_scored_assessment(self, client):
        """Narrative generation should require scored assessment."""
        # Try to get narratives for non-existent assessment
        response = client.post("/api/narratives/fake-id/narratives")
        
        assert response.status_code == 404
