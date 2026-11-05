# API Contract Specification — ResilAI (AIRS)

**Version**: 1.3.0  
**Environment Compliance**: Staging / Production  
**Backend Compliance Policy (R13)**: The frontend MUST consume only the frozen backend contract. No client-side business calculations, score computations, or connector inferences are performed on the frontend.

---

## 1. Core REST Endpoints

### 1.1 Environment Configuration
- **Method**: `GET`
- **URI**: `/api/v1/config`
- **Authentication**: None (Public Endpoint)
- **Response Payload**:
```json
{
  "environment": "staging",
  "api_base_url": "https://airs-api-staging-knu3wsxymq-uc.a.run.app",
  "analytics_enabled": true,
  "auth_provider": "firebase",
  "app_name": "ResilAI",
  "app_version": "1.3.0"
}
```

### 1.2 System Health & Status
- **Method**: `GET`
- **URI**: `/health` and `/health/system`
- **Authentication**: None (Public Probe)
- **Response Payload (`/health`)**:
```json
{
  "status": "ok",
  "product": {
    "name": "ResilAI",
    "version": "1.3.0"
  }
}
```
- **Response Payload (`/health/system`)**:
```json
{
  "version": "1.3.0",
  "environment": "staging",
  "llm_enabled": true,
  "demo_mode": false,
  "is_read_only": false,
  "integrations_enabled": true,
  "wazuh_connected": true,
  "splunk_connected": true,
  "elastic_connected": false,
  "siem_verified": true
}
```

### 1.3 Clinic Daily Readiness Report (Product Layer)
- **Method**: `GET`
- **URI**: `/api/clinic/readiness/{org_id}`
- **Authentication**: Bearer Token required when `AUTH_REQUIRED=true`
- **Response Payload**:
```json
{
  "org_id": "acme-health",
  "clinic_health_pct": 98,
  "status": "safe_to_open",
  "business_continuity": {
    "status": "verified",
    "ransomware_safe": true,
    "blockers": []
  },
  "connectors": [
    { "id": "m365", "name": "Microsoft 365", "status": "healthy" },
    { "id": "wazuh", "name": "Wazuh EDR", "status": "healthy" },
    { "id": "veeam", "name": "Veeam Backup", "status": "healthy" }
  ],
  "health_check": {
    "last_health_check_time": "2026-08-04T19:40:00Z",
    "health_check_source": "Deterministic Engine",
    "cryptographic_hash": "sha256-e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  }
}
```

---

## 2. Interactive Sales Demo Firewall Contract

When `env=demo` or `host.includes('demo')`, all POST, PUT, DELETE, and PATCH endpoints intercept mutations with HTTP 403 Forbidden:
```json
{
  "detail": {
    "message": "Read-Only Demo: Saving changes is disabled in the interactive demo."
  }
}
```
Frontend dispatches event `resilai-readonly-action` to notify the user via Toast alert.
