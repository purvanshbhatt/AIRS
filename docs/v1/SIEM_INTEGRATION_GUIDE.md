# Real-World Evidence Module: Wazuh & Splunk Integration

**Version 1.0** | May 2026

---

## Overview

The Real-World Evidence (RWE) module connects ResilAI to Wazuh (XDR) and Splunk (SIEM) to enable **Tier 3 (SIEM-Verified)** governance scoring. Instead of relying on self-reported questionnaire answers, ResilAI now pulls live telemetry to verify security controls.

### Key Capabilities

✅ **Wazuh Integration (XDR Layer)**
- Endpoint health monitoring (active vs disconnected agents)
- Vulnerability detection & CVE alerting
- Auto-generation of findings for critical vulnerabilities

✅ **Splunk Integration (SIEM Layer)**
- Logging persistence verification (heartbeat check)
- Custom SPL query execution
- Security drift detection

✅ **GHI Enhancement**
- 1.2x multiplier for SIEM-verified controls
- Evidence-based scoring rewards real security observability

✅ **Automated Finding Generation**
- Critical CVE auto-detection (CVE-2024-3094, etc)
- High disconnection rate alerts (>10%)
- Automatic GHI impact computation

---

## Architecture

```
ResilAI Platform
├── Wazuh Integration
│   ├── Agent Status Monitoring (GET /api/integrations/wazuh/agent-status)
│   ├── Vulnerability Detection (GET /api/integrations/wazuh/vulnerabilities)
│   └── Auto-Finding Generation
│
├── Splunk Integration
│   ├── Logging Health Check (GET /api/integrations/splunk/logging-health)
│   ├── Custom Queries (POST /api/integrations/splunk/query)
│   └── Drift Detection
│
├── Enhanced GHI Scoring
│   ├── Base GHI Calculation (existing)
│   ├── SIEM Multiplier Application (×1.2)
│   └── Evidence-Based Grade Assignment
│
└── Health Monitoring
    └── /health/system endpoint reports SIEM connectivity
```

---

## API Reference

### Configuration Endpoints

#### Configure Wazuh Integration
```http
POST /api/integrations/wazuh/configure
Authorization: Bearer {token}
Content-Type: application/json

{
  "wazuh_host": "wazuh.example.com",
  "wazuh_api_key": "your-api-key",
  "wazuh_port": 55000,
  "verify_ssl": true
}

Response:
{
  "status": "configured",
  "host": "wazuh.example.com",
  "port": 55000,
  "message": "Wazuh connection validated successfully"
}
```

#### Configure Splunk Integration
```http
POST /api/integrations/splunk/configure
Authorization: Bearer {token}
Content-Type: application/json

{
  "splunk_host": "splunk.example.com",
  "splunk_hec_token": "your-hec-token",
  "splunk_port": 8089,
  "verify_ssl": true
}

Response:
{
  "status": "configured",
  "host": "splunk.example.com",
  "port": 8089,
  "message": "Splunk connection validated successfully"
}
```

### Evidence Collection Endpoints

#### Get Wazuh Agent Status
```http
GET /api/integrations/wazuh/agent-status
Authorization: Bearer {token}

Response:
{
  "total_agents": 42,
  "active_agents": 40,
  "disconnected_agents": 2,
  "pending_agents": 0,
  "never_connected_agents": 0,
  "disconnection_rate_percent": 4.76,
  "agent_list": [
    {
      "agent_id": "001",
      "agent_name": "linux-prod-01",
      "ip_address": "192.168.1.10",
      "status": "active",
      "last_keepalive": "2026-05-08T10:30:00Z",
      "os_platform": "Linux",
      "os_version": "5.15.0"
    }
  ],
  "verified_at": "2026-05-08T10:35:20Z"
}
```

**SIEM Evidence Mapping:**
- If `disconnection_rate_percent > 10%`: Automatically triggers high-severity finding in "Detection Coverage" domain

#### Get Wazuh Vulnerabilities
```http
GET /api/integrations/wazuh/vulnerabilities?severity=critical&limit=100
Authorization: Bearer {token}

Response:
{
  "total_vulnerabilities": 3,
  "critical_count": 1,
  "high_count": 1,
  "medium_count": 1,
  "low_count": 0,
  "vulnerabilities": [
    {
      "cve_id": "CVE-2024-3094",
      "title": "XZ Utils Backdoor",
      "severity": "critical",
      "cvss_score": 9.8,
      "agent_id": "001",
      "agent_name": "linux-prod-01",
      "timestamp": "2026-05-08T10:15:00Z",
      "description": "Supply-chain backdoor in XZ Utils",
      "affected_packages": ["xz-utils-5.2.5-2"],
      "remediation": "Upgrade to xz-utils >= 5.2.5-3"
    }
  ],
  "verified_at": "2026-05-08T10:35:20Z"
}
```

