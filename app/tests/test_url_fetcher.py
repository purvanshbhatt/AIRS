import pytest
from unittest.mock import patch, MagicMock
from app.core.url_fetcher import fetch_url, SSRFError, FetchError

def test_fetch_url_valid():
    """Test fetching a valid public URL."""
    with patch('app.core.url_fetcher.requests.Session.get') as mock_get:
        mock_response = MagicMock()
        mock_response.headers = {'Content-Length': '100'}
        mock_response.iter_content.return_value = [b"<html><body>Hello</body></html>"]
        mock_get.return_value.__enter__.return_value = mock_response
        
        content = fetch_url("https://example.com")
        assert "Hello" in content

def test_fetch_url_ssrf_private_ip():
    """Test blocking private IP addresses."""
    # Mock DNS resolution to return a private IP
    with patch('app.core.url_fetcher.socket.getaddrinfo') as mock_dns:
        mock_dns.return_value = [(2, 1, 6, '', ('192.168.1.1', 80))]
        
        with pytest.raises(SSRFError):
            fetch_url("http://internal-site.com")

def test_fetch_url_ssrf_localhost():
    """Test blocking localhost."""
    with patch('app.core.url_fetcher.socket.getaddrinfo') as mock_dns:
        mock_dns.return_value = [(2, 1, 6, '', ('127.0.0.1', 80))]
        
        with pytest.raises(SSRFError):
            fetch_url("http://localhost")

def test_fetch_url_invalid_scheme():
    """Test blocking non-http schemes."""
    with pytest.raises(SSRFError):
        fetch_url("file:///etc/passwd")

def test_fetch_url_too_large():
    """Test blocking large responses."""
    with patch('app.core.url_fetcher.requests.Session.get') as mock_get:
        mock_response = MagicMock()
        # Header check
        mock_response.headers = {'Content-Length': '1048577'} # 1MB + 1
        mock_get.return_value.__enter__.return_value = mock_response
        
        with pytest.raises(FetchError):
            fetch_url("https://example.com/bigfile")
