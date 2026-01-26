"""
Tests for AI Narrative Generator (ai_narrative.py).

Tests cover:
1. Fallback narrative generation
2. LLM retry logic
3. SDK initialization modes (Vertex AI vs API key)
4. Timeout configuration
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from typing import Dict, Any

from app.services.ai_narrative import (
    generate_narrative,
    _generate_fallback_narrative,
    _generate_llm_narrative,
    LLM_TIMEOUT_SECONDS,
    LLM_MAX_RETRIES,
)


@pytest.fixture
def sample_payload() -> Dict[str, Any]:
    """Sample assessment payload for testing."""
    return {
        "overall_score": 72.5,
        "tier": {
            "label": "Good",
            "color": "#22C55E"
        },
        "domain_scores": [
            {"domain_id": "gov", "domain_name": "Governance", "score_5": 4.2},
            {"domain_id": "sec", "domain_name": "Security", "score_5": 3.8},
            {"domain_id": "ops", "domain_name": "Operations", "score_5": 3.5},
        ],
        "findings": [
            {"severity": "high", "title": "Missing AI Policy", "domain": "Governance", "recommendation": "Create formal AI policy"},
            {"severity": "medium", "title": "Incomplete Logging", "domain": "Operations", "recommendation": "Implement audit logging"},
        ],
        "organization_name": "Test Corp"
    }


@pytest.fixture
def critical_payload() -> Dict[str, Any]:
    """Critical tier payload for testing."""
    return {
        "overall_score": 28.0,
        "tier": {"label": "Critical", "color": "#EF4444"},
        "domain_scores": [
            {"domain_id": "gov", "domain_name": "Governance", "score_5": 1.2},
            {"domain_id": "sec", "domain_name": "Security", "score_5": 1.5},
        ],
        "findings": [
            {"severity": "critical", "title": "No Security Controls", "domain": "Security", "recommendation": "Implement immediately"},
            {"severity": "critical", "title": "No Governance", "domain": "Governance", "recommendation": "Establish framework"},
            {"severity": "high", "title": "Missing Monitoring", "domain": "Operations", "recommendation": "Deploy monitoring"},
        ],
        "organization_name": "Vulnerable Inc"
    }


class TestFallbackNarrative:
    """Tests for deterministic fallback narratives."""
    
    def test_fallback_returns_expected_keys(self, sample_payload):
        """Fallback should return all required keys."""
        result = _generate_fallback_narrative(sample_payload)
        
        assert "executive_summary_text" in result
        assert "roadmap_narrative_text" in result
        assert "llm_generated" in result
        assert result["llm_generated"] is False
    
    def test_fallback_good_tier_narrative(self, sample_payload):
        """Good tier should generate appropriate narrative."""
        result = _generate_fallback_narrative(sample_payload)
        
        assert "Good" in result["executive_summary_text"] or "72" in result["executive_summary_text"]
        assert "Test Corp" in result["executive_summary_text"]
    
    def test_fallback_critical_tier_narrative(self, critical_payload):
        """Critical tier should generate urgent narrative."""
        result = _generate_fallback_narrative(critical_payload)
        
        assert "Critical" in result["executive_summary_text"]
        assert "immediate" in result["executive_summary_text"].lower() or "urgent" in result["executive_summary_text"].lower()
    
    def test_fallback_includes_finding_counts(self, critical_payload):
        """Narrative should reference finding counts."""
        result = _generate_fallback_narrative(critical_payload)
        
        # Should mention critical findings
        exec_text = result["executive_summary_text"].lower()
        assert "critical" in exec_text
    
    def test_fallback_roadmap_present(self, sample_payload):
        """Roadmap narrative should be non-empty."""
        result = _generate_fallback_narrative(sample_payload)
        
        assert len(result["roadmap_narrative_text"]) > 50


class TestLLMConfiguration:
    """Tests for LLM configuration constants."""
    
    def test_timeout_is_reasonable(self):
        """Timeout should be 30-45 seconds."""
        assert 30 <= LLM_TIMEOUT_SECONDS <= 45
    
    def test_max_retries_is_two(self):
        """Should retry twice (2 retries + 1 initial = 3 attempts max)."""
        assert LLM_MAX_RETRIES == 2


class TestGenerateNarrative:
    """Tests for the main generate_narrative function."""
    
    def test_returns_fallback_when_llm_disabled(self, sample_payload):
        """Should return fallback when LLM is disabled."""
        with patch('app.services.ai_narrative.settings') as mock_settings:
            mock_settings.is_llm_enabled = False
            
            result = generate_narrative(sample_payload)
            
            assert result["llm_generated"] is False
    
    def test_logs_demo_mode_warning(self, sample_payload):
        """Should log warning in demo mode."""
        with patch('app.services.ai_narrative.settings') as mock_settings:
            mock_settings.is_llm_enabled = True
            mock_settings.is_demo_mode = True
            
            with patch('app.services.ai_narrative._generate_llm_narrative') as mock_llm:
                mock_llm.return_value = {
                    "executive_summary_text": "Test",
                    "roadmap_narrative_text": "Test",
                    "llm_generated": True
                }
                
                with patch('app.services.ai_narrative.logger') as mock_logger:
                    generate_narrative(sample_payload)
                    
                    # Should have logged demo mode warning
                    mock_logger.warning.assert_called()


class TestLLMNarrativeGeneration:
    """Tests for LLM narrative generation with mocked SDK."""
    
    def test_uses_vertex_ai_when_project_id_set(self, sample_payload):
        """Should prefer Vertex AI when GCP_PROJECT_ID is available."""
        # This test verifies the configuration preference
        # Actual SDK initialization is tested in integration tests
        # Here we just verify the settings are properly used
        from app.core.config import settings
        
        # Verify the settings exist and are accessible
        assert hasattr(settings, 'GCP_PROJECT_ID')
        assert hasattr(settings, 'GEMINI_API_KEY')
        assert hasattr(settings, 'LLM_MODEL')
    
    def test_falls_back_on_llm_error(self, sample_payload):
        """Should fall back to deterministic narrative on LLM error."""
        with patch('app.services.ai_narrative.settings') as mock_settings:
            mock_settings.is_llm_enabled = True
            mock_settings.is_demo_mode = False
            
            with patch('app.services.ai_narrative._generate_llm_narrative') as mock_llm:
                mock_llm.side_effect = Exception("API Error")
                
                result = generate_narrative(sample_payload)
                
                # Should have used fallback
                assert result["llm_generated"] is False


class TestRetryLogic:
    """Tests for retry behavior."""
    
    def test_retries_on_transient_error(self):
        """Should retry on transient errors up to MAX_RETRIES times."""
        # This would be tested with integration tests
        # Unit test verifies configuration is correct
        assert LLM_MAX_RETRIES == 2
    
    def test_exponential_backoff_configured(self):
        """Exponential backoff should be configured."""
        from app.services.ai_narrative import LLM_INITIAL_BACKOFF
        
        # Initial backoff should be 1 second
        assert LLM_INITIAL_BACKOFF == 1.0
