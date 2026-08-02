"""
Unit tests for SIEM/XDR integration modules.

Tests cover:
  - Wazuh client (agent status, vulnerabilities)
  - Splunk client enhancements (logging health, custom queries)
  - GHI scoring with SIEM multiplier
  - Automated finding generation for CVEs
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone

# Wazuh Tests
from app.services.wazuh_client import (
    WazuhClient,
    WazuhAgentStatusResponse,
    WazuhVulnerabilitiesResponse,
    AgentStatus,
    VulnerabilityAlert,
    CVESeverity,
)

# Splunk Tests: Splunk legacy classes were removed in Sprint 2.2
# consolidation. Canonical Splunk tests now live in
# tests/test_splunk_adapter.py (the SplunkAdapter) and indirectly via
# ConnectorManager integration tests. The SplunkService facade no
# longer exists, so the previous TestSplunkClient class is removed.

# GHI Scoring Tests
from app.services.governance.scoring_v2 import (
    compute_ghi_with_siem,
    evaluate_siem_context,
    SIEMVerificationContext,
    apply_siem_multiplier,
)

# Finding Generation Tests
from app.services.governance.automated_findings import (
    generate_finding_from_cve,
    generate_remediation_task_from_cve,
    process_wazuh_agent_disconnections,
)


# =============================================================================
# Wazuh Client Tests
# =============================================================================

class TestWazuhClient:
    """Test suite for WazuhClient."""
    
    @pytest.fixture
    def wazuh_client(self):
        """Create a Wazuh client for testing."""
        return WazuhClient(
            host="wazuh.example.com",
            api_key="test-api-key",
            port=55000,
            verify_ssl=True,
        )
    
    @pytest.mark.asyncio
    @patch('app.services.wazuh_client.httpx.AsyncClient')
    async def test_get_jwt_token_success(self, mock_async_client, wazuh_client):
        """Test successful JWT token retrieval."""
        # Mock response
        mock_response = AsyncMock()
        mock_response.json.return_value = {"token": "test-jwt-token"}
        mock_response.raise_for_status.return_value = None
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        mock_async_client.return_value = mock_client
        
        # Call
        token = await wazuh_client._get_jwt_token()
        
        # Assert
        assert token == "test-jwt-token"
        assert wazuh_client._jwt_token == "test-jwt-token"
    
    @pytest.mark.asyncio
    @patch('app.services.wazuh_client.httpx.AsyncClient')
    async def test_get_agent_status(self, mock_async_client, wazuh_client):
        """Test fetching agent status from Wazuh."""
        # Mock JWT retrieval
        wazuh_client._jwt_token = "test-token"
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "data": {
                "affected_items": [
                    {
                        "id": "001",
                        "name": "linux-prod-01",
                        "ip": "192.168.1.10",
                        "status": "active",
                        "lastKeepAlive": "2026-05-08T10:30:00Z",
                        "os": {"platform": "Linux", "version": "5.15.0"},
                    },
                    {
                        "id": "002",
                        "name": "windows-server-01",
                        "ip": "192.168.1.20",
                        "status": "disconnected",
                        "lastKeepAlive": None,
                        "os": {"platform": "Windows", "version": "10"},
                    },
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        mock_async_client.return_value = mock_client
        
        # Call
        result = await wazuh_client.get_agent_status()
        
        # Assert
        assert isinstance(result, WazuhAgentStatusResponse)
        assert result.total_agents == 2
        assert result.active_agents == 1
        assert result.disconnected_agents == 1
        assert result.disconnection_rate == 50.0
    
    @pytest.mark.asyncio
    @patch('app.services.wazuh_client.httpx.AsyncClient')
    async def test_get_vulnerabilities(self, mock_async_client, wazuh_client):
        """Test fetching vulnerabilities from Wazuh."""
        # Mock JWT retrieval
        wazuh_client._jwt_token = "test-token"
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "data": {
                "affected_items": [
                    {
                        "cve": "CVE-2024-3094",
                        "name": "XZ Utils Backdoor",
                        "severity": "critical",
                        "cvss": {"cvss3": {"base_score": 9.8}},
                        "agent_id": "001",
                        "agent_name": "linux-prod-01",
                        "timestamp": "2026-05-08T10:15:00Z",
                        "description": "Supply-chain backdoor in XZ Utils",
                        "package_affected": ["xz-utils-5.2.5-2"],
                        "remediation": "Upgrade to xz-utils >= 5.2.5-3",
                    },
                    {
                        "cve": "CVE-2024-1234",
                        "name": "High-severity RCE",
                        "severity": "high",
                        "cvss": {"cvss3": {"base_score": 8.2}},
                        "agent_id": "002",
                        "agent_name": "windows-server-01",
                        "timestamp": "2026-05-08T10:20:00Z",
                        "description": "Remote code execution vulnerability",
                        "package_affected": ["vulnerable-lib-1.0.0"],
                        "remediation": "Patch to vulnerable-lib-1.1.0",
                    },
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        
        mock_async_client.return_value = mock_client
        
        # Call
        result = await wazuh_client.get_vulnerabilities(severity="critical")
        
        # Assert
        assert isinstance(result, WazuhVulnerabilitiesResponse)
        assert result.total_vulnerabilities == 2
        assert result.critical_count == 1
        assert result.high_count == 1
        assert result.vulnerabilities[0].cve_id == "CVE-2024-3094"


# =============================================================================
# Splunk Client Tests
# =============================================================================
#
# Tests for the canonical SplunkConnector / SplunkAdapter live in
# tests/test_splunk_adapter.py. The legacy ``TestSplunkClient`` class
# that exercised the deleted SplunkService facade has been removed
# in Sprint 2.2 (2026-07-19).
#



# =============================================================================
# GHI Scoring V2 Tests
# =============================================================================

class TestGHIScoringV2:
    """Test suite for SIEM-enhanced GHI scoring."""
    
    def test_evaluate_siem_context_no_data(self):
        """Test SIEM context evaluation with no data."""
        context = evaluate_siem_context()
        
        assert context.wazuh_available is False
        assert context.splunk_available is False
        assert context.siem_verified_controls == 0
        assert context.siem_verification_score == 0.0
    
    def test_evaluate_siem_context_wazuh_connected(self):
        """Test SIEM context with Wazuh data."""
        wazuh_agents = {
            "total_agents": 10,
            "disconnected_agents": 0,
            "disconnection_rate_percent": 0.0,
        }
        
        context = evaluate_siem_context(wazuh_agent_status=wazuh_agents)
        
        assert context.wazuh_available is True
        assert context.wazuh_agents_connected is True
        assert context.siem_verified_controls == 1
        assert context.siem_verification_score == 0.5  # 1 out of 2 possible
    
    def test_evaluate_siem_context_agent_disconnection(self):
        """Test SIEM context with agent disconnections."""
        wazuh_agents = {
            "total_agents": 10,
            "disconnected_agents": 3,
            "disconnection_rate_percent": 30.0,
        }
        
        context = evaluate_siem_context(wazuh_agent_status=wazuh_agents)
        
        assert context.wazuh_available is True
        assert context.wazuh_agents_connected is False
        assert context.wazuh_agent_disconnection_rate == 30.0
        assert context.siem_verified_controls == 0  # Not counted if agents disconnected
    
    def test_evaluate_siem_context_full_coverage(self):
        """Test SIEM context with both Wazuh and Splunk."""
        wazuh_agents = {
            "total_agents": 10,
            "disconnected_agents": 0,
            "disconnection_rate_percent": 0.0,
        }
        splunk_logging = {
            "logging_enabled": True,
            "event_count_24h": 50000,
        }
        
        context = evaluate_siem_context(
            wazuh_agent_status=wazuh_agents,
            splunk_logging_health=splunk_logging,
        )
        
        assert context.siem_verified_controls == 2
        assert context.siem_verification_score == 1.0  # Full coverage
    
    def test_apply_siem_multiplier_with_verification(self):
        """Test 1.2x multiplier when SIEM controls are verified."""
        from app.services.governance.validation_engine import GovernanceHealthIndex, GHI_WEIGHTS
        
        base_ghi = GovernanceHealthIndex(
            ghi=80.0,
            dimensions={"audit": 80, "lifecycle": 80, "sla": 80, "compliance": 80},
            weights=GHI_WEIGHTS,
            grade="B",
        )
        
        siem_context = SIEMVerificationContext(
            wazuh_available=True,
            wazuh_agents_connected=True,
            siem_verified_controls=1,
        )
        
        enhanced = apply_siem_multiplier(base_ghi, siem_context)
        
        # 80 * 1.2 = 96
        assert enhanced.ghi == 96.0
        assert enhanced.grade == "A"
    
    def test_apply_siem_multiplier_capped_at_100(self):
        """Test that SIEM multiplier is capped at 100."""
        from app.services.governance.validation_engine import GovernanceHealthIndex, GHI_WEIGHTS
        
        base_ghi = GovernanceHealthIndex(
            ghi=90.0,
            dimensions={"audit": 90, "lifecycle": 90, "sla": 90, "compliance": 90},
            weights=GHI_WEIGHTS,
            grade="A",
        )
        
        siem_context = SIEMVerificationContext(
            wazuh_available=True,
            wazuh_agents_connected=True,
            siem_verified_controls=1,
        )
        
        enhanced = apply_siem_multiplier(base_ghi, siem_context)
        
        # 90 * 1.2 = 108, but capped at 100
        assert enhanced.ghi == 100.0
        assert enhanced.grade == "A"
    
    def test_apply_siem_multiplier_no_verification(self):
        """Test no multiplier when SIEM controls are not verified."""
        from app.services.governance.validation_engine import GovernanceHealthIndex, GHI_WEIGHTS
        
        base_ghi = GovernanceHealthIndex(
            ghi=80.0,
            dimensions={"audit": 80, "lifecycle": 80, "sla": 80, "compliance": 80},
            weights=GHI_WEIGHTS,
            grade="B",
        )
        
        siem_context = SIEMVerificationContext(
            wazuh_available=False,
            splunk_available=False,
            siem_verified_controls=0,
        )
        
        enhanced = apply_siem_multiplier(base_ghi, siem_context)
        
        # No multiplier applied
        assert enhanced.ghi == 80.0
        assert enhanced.grade == "B"


# =============================================================================
# Automated Finding Generation Tests
# =============================================================================

class TestAutomatedFindings:
    """Test suite for CVE-driven finding generation."""
    
    @pytest.mark.asyncio
    async def test_generate_finding_from_xz_cve(self):
        """Test auto-generation of finding for CVE-2024-3094."""
        # Mock database session
        mock_db = MagicMock()
        
        # Mock assessment
        mock_assessment = MagicMock()
        mock_assessment.id = "test-assessment-id"
        
        # Call
        finding = await generate_finding_from_cve(
            db=mock_db,
            assessment=mock_assessment,
            cve_id="CVE-2024-3094",
            agent_name="linux-prod-01",
            cvss_score=9.8,
            affected_packages=["xz-utils-5.2.5-2"],
            remediation="Upgrade to xz-utils >= 5.2.5-3",
        )
        
        # Assert
        assert finding is not None
        assert "CVE-2024-3094" in finding.title
        assert finding.severity.value == "critical"
        assert "XZ Utils" in finding.title
    
    @pytest.mark.asyncio
    async def test_generate_remediation_task_ghi_impact(self):
        """Test remediation task creation with GHI impact."""
        mock_db = MagicMock()
        
        task = await generate_remediation_task_from_cve(
            db=mock_db,
            organization_id="test-org",
            cve_id="CVE-2024-3094",
            agent_name="linux-prod-01",
            ghi_impact=15,
        )
        
        assert task is not None
        assert task["ghi_impact"] == 15
        assert task["cve_id"] == "CVE-2024-3094"
    
    @pytest.mark.asyncio
    async def test_process_agent_disconnections_high_rate(self):
        """Test auto-finding generation for high agent disconnection rate."""
        mock_db = MagicMock()
        mock_assessment = MagicMock()
        mock_assessment.id = "test-assessment-id"
        
        finding = await process_wazuh_agent_disconnections(
            db=mock_db,
            organization_id="test-org",
            assessment=mock_assessment,
            disconnection_rate=15.0,  # 15% > 10% threshold
            disconnected_agents=3,
            total_agents=20,
        )
        
        assert finding is not None
        assert "Disconnection" in finding.title
        assert finding.severity.value == "high"
    
    @pytest.mark.asyncio
    async def test_process_agent_disconnections_below_threshold(self):
        """Test no finding when disconnection rate is below threshold."""
        mock_db = MagicMock()
        mock_assessment = MagicMock()
        
        finding = await process_wazuh_agent_disconnections(
            db=mock_db,
            organization_id="test-org",
            assessment=mock_assessment,
            disconnection_rate=5.0,  # 5% < 10% threshold
            disconnected_agents=1,
            total_agents=20,
        )
        
        assert finding is None
