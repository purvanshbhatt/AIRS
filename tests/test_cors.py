"""
Tests for CORS configuration helper.
"""

import os
import pytest
from unittest.mock import patch

from app.core.cors import validate_origin, get_allowed_origins, is_localhost_origin, DEV_LOCALHOST_ORIGINS


class TestIsLocalhostOrigin:
    """Tests for is_localhost_origin function."""
    
    def test_localhost(self):
        assert is_localhost_origin("http://localhost:5173") is True
    
    def test_127_0_0_1(self):
        assert is_localhost_origin("http://127.0.0.1:3000") is True
    
    def test_ipv6_loopback(self):
        assert is_localhost_origin("http://[::1]:8080") is True
    
    def test_not_localhost(self):
        assert is_localhost_origin("https://example.com") is False
    
    def test_empty(self):
        assert is_localhost_origin("") is False


class TestValidateOrigin:
    """Tests for validate_origin function."""
    
    def test_valid_https_origin(self):
        is_valid, error = validate_origin("https://example.com")
        assert is_valid is True
        assert error == ""
    
    def test_valid_http_localhost(self):
        is_valid, error = validate_origin("http://localhost:5173")
        assert is_valid is True
        assert error == ""
    
    def test_valid_https_with_port(self):
        is_valid, error = validate_origin("https://example.com:8080")
        assert is_valid is True
        assert error == ""
    
    def test_valid_subdomain(self):
        is_valid, error = validate_origin("https://app.example.com")
        assert is_valid is True
        assert error == ""
    
    def test_valid_firebase_hosting(self):
        is_valid, error = validate_origin("https://airs-demo.web.app")
        assert is_valid is True
        assert error == ""
    
    def test_valid_127_0_0_1(self):
        is_valid, error = validate_origin("http://127.0.0.1:3000")
        assert is_valid is True
        assert error == ""
    
    def test_wildcard_is_valid(self):
        is_valid, error = validate_origin("*")
        assert is_valid is True
    
    def test_empty_origin(self):
        is_valid, error = validate_origin("")
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_missing_scheme(self):
        is_valid, error = validate_origin("example.com")
        assert is_valid is False
        assert "scheme" in error.lower()
    
    def test_invalid_scheme_ftp(self):
        is_valid, error = validate_origin("ftp://example.com")
        assert is_valid is False
        assert "scheme" in error.lower()
    
    def test_origin_with_path(self):
        is_valid, error = validate_origin("https://example.com/path")
        assert is_valid is False
        assert "path" in error.lower()
    
    def test_origin_with_query(self):
        is_valid, error = validate_origin("https://example.com?foo=bar")
        assert is_valid is False
        assert "query" in error.lower()
    
    def test_trailing_slash_accepted(self):
        # The validator allows trailing slash for normalization
        is_valid, error = validate_origin("https://example.com/")
        assert is_valid is True


class TestGetAllowedOrigins:
    """Tests for get_allowed_origins function."""
    
    def test_single_origin(self):
        with patch.dict(os.environ, {"CORS_ALLOW_ORIGINS": "https://example.com"}, clear=False):
            origins = get_allowed_origins(is_production=True)
            assert "https://example.com" in origins
    
    def test_multiple_origins_comma_separated(self):
        with patch.dict(os.environ, {"CORS_ALLOW_ORIGINS": "https://a.com,https://b.com"}, clear=False):
            origins = get_allowed_origins(is_production=True)
            assert "https://a.com" in origins
            assert "https://b.com" in origins
    
    def test_whitespace_trimmed(self):
        with patch.dict(os.environ, {"CORS_ALLOW_ORIGINS": "  https://a.com , https://b.com  "}, clear=False):
            origins = get_allowed_origins(is_production=True)
            assert "https://a.com" in origins
            assert "https://b.com" in origins
    
    def test_trailing_slash_removed(self):
        with patch.dict(os.environ, {"CORS_ALLOW_ORIGINS": "https://example.com/"}, clear=False):
            origins = get_allowed_origins(is_production=True)
            assert "https://example.com" in origins
    
    def test_invalid_origins_filtered(self):
        with patch.dict(os.environ, {"CORS_ALLOW_ORIGINS": "https://valid.com,invalid,https://also-valid.com"}, clear=False):
            origins = get_allowed_origins(is_production=True)
            assert "https://valid.com" in origins
            assert "https://also-valid.com" in origins
            assert "invalid" not in origins
    
    def test_deduplication(self):
        with patch.dict(os.environ, {"CORS_ALLOW_ORIGINS": "https://a.com,https://a.com"}, clear=False):
            origins = get_allowed_origins(is_production=True)
            assert origins.count("https://a.com") == 1
    
    def test_wildcard_in_development(self):
        with patch.dict(os.environ, {"CORS_ALLOW_ORIGINS": "*"}, clear=False):
            origins = get_allowed_origins(is_production=False)
            assert origins == ["*"]
    
    def test_wildcard_blocked_in_production(self):
        with patch.dict(os.environ, {"CORS_ALLOW_ORIGINS": "*"}, clear=False):
            origins = get_allowed_origins(is_production=True)
            assert origins == []
    
    def test_dev_mode_auto_adds_localhost(self):
        """In dev mode, localhost:3000 and localhost:5173 are auto-added."""
        with patch.dict(os.environ, {"CORS_ALLOW_ORIGINS": "https://example.com"}, clear=False):
            origins = get_allowed_origins(is_production=False)
            assert "https://example.com" in origins
            assert "http://localhost:3000" in origins
            assert "http://localhost:5173" in origins
    
    def test_dev_mode_empty_still_has_localhost(self):
        """In dev mode with no CORS_ALLOW_ORIGINS, localhost is still added."""
        with patch.dict(os.environ, {"CORS_ALLOW_ORIGINS": ""}, clear=False):
            origins = get_allowed_origins(is_production=False)
            assert "http://localhost:3000" in origins
            assert "http://localhost:5173" in origins
    
    def test_prod_mode_rejects_localhost(self):
        """In prod mode, localhost origins are rejected."""
        with patch.dict(os.environ, {"CORS_ALLOW_ORIGINS": "https://example.com,http://localhost:5173"}, clear=False):
            origins = get_allowed_origins(is_production=True)
            assert "https://example.com" in origins
            assert "http://localhost:5173" not in origins
            assert "http://localhost:3000" not in origins
    
    def test_prod_mode_rejects_non_https(self):
        """In prod mode, non-HTTPS origins are rejected."""
        with patch.dict(os.environ, {"CORS_ALLOW_ORIGINS": "https://secure.com,http://insecure.com"}, clear=False):
            origins = get_allowed_origins(is_production=True)
            assert "https://secure.com" in origins
            assert "http://insecure.com" not in origins
    
    def test_prod_mode_no_auto_localhost(self):
        """In prod mode, localhost is NOT auto-added."""
        with patch.dict(os.environ, {"CORS_ALLOW_ORIGINS": "https://example.com"}, clear=False):
            origins = get_allowed_origins(is_production=True)
            assert "https://example.com" in origins
            assert "http://localhost:3000" not in origins
            assert "http://localhost:5173" not in origins
    
    def test_env_var_not_set_dev_mode(self):
        """When env var not set in dev mode, still gets localhost."""
        env = os.environ.copy()
        env.pop("CORS_ALLOW_ORIGINS", None)
        with patch.dict(os.environ, env, clear=True):
            origins = get_allowed_origins(
                env_var="CORS_ALLOW_ORIGINS",
                default="",
                is_production=False
            )
            assert "http://localhost:3000" in origins
            assert "http://localhost:5173" in origins
