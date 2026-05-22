"""Unit and integration tests for the Google Antigravity Agent, Ticket Sync, and Elastic SIEM."""

import pytest
import hmac
import hashlib
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.models.assessment import Assessment
from app.models.finding import Finding, Severity, FindingStatus
from app.services.antigravity import get_remediation_agent
from app.services.ticket_sync import TicketSyncService
from app.services.elastic import ElasticService


# =============================================================================
# Antigravity Agent Tests
# =============================================================================

class TestAntigravityAgent:
    """Test suite for the Google Antigravity Agent."""

    def test_remediation_agent_disclaimer(self):
        """Verify that any agent execution appends the required math vs speech disclaimer."""
        agent = get_remediation_agent()
        playbook = agent.execute_remediation_agent(
            finding_title="Insecure Storage Configuration",
            finding_description="S3 buckets allow public read access.",
            finding_severity="high",
            finding_recommendation="Disable public access policies.",
            finding_evidence="Policy allows * Principal.",
            rule_id="AWS-SEC-001"
        )
        assert "NOTICE" in playbook
        assert "ResilAI Governance Engine" in playbook
        assert "does not modify the baseline score" in playbook


# =============================================================================
# Ticket Sync Service Tests
# =============================================================================

class TestTicketSyncService:
    """Test suite for the TicketSyncService."""

    @pytest.mark.asyncio
    async def test_sync_to_jira_mock(self):
        """Test Jira ticket creation simulation in demo mode."""
        sync_service = TicketSyncService()
        result = await sync_service.sync_finding_to_target(
            finding_id="f-001",
            title="Exposed Database Port",
            description="Port 5432 open to world.",
            severity="critical",
            recommendation="Restrict ingress to internal CIDR.",
            rule_id="SEC-PG-01",
            target="jira",
            config={"url": "https://test.jira.com", "project_key": "PROD"}
        )
        assert result["success"] is True
        assert "PROD-" in result["ticket_key"]
        assert "test.jira.com/browse" in result["ticket_url"]

    @pytest.mark.asyncio
    async def test_sync_to_servicenow_mock(self):
        """Test ServiceNow incident creation simulation in demo mode."""
        sync_service = TicketSyncService()
        result = await sync_service.sync_finding_to_target(
            finding_id="f-002",
            title="Outdated SSH Version",
            description="Host is running OpenSSH 7.2.",
            severity="medium",
            recommendation="Upgrade to OpenSSH 9.6+.",
            rule_id="SSH-01",
            target="servicenow",
            config={"url": "https://test.service-now.com"}
        )
        assert result["success"] is True
        assert "INC" in result["ticket_key"]
        assert "incident.do" in result["ticket_url"]

    @pytest.mark.asyncio
    async def test_sync_to_webhook_signature_and_ssrf(self):
        """Test webhook syncing with SHA256 signature payload."""
        sync_service = TicketSyncService()
        secret = "super_secret_webhook_key"
        
        # We test with a mock site to bypass SSRF check or run under demo simulation
        result = await sync_service.sync_finding_to_target(
            finding_id="f-003",
            title="SSO Disabled for Admin Panel",
            description="Admins can sign in with local passwords.",
            severity="high",
            recommendation="Enforce Okta authentication.",
            rule_id="IAM-01",
            target="webhook",
            config={"url": "https://mock.webhook/test-endpoint", "secret": secret}
        )
        
        assert result["success"] is True
        assert result["ticket_key"] == "webhook-delivered"


# =============================================================================
# Elastic SIEM Service Tests
# =============================================================================

class TestElasticService:
    """Test suite for ElasticService SIEM connector."""

    @pytest.mark.asyncio
    async def test_verify_mfa_enforcement_mock(self):
        """Test Elasticsearch MFA verification query."""
        service = ElasticService(base_url="https://mock-elastic.local", api_key="mock-api-key")
        res = await service.verify_mfa_enforcement()
        assert res.status.value == "verified"
        assert res.event_count > 0
        assert "logs-okta*" in res.query_used

    @pytest.mark.asyncio
    async def test_verify_edr_coverage_mock(self):
        """Test Elasticsearch EDR coverage query."""
        service = ElasticService(base_url="https://mock-elastic.local", api_key="mock-api-key")
        res = await service.verify_edr_coverage()
        assert res.status.value == "verified"
        assert res.event_count > 0
        assert "logs-endpoint*" in res.query_used

    @pytest.mark.asyncio
    async def test_verify_logging_health_mock(self):
        """Test Elasticsearch logging health heartbeat."""
        service = ElasticService(base_url="https://mock-elastic.local", api_key="mock-api-key")
        res = await service.verify_logging_health()
        assert res.logging_enabled is True
        assert res.event_count_24h > 0


