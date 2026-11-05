# ResilAI Governance Expansion — Implementation Record

**Version:** v0.7 (Staging Only)
**Status:** Active Development (Not in Demo)
**Branch:** `dev` → staging
**Date:** 2026-02-24

---

## Executive Summary

ResilAI has been expanded from an AI-driven incident readiness assessment tool into a **Continuous Governance & Compliance Intelligence Platform**.

This expansion introduces organizational context awareness, deterministic compliance inference, audit readiness forecasting, and lifecycle governance monitoring.

This implementation is currently deployed in staging and has **not** been merged into demo. The demo environment remains locked at the NIST CSF 2.0 milestone.

---

## 1. Organization Profile Module

### Purpose

Introduce contextual awareness to assessments by capturing regulatory and operational exposure.

### Added Fields

| Field | Type | Description |
|-------|------|-------------|
| `revenue_band` | String(50) | Revenue classification: `<10M`, `10M-100M`, `100M-1B`, `1B+` |
| `employee_count` | Integer | Total employee headcount |
| `geo_regions` | JSON Text | Geographic operating regions: `["US", "EU", "APAC"]` |
| `processes_pii` | Boolean | Organization processes Personally Identifiable Information |
| `processes_phi` | Boolean | Organization processes Protected Health Information |
| `processes_cardholder_data` | Boolean | Organization processes payment card / cardholder data |
| `handles_dod_data` | Boolean | Organization handles Department of Defense data |
| `uses_ai_in_production` | Boolean | AI/ML models deployed in production systems |
| `government_contractor` | Boolean | Organization is a government contractor |
| `financial_services` | Boolean | Organization operates in financial services |
| `application_tier` | String(20) | Uptime classification: `tier_1`, `tier_2`, `tier_3` |
| `sla_target` | Float | User-specified SLA target percentage |

### Impact

Enables deterministic compliance inference and governance weighting without altering scoring logic.

---

## 2. Compliance Applicability Engine

### Type

Deterministic Rule-Based Engine (no AI, no external dependencies)

### Rules Implemented

| Condition | Framework(s) | Mandatory |
|-----------|-------------|-----------|
| `processes_phi = true` | HIPAA | Yes |
| `handles_dod_data = true` | CMMC Level 2, NIST SP 800-171 | Yes |
| `processes_cardholder_data = true` | PCI-DSS v4.0 | Yes |
| `processes_pii = true` AND `"EU" in geo_regions` | GDPR | Yes |
| `processes_pii = true` (non-EU) | NIST Privacy Framework | No |
| `industry in (technology, saas, software)` | SOC 2 Type II | No |
| `uses_ai_in_production = true` | NIST AI RMF | No |
| `financial_services = true` | NIST CSF 2.0, FFIEC IT Handbook | Yes |
| `government_contractor = true` | FedRAMP | No |

### Architecture

- Standalone service module: `services/governance/compliance_engine.py`
- Pure function: `get_applicable_frameworks(org) → List[ApplicableFramework]`
- No LLM usage
- No external API calls

---

## 3. Audit Calendar Module

### Capabilities

- Full CRUD for scheduled audits (external and internal)
- Audit countdown tracking with configurable reminder windows
- Pre-audit risk forecasting via finding cross-reference

### Forecast Logic

Cross-references live findings against framework-specific keywords to generate deterministic risk assessments:

- **Critical**: 3+ critical/high findings OR <30 days with any critical/high finding
- **High**: 1+ critical/high finding OR 5+ related findings
- **Medium**: 2+ related findings
- **Low**: No significant related findings

### Audit Readiness Score (v0.7.1)

```
audit_readiness_score = 100 - (critical_findings × 15) - (high_findings × 8) - (medium_findings × 3)
```

Displayed in staging dashboard per audit entry.

---

## 4. SOC 2 Control Mapping Expansion

Findings now support a `soc2_controls` field (JSON array):

```json
["CC6.1", "CC7.2", "CC8.1"]
```

Enables direct audit traceability from individual findings to SOC 2 Trust Services Criteria.

---

## 5. Tech Stack Lifecycle Governance

### Registry Table

| Field | Description |
|-------|-------------|
| `component_name` | Technology name (e.g., Python, React, PostgreSQL) |
| `version` | Installed version |
| `lts_status` | `lts`, `active`, `deprecated`, `eol` |
| `major_versions_behind` | Count of major versions behind current |
| `category` | Runtime, Framework, Database, Library, etc. |

### Risk Classification

| Condition | Risk Level |
|-----------|------------|
| `lts_status = eol` | Critical |
| `lts_status = deprecated` | High |
| `major_versions_behind >= 3` | High |
| `major_versions_behind >= 1` | Medium |
| Current / LTS | Low |

### Static Lifecycle Config (v0.7.1)

Internal lifecycle database stored in `app/core/lifecycle_config.json`:

