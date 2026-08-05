# Release Notes — ResilAI (AIRS) v1.3.0

**Release Version**: v1.3.0  
**Release Name**: Sprint 3: Platform Consolidation & Production Readiness  
**Release Date**: 2026-08-04  

---

## 🚀 Highlights

### 1. Dual Workspace Architecture (Business & Technology Operations)
- Introduces progressive disclosure navigation shell grouping Morning Brief, Needs Attention, Recovery, and Technology Operations domains (Identity, Devices, Backups, Email, Network, Cloud, AI).
- Preserves all 7 legacy graph tools (`EvidenceNetwork`, `ComplianceDrift`, `TechnologyIntelligence`, `ReliabilityDashboard`, `RemediationLedger`, `DecisionEngine`, `AIAttackSimulationLab`) remapped into the Operations workspace.

### 2. First-Class Sales Demo Mode (Acme Health Systems)
- Delivers complete mock telemetry for Acme Health Systems profile (98% clinic health, `safe_to_open`, 7 healthy connectors, zero blockers).
- Enforces client/server mutation firewall blocking write operations with user-facing toast alerts.

### 3. Terminology Overhaul ("Verification" -> "Health Check")
- Renames all customer-facing UI references, headers, drawers, tables, and badges from "Verification" to "Health Check" while maintaining backwards-compatible type aliases.

### 4. Phase 9 Live Staging Deployment & E2E Validation
- Deploys backend API to Cloud Run (`https://airs-api-staging-knu3wsxymq-uc.a.run.app`).
- Deploys frontend to Firebase Hosting (`https://airs-staging-0384513977.web.app`).
- Eliminates 401 redirect loops via `auth.authStateReady()` and explicit `browserLocalPersistence`.
- Verifies 100% pass rate across live integration test suite (`scripts/verify_staging.py`).

---

## 📋 Deliverables Documentation Suite
All 13 canonical deliverable reports generated and verified:
1. `PRODUCT_MAP.md`
2. `STAGING_TEST_REPORT.md`
3. `UI_INVENTORY.md`
4. `DESIGN_SYSTEM.md`
5. `FEATURE_MAP.md`
6. `ROUTE_MAP.md`
7. `COMPONENT_MAP.md`
8. `FRONTEND_ARCHITECTURE.md`
9. `API_CONTRACT.md`
10. `STATE_MANAGEMENT.md`
11. `PERFORMANCE_AUDIT.md`
12. `SECURITY_AUDIT.md`
13. `RELEASE_NOTES.md`