**SIEM Evidence Mapping:**
- CVE-2024-3094 (XZ Utils): Auto-generates **+15 GHI impact** remediation task
- Other critical CVEs: Auto-generates **+10 GHI impact** remediation task
- Automatic assignment to org_admin for triage

#### Check Splunk Logging Health
```http
GET /api/integrations/splunk/logging-health?sourcetype=resilai_drift&index=security_alerts
Authorization: Bearer {token}

Response:
{
  "logging_enabled": true,
  "last_event_time": "2026-05-08T10:32:15Z",
  "event_count_24h": 47293,
  "event_count_7d": 331456,
  "sourcetypes_active": ["resilai_drift"],
  "indexes_active": ["security_alerts"],
  "verified_at": "2026-05-08T10:35:20Z"
}
```

**SIEM Evidence Mapping:**
- Successful heartbeat: Marks "Centralized Logging Enabled" as **verified** in Telemetry & Logging domain
- Event flow confirmation: Enables 1.2x GHI multiplier

#### Execute Custom Splunk Query
```http
POST /api/integrations/splunk/query
Authorization: Bearer {token}
Content-Type: application/json

{
  "query": "index=security_alerts sourcetype=resilai_drift | stats count by severity",
  "earliest": "-7d",
  "latest": "now",
  "max_results": 1000
}

Response:
{
  "results": [
    {"severity": "critical", "count": 42},
    {"severity": "high", "count": 156},
    {"severity": "medium", "count": 892}
  ],
  "total_count": 3,
  "query_used": "index=security_alerts sourcetype=resilai_drift | stats count by severity"
}
```

### Status & Monitoring Endpoints

#### Get SIEM Integration Status
```http
GET /api/integrations/status
Authorization: Bearer {token}

Response:
{
  "wazuh_status": "configured",
  "wazuh_message": "Wazuh manager connected",
  "wazuh_last_successful": "2026-05-08T10:35:20Z",
  "splunk_status": "configured",
  "splunk_message": "Splunk instance connected",
  "splunk_last_successful": "2026-05-08T10:32:15Z",
  "siem_verified_controls": 2,
  "siem_verified_percentage": 100.0
}
```

#### Check System Health with SIEM Status
```http
GET /health/system

Response:
{
  "version": "1.0.0",
  "environment": "staging",
  "llm_enabled": true,
  "demo_mode": false,
  "is_read_only": false,
  "integrations_enabled": true,
  "last_deployment_at": "2026-05-08T09:00:00Z",
  "wazuh_connected": true,
  "splunk_connected": true,
  "siem_verified": true
}
```

---

## GHI Scoring with SIEM Multiplier

### Formula

**Base GHI** (existing):
```
GHI = (Audit × 0.4) + (Lifecycle × 0.3) + (SLA × 0.2) + (Compliance × 0.1)
```

**Enhanced GHI** (with SIEM verification):
```
If SIEM-verified controls > 0:
  Final GHI = min(100, Base GHI × 1.2)
Else:
  Final GHI = Base GHI
```

### Example Scoring

| Scenario | Base GHI | SIEM Verified | Multiplier | Final GHI | Grade |
|----------|----------|---------------|-----------|-----------|-------|
| Self-reported only | 80 | No | 1.0 | 80 | B |
| Wazuh verified | 80 | Yes (agents active) | 1.2 | 96 | A |
| Splunk verified | 80 | Yes (logging enabled) | 1.2 | 96 | A |
| Both verified | 80 | Yes (both active) | 1.2 | 96 | A |
| Near-perfect + verified | 90 | Yes | 1.2 | 100 | A (capped) |

---

## Automated Finding Generation

### CVE Auto-Detection

When Wazuh detects critical CVEs, findings are automatically created with GHI impact:

#### CVE-2024-3094 (XZ Utils Backdoor)
- **Severity**: CRITICAL
- **GHI Impact**: +15
- **Status**: Auto-generated as OPEN
- **Priority**: 1 (highest)
- **Assignment**: org_admin for immediate triage

#### Other 2024 CVEs
- **Severity**: HIGH
- **GHI Impact**: +8-10 per CVE
- **Status**: Auto-generated as OPEN
- **Assignment**: Included in Remediation Ledger

