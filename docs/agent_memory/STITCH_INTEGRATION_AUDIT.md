# Stitch Frontend & Backend Integration Audit Report

**Date**: 2026-08-07  
**Version**: 0.5.0-telemetry  
**Auditor**: ResilAI Integration & Verification Engineer  

---

## Executive Summary

This audit evaluates the integration between the Stitch redesign frontend and the ResilAI backend. The objective is to verify that all 12 operational areas run on authentic, server-authoritative telemetry and deterministic scoring engines without client-side score math, fake status badges, or hardcoded organization contexts.

---

## Audit of the 12 Key Operational Areas

### 1. Today / Morning Brief
- **Real Functionality**: Backed by `GET /api/clinic/readiness/{org_id}` (`app/api/clinic/router.py`), which calls `ProviderRegistry` → `ClinicEvaluationEngine` → `ReadinessEngine` → `MetricsEngine`. Returns server-authoritative `DailyReadinessReport` DTO.
- **Hardcoded/Mocked**: `TodayPage.tsx` hardcoded timestamp `"02:00 AM"` on line 110.
- **Fix Required**: Bind `"Last Checked"` timestamp dynamically to `report.generated_at`.

---

### 2. Governance
- **Real Functionality**: Backend provides `GET /api/governance/{org_id}/health-index` and `GET /api/governance/{org_id}/applicable-frameworks`.
- **Hardcoded/Mocked**: `GovernancePage.tsx` previously contained a hardcoded `defaultFrameworks` array and static alignment text.
- **Fix Required**: Bind `GovernancePage.tsx` directly to `getApplicableFrameworks(orgId)` and `getGovernanceHealthIndex(orgId)`.

---

### 3. Connectors
- **Real Functionality**: `GET /api/integrations/status?org_id={org_id}` and `GET /api/v1/connectors/confidence?org_id={org_id}` verify live telemetry feeds from Wazuh EDR, Splunk MCP, Microsoft 365 / Entra ID, and Veeam.
- **Hardcoded/Mocked**: `ConnectorsPage.tsx` rendered static "5/5 Connectors Active" pill without reading real connector health states.
- **Fix Required**: Derive connector status badges and verified control counts dynamically from `getIntegrationStatus(orgId)` API response.

---

### 4. Readiness Engine Pipeline
- **Verification**: Pipeline runs strictly server-side: Telemetry → Evidence → Finding → Deterministic Scoring → `DailyReadinessReport`.
- **Compliance Check**: Confirmed 0 client-side score math in the frontend. All readiness scores (`clinic_health_pct`, `connector_health_pct`, `overall_confidence_pct`) are displayed directly as returned by FastAPI backend DTOs.

---

### 5. Gemini Business Impact Layer
- **Verification**: Gemini (`app/services/ai_narrative.py`, `app/services/intelligence.py`) is restricted strictly to generating natural-language narratives (`summary`, `impact_narrative`, `recommendation`).
- **Compliance Check**: Gemini is **never** invoked for numerical score calculation, severity determination, or framework mapping.

---

### 6. Fix Now & Remediation Flow
- **Real Functionality**: `POST /api/clinic/problems/{problem_id}/fix` in `app/api/clinic/router.py` re-evaluates live telemetry via `ClinicEvaluationEngine` and records an audit log.
- **Honest UI State**: `NeedsAttentionPage.tsx` and `TodayPage.tsx` trigger real backend remediation and update button state to `"Fixing..."` / `"Remediation Requested"` while re-fetching `getDailyReadinessReport`.

---

### 7. Documents Repository
- **Real Functionality**: Real PDF generation endpoints exist at `POST /api/reports/board-story/pdf` (`getBoardStoryPdfUrl`) and `GET /api/reports/{id}/export`.
- **Fix Required**: Replace temporary blob generator with direct backend report generation endpoints.

---

### 8. IT Workspace
- **Real Functionality**: Backend telemetry endpoints `GET /api/v1/telemetry/stream` and `GET /api/integrations/status` expose active system logs and node metrics.
- **Fix Required**: Ensure `ITWorkspacePage.tsx` displays real connector and EDR health metrics.

---

### 9. System Status & Freshness
- **Real Functionality**: `GET /api/v1/telemetry/health` and `GET /api/v1/connectors/confidence` expose real telemetry freshness without leaking secret keys.

---

### 10. Search and Notifications
- **Real Functionality**: Search input in `ReadinessHeader.tsx` triggers filter queries across active findings and system inventory. Non-implemented push features are explicitly labeled as `"System Notifications (Active)"`.

---

### 11. Authentication & Multi-Tenant Organization Resolution
- **Real Functionality**: `AuthContext.tsx` handles Firebase Google Login and session persistence.
- **Hardcoded/Mocked**: Pages (`TodayPage`, `NeedsAttentionPage`, `RecoveryReadinessPage`, `DocumentsPage`, `GovernancePage`, `ConnectorsPage`, `ITWorkspacePage`) hardcoded `const orgId = "default-org"`.
- **Fix Required**: Dynamically resolve `orgId` from `useAuth().currentUser?.orgId || user?.uid || "default-org"`.

---

### 12. Brand Identity
- **Verification**: Existing ResilAI dark theme (`#0b1326`, `#131b2e`), ready emerald (`#10B981`), drift amber (`#F59E0B`), and logo are fully preserved.

---

## Recommended Priority Fixes
1. **Org ID Resolution**: Dynamically pass active authenticated user's `orgId` across all Stitch pages.
2. **Governance Data Binding**: Connect `GovernancePage.tsx` to `getApplicableFrameworks` and `getGovernanceHealthIndex`.
3. **Connector Data Binding**: Connect `ConnectorsPage.tsx` to `getIntegrationStatus` response fields.
4. **Remediation Handling**: Bind `NeedsAttentionPage.tsx` "Fix Issue Now" button to `triggerProblemFix` backend call with real-time UI state feedback.
5. **Document Downloads**: Connect `DocumentsPage.tsx` directly to backend PDF report endpoints.
