import pytest
from unittest.mock import patch, MagicMock
from app.services.enrichment import EnrichmentService

@pytest.fixture
def service():
    return EnrichmentService()

def test_infer_baseline_saas(service):
    """Test inferring SaaS startup profile."""
    text = "We are a cloud platform for AI driven analytics and software data."
    profile, confidence = service._infer_baseline(text)
    assert profile == "saas_startup"
    assert confidence > 0.0

def test_infer_baseline_healthcare(service):
    """Test inferring Healthcare profile."""
    text = "Our medical clinic provides patient care and health services."
    profile, confidence = service._infer_baseline(text)
    assert profile == "healthcare"
    assert confidence > 0.0

def test_enrich_from_url_success(service):
    """Test successful enrichment flow."""
    html = """
    <html>
        <head>
            <title>Acme Corp - AI Solutions</title>
            <meta name="description" content="Leading provider of artificial intelligence software.">
            <meta name="keywords" content="AI, tech, startup, cloud">
        </head>
        <body></body>
    </html>
    """
    
    with patch('app.services.enrichment.fetch_url', return_value=html):
        result = service.enrich_from_url("https://acme.com")
        
        assert result.title == "Acme Corp - AI Solutions"
        assert result.description == "Leading provider of artificial intelligence software."
        assert "AI" in result.keywords
        assert result.baseline_suggestion == "saas_startup"
        assert result.confidence > 0.5

def test_enrich_from_url_failure(service):
    """Test handling fetch failure."""
    with patch('app.services.enrichment.fetch_url', side_effect=Exception("Fetch failed")):
        result = service.enrich_from_url("https://bad-url.com")
        
        assert result.source_url == "https://bad-url.com"
        assert "Failed" in result.description