### Agent Disconnection Auto-Detection

When agent disconnection rate exceeds 10%:
- **Finding Type**: High-severity detection gap
- **Domain**: Detection Coverage
- **Status**: Auto-generated as OPEN
- **Recommendation**: Investigate connectivity, ensure agents running

---

## Implementation Examples

### Python: Using Wazuh Client

```python
from app.services.wazuh_client import WazuhClient
import asyncio

async def check_vulnerabilities():
    client = WazuhClient(
        host="wazuh.example.com",
        api_key="your-api-key",
        port=55000,
        verify_ssl=True,
    )
    
    # Get agent status
    agents = await client.get_agent_status()
    print(f"Active agents: {agents.active_agents}/{agents.total_agents}")
    print(f"Disconnection rate: {agents.disconnection_rate:.1f}%")
    
    # Get vulnerabilities
    vulns = await client.get_vulnerabilities(severity="critical")
    print(f"Critical CVEs: {vulns.critical_count}")
    for vuln in vulns.vulnerabilities:
        print(f"  - {vuln.cve_id}: {vuln.title}")

asyncio.run(check_vulnerabilities())
```

### Python: Using Enhanced GHI Scoring

```python
from app.services.governance.scoring_v2 import (
    compute_ghi_with_siem,
    evaluate_siem_context,
)

# Fetch SIEM data
wazuh_agents = await wazuh_client.get_agent_status()
splunk_logging = await splunk_client.verify_logging_health()

# Create SIEM context
siem_context = evaluate_siem_context(
    wazuh_agent_status=wazuh_agents.to_dict(),
    splunk_logging_health=splunk_logging.to_dict(),
)

# Compute enhanced GHI
ghi_result = compute_ghi_with_siem(
    db=session,
    organization_id=org_id,
    audit_score=85,
    lifecycle_score=75,
    sla_score=90,
    compliance_score=80,
    siem_context=siem_context,
)

print(f"Base GHI: {ghi_result['base_ghi']}")
print(f"Final GHI (with SIEM): {ghi_result['final_ghi']}")
print(f"Multiplier Applied: {ghi_result['siem_multiplier']}x")
print(f"Grade: {ghi_result['grade']}")
```

### FastAPI: Using Integration Endpoints

```python
from fastapi import APIRouter, Depends
from app.api.v1.integrations import router as integrations_router

# Include in main app
app.include_router(integrations_router)

# Available endpoints:
# POST   /api/integrations/wazuh/configure
# GET    /api/integrations/wazuh/agent-status
# GET    /api/integrations/wazuh/vulnerabilities
# POST   /api/integrations/splunk/configure
# POST   /api/integrations/splunk/query
# GET    /api/integrations/splunk/logging-health
# GET    /api/integrations/status
```

---

## Security Considerations

### Credential Management

**Development/Testing:**
```python
# Use environment variables or .env.dev
WAZUH_HOST=wazuh.example.com
WAZUH_API_KEY=your-api-key
SPLUNK_HOST=splunk.example.com
SPLUNK_HEC_TOKEN=your-hec-token
```

**Production:**
```python
# Use Google Cloud Secret Manager
from google.cloud import secretmanager

def get_wazuh_api_key():
    client = secretmanager.SecretManagerServiceClient()
    name = "projects/YOUR-PROJECT/secrets/wazuh-api-key/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
```

### Encryption

All SIEM telemetry payloads are encrypted in Firestore using AES-256-GCM:

```python
from app.core.security.encryption import encrypt_field, decrypt_field

# Encrypt before storing
encrypted = encrypt_field(wazuh_data.to_json())
org.wazuh_telemetry = encrypted

# Decrypt on retrieval
decrypted = decrypt_field(org.wazuh_telemetry)
data = WazuhData.parse_raw(decrypted)
```

### Authorization

All integration endpoints require authentication and restrict to `org_admin` role:

```python
from app.api.routes.auth import require_org_admin

@router.post("/wazuh/configure")
async def configure_wazuh(
    config: WazuhConfigRequest,
    user: User = Depends(require_org_admin),  # Only org admins
):
    # Configure integration
    pass
```

---

## Deployment & Configuration

### Local Development