```json
{
  "python": {
    "3.8": { "status": "eol", "eol_date": "2024-10-01" },
    "3.9": { "status": "security", "eol_date": "2025-10-01" },
    "3.10": { "status": "active", "eol_date": "2026-10-01" }
  }
}
```

No live scraping. No CVE integration. Governance-only intelligence.

---

## 6. Uptime Tier Governance Logic

### Tiers Defined

| Tier | Classification | Standard SLA |
|------|---------------|-------------|
| Tier 1 | Mission Critical | 99.99% |
| Tier 2 | Business Critical | 99.9% |
| Tier 3 | Important | 99.5% |
| Tier 4 | Internal | 99.0% |

### Features

- SLA gap detection (target vs. tier standard)
- Over-provision warning (when tier SLA exceeds operational need)
- Cost-overprovision detection (Tier 3 org targeting 99.99%)
- Under-provision risk classification
- Audit implication tagging (SOC 2 CC7 impact for Tier 1/2)

---

## 7. Canonical Framework Registry

### Purpose

Normalize framework references across the platform via a proper database table instead of hardcoded strings.

### Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | CHAR(36) | UUID primary key |
| `name` | String(100) | Framework name (e.g., "HIPAA") |
| `full_name` | String(255) | Full official name |
| `category` | Enum | `regulatory`, `contractual`, `voluntary` |
| `version` | String(20) | Framework version |
| `description` | Text | Brief description |
| `reference_url` | String(500) | Official documentation URL |

### Impact

- Findings linked via FK instead of free-text strings
- Compliance engine outputs reference canonical framework IDs
- Audit calendar uses FK to framework registry
- Prevents technical debt from string-matching across modules

---

## Architecture

### Service Layer Structure

```
app/services/governance/
├── __init__.py
├── compliance_engine.py      # 9 deterministic rules
├── audit_forecast_engine.py  # Pre-audit risk scoring
├── lifecycle_engine.py       # Tech stack risk classification
└── uptime_engine.py          # SLA gap analysis
```

### API Routes

All governance endpoints are registered under `/api/governance/`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/{org_id}/profile` | Get governance profile |
| PUT | `/{org_id}/profile` | Update governance profile |
| GET | `/{org_id}/applicable-frameworks` | Deterministic compliance mapping |
| GET | `/{org_id}/uptime-analysis` | SLA gap analysis |
| GET | `/{org_id}/audit-calendar` | List audit entries |
| POST | `/{org_id}/audit-calendar` | Create audit entry |
| PUT | `/{org_id}/audit-calendar/{id}` | Update audit entry |
| DELETE | `/{org_id}/audit-calendar/{id}` | Delete audit entry |
| GET | `/{org_id}/audit-calendar/{id}/forecast` | Pre-audit risk forecast |
| GET | `/{org_id}/tech-stack` | List tech stack with risk summary |
| POST | `/{org_id}/tech-stack` | Add tech stack item |
| PUT | `/{org_id}/tech-stack/{id}` | Update tech stack item |
| DELETE | `/{org_id}/tech-stack/{id}` | Delete tech stack item |

### Database Migration

- Migration: `0007_governance_expansion`
- Uses `batch_alter_table` for SQLite compatibility
- Fully reversible with `downgrade()`

---

## Guardrails

The following were intentionally excluded:

- Real-time CVE scanning
- Dependency scraping / live version checking
- Automated migration diffing
- Modification of deterministic scoring engine
- Assessment telemetry storage
- Any changes to the locked demo environment

AI usage remains restricted to:

- Executive summary generation
- Audit forecast narrative (LLM-enhanced, not LLM-dependent)
- Upgrade governance explanation

---

## Current Deployment Status

| Environment | Status | Notes |
|------------|--------|-------|
| Demo | Locked | NIST CSF 2.0 release (`v0.5-demo-locked` tag) |
| Staging | Active | Governance expansion modules deployed |
| Main branch | Demo-aligned | No governance features merged |
| Dev branch | Development | All governance work committed |

---

## Strategic Positioning Shift

| Aspect | Before | After |
|--------|--------|-------|
| Product Identity | AI Incident Readiness Assessment Tool | Continuous Governance & Readiness Intelligence Platform |
| Scope | Single assessment scoring | Organization-wide compliance posture |
| Compliance | Manual framework selection | Deterministic framework inference |
| Audit Support | None | Calendar + pre-audit risk forecasting |
| Lifecycle | None | Tech stack risk monitoring |
| Uptime | None | SLA gap analysis with tier governance |

---

## Test Coverage Targets

| Module | Target | Method |
|--------|--------|--------|
| Compliance Engine | 95% rule coverage | Unit tests for all 9 rules + combinations |
| Audit Forecast | 90% | Unit tests for risk level computation |
| Tech Stack Risk | 95% | Unit tests for classification matrix |
| Uptime Analysis | 100% | Unit tests for all tier/SLA combinations |
| Framework Registry | 90% | CRUD + referential integrity tests |
| Migration | 100% | Rollback + fresh bootstrap validation |