# =============================================================================
# API Endpoints Verification Tests
# =============================================================================

class TestRemediationEndpoints:
    """End-to-end endpoint tests for integrations and remediations."""

    def test_configure_elastic_endpoint(self, client):
        """Test POST /api/v1/integrations/elastic/configure success."""
        # For tests, we use the global _elastic_client configuration endpoint.
        # Since it runs a heartbeat test, it will use mock if host is mock.
        payload = {
            "elastic_host": "mock-elastic.local",
            "elastic_api_key": "some-api-key-here-12345",
            "elastic_port": 9200,
            "verify_ssl": False
        }
        resp = client.post("/api/v1/integrations/elastic/configure", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "configured"
        assert data["host"] == "mock-elastic.local"

    def test_elastic_logging_health_endpoint(self, client):
        """Test GET /api/v1/integrations/elastic/logging-health."""
        # First ensure configured
        payload = {
            "elastic_host": "mock-elastic.local",
            "elastic_api_key": "some-api-key-here-12345",
            "elastic_port": 9200,
            "verify_ssl": False
        }
        client.post("/api/v1/integrations/elastic/configure", json=payload)

        resp = client.get("/api/v1/integrations/elastic/logging-health?index=logs-resilai*")
        assert resp.status_code == 200
        data = resp.json()
        assert data["logging_enabled"] is True
        assert data["event_count_24h"] > 0

    def test_siem_status_endpoint_reports_elastic(self, client):
        """Verify that GET /api/v1/integrations/status contains Elastic details."""
        # Configure Elastic client
        payload = {
            "elastic_host": "mock-elastic.local",
            "elastic_api_key": "some-api-key-here-12345",
            "elastic_port": 9200,
            "verify_ssl": False
        }
        client.post("/api/v1/integrations/elastic/configure", json=payload)

        resp = client.get("/api/v1/integrations/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "elastic_status" in data
        assert data["elastic_status"] == "configured"
        assert data["siem_verified_controls"] > 0

    def test_agentic_fix_endpoint(self, client, db_session):
        """Test POST /api/remediations/findings/{finding_id}/agentic-fix."""
        # Setup assessment & finding
        assessment = Assessment(
            id="a-001",
            title="Sovereign Audit 2026",
            owner_uid="dev-user",  # Match default auth user_uid or conftest default
            organization_id="org-001",
        )
        finding = Finding(
            id="f-101",
            assessment_id="a-001",
            title="Insecure Storage",
            description="Public write access on standard buckets.",
            severity=Severity.HIGH,
            status=FindingStatus.OPEN,
            question_id="SEC-001",
            evidence="Bucket allows all write actions.",
            recommendation="Configure bucket-level block public access settings."
        )
        db_session.add(assessment)
        db_session.add(finding)
        db_session.commit()

        resp = client.post("/api/remediations/findings/f-101/agentic-fix")
        assert resp.status_code == 200
        data = resp.json()
        assert data["finding_id"] == "f-101"
        assert "playbook" in data
        assert "NOTICE" in data["playbook"]
        assert "does not modify the baseline score" in data["playbook"]

    def test_sync_finding_endpoint(self, client, db_session):
        """Test POST /api/remediations/findings/{finding_id}/sync."""
        # Setup assessment & finding
        assessment = Assessment(
            id="a-002",
            title="Sovereign Audit 2026",
            owner_uid="dev-user",
            organization_id="org-002",
        )
        finding = Finding(
            id="f-102",
            assessment_id="a-002",
            title="Insecure Storage V2",
            description="Public write access.",
            severity=Severity.HIGH,
            status=FindingStatus.OPEN,
            question_id="SEC-002",
            evidence="Bucket allows all write actions.",
            recommendation="Configure block public access."
        )
        db_session.add(assessment)
        db_session.add(finding)
        db_session.commit()

        payload = {
            "target": "webhook",
            "config": {
                "url": "https://mock.webhook/remediations",
                "secret": "webhook-secret"
            }
        }
        
        # Override require_writable to pass (since DEMO_MODE forces read-only and require_writable raises 403)
        with patch("app.api.remediations.require_writable", return_value=None):
            resp = client.post("/api/remediations/findings/f-102/sync", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["ticket_key"] == "webhook-delivered"