```bash
# 1. Install dependencies (already in requirements.txt)
pip install -r requirements.txt

# 2. Configure Wazuh and Splunk in .env.dev
echo "WAZUH_HOST=localhost" >> .env.dev
echo "WAZUH_API_KEY=dev-key" >> .env.dev
echo "SPLUNK_HOST=localhost" >> .env.dev
echo "SPLUNK_HEC_TOKEN=dev-token" >> .env.dev

# 3. Run integration tests
py -m pytest tests/test_siem_integrations.py -v

# 4. Start server
python -m uvicorn app.main:app --reload
```

### Staging/Production

```bash
# 1. Set environment variables in Cloud Run
gcloud run deploy airs-api \
  --set-env-vars WAZUH_HOST=wazuh.prod.example.com \
  --set-env-vars WAZUH_API_KEY=$(gcloud secrets versions access latest --secret=wazuh-api-key) \
  --set-env-vars SPLUNK_HOST=splunk.prod.example.com \
  --set-env-vars SPLUNK_HEC_TOKEN=$(gcloud secrets versions access latest --secret=splunk-hec-token)

# 2. Or use Secret Manager directly in code (recommended)
# See credential management section above
```

---

## Monitoring & Alerting

### Key Metrics to Monitor

```
/api/integrations/status
├── Wazuh Connection Status
├── Splunk Connection Status
├── SIEM Verified Controls Count
└── SIEM Verification Percentage

/health/system
├── wazuh_connected (boolean)
├── splunk_connected (boolean)
└── siem_verified (boolean)
```

### Alert Rules (Example)

```
Alert: Wazuh Disconnection Rate > 10%
├── Trigger: GET /api/integrations/wazuh/agent-status
├── Condition: disconnection_rate_percent > 10.0
└── Action: Auto-generate HIGH finding in Detection Coverage domain

Alert: Critical CVE Detected
├── Trigger: GET /api/integrations/wazuh/vulnerabilities
├── Condition: severity == "critical"
└── Action: Auto-generate CRITICAL finding with +15 GHI impact

Alert: Splunk Logging Gap > 1 hour
├── Trigger: GET /api/integrations/splunk/logging-health
├── Condition: (now - last_event_time) > 3600 seconds
└── Action: Alert org_admin, disable Splunk multiplier
```

---

## Testing

### Run Integration Tests

```bash
# All integration tests
py -m pytest tests/test_siem_integrations.py -v

# Specific test
py -m pytest tests/test_siem_integrations.py::TestWazuhClient::test_get_agent_status -v

# With coverage
py -m pytest tests/test_siem_integrations.py --cov=app.services.wazuh_client --cov=app.services.splunk
```

### Mock Testing (No Live Wazuh/Splunk Needed)

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_agent_status_with_mock():
    with patch('app.services.wazuh_client.httpx.AsyncClient'):
        client = WazuhClient("test.com", "key")
        # Mock authentication
        client._jwt_token = "test-token"
        # Test...
```

---

## Troubleshooting

### "Wazuh connection failed"
- Check `wazuh_host` and `wazuh_api_key`
- Verify Wazuh manager is running: `curl -k https://wazuh.example.com:55000`
- Check network connectivity and firewall rules

### "No Splunk logs found"
- Verify `splunk_hec_token` is valid
- Check index and sourcetype are correct: `index=security_alerts sourcetype=resilai_drift`
- Ensure logs are being sent to Splunk

### "SIEM multiplier not applied"
- Verify `wazuh_connected` or `splunk_connected` is `true` via `/health/system`
- Check agent connectivity rate: `GET /api/integrations/wazuh/agent-status`
- Check logging health: `GET /api/integrations/splunk/logging-health`

### "Auto-finding not generated for CVE"
- Check CVE is in critical/high severity
- Check Wazuh query returned results: `GET /api/integrations/wazuh/vulnerabilities?severity=critical`
- Verify assessment exists for org

---

## References

- **Wazuh Documentation**: https://documentation.wazuh.com/current/api/reference.html
- **Splunk SPL Guide**: https://docs.splunk.com/Documentation/SplunkCloud/9.1.3/SearchReference/Thestatscommand
- **Technical Whitepaper**: [docs/whitepaper_governance_architecture.md](../docs/whitepaper_governance_architecture.md)
- **GHI Formula**: [Governance Health Index](../docs/whitepaper_governance_architecture.md#3-the-governance-health-index-ghi)

---

## Support & Issues

For issues, questions, or feature requests:
1. Check existing GitHub issues
2. Create a detailed issue with logs from `/health/system` and `/api/integrations/status`
3. Include error messages from app logs

---

**Last Updated**: May 8, 2026
**Maintainer**: Security Architecture Team
