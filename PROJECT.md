# Project: ResilAI Authenticated Product Experience Refactoring

## Architecture
ResilAI is an executive-first healthcare incident readiness platform. The authenticated product experience is built on:
- **Core Narrative Flow**: Answers *"Are we ready for today?"* via 5 progressive stages:
  1. *Current Readiness* (Macro status & Readiness Score Arc)
  2. *Why* (Overnight verification summary & delta explanation)
  3. *What Needs Attention* (Triage of active gaps & incident risks)
  4. *What Should We Do* (Executive / IT recommended actions & 1-click remediation)
  5. *How Can We Prove It* (Verifiable evidence links, connector sync status, SHA-256 cryptographic provenance)
- **4-Tier Progressive Disclosure Model**:
  1. *Tier 1 (Executive Explanation)*: Plain-English business summary suitable for Managing Partners (<2 min/day).
  2. *Tier 2 (Business Impact)*: Operational consequences, patient appointment disruption risk, liability exposure.
  3. *Tier 3 (Technical Evidence)*: Inspected system controls, monitored telemetry endpoints, raw configuration payloads.
  4. *Tier 4 (Cryptographic Provenance)*: SHA-256 evidence hash, connector origin, exact UTC execution timestamp.
- **Backend Intelligence Only**: No client-side LLM calls, synthetic intelligence, or frontend score math. All metrics, executive explanations, and reports are served by backend deterministic engines (`ReadinessEngine`, `ExplainabilityEngine`, Report APIs).
- **Stitch Design System Tokens (`5374718910617390721`)**: Obsidian canvas `#0b1326`, surface container hierarchy `#131b2e` to `#2d3449`, text `#dae2fd`/`#bbcabf`, accents `#10B981` (Ready Emerald), `#F59E0B` (Drift Amber), `#EF4444` (Critical Red), Lucide icons.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| F1 | Narrative Dashboard Hierarchy | 5-stage narrative layout on `TodayPage.tsx`: Readiness → Why → Needs Attention → Actions → Provenance | M1 | R1, Survey 1 |
| F2 | Stitch Design Tokens & Visual Hierarchy | Apply obsidian/emerald/amber Stitch palette, eliminate nested card borders & noise | M1 | R1, Survey 1 |
| F3 | 4-Tier Progressive Disclosure Cards & AIDrawer | Unified 4-tier model (Executive -> Impact -> Technical -> SHA-256) across cards and `AIDrawer.tsx` | M1 | R2, Survey 1 |
| F4 | 6-Step Guided Onboarding Workflow | Persistent, resumable, skippable 6-step walkthrough (Readiness, Connect, Verify, Needs Attention, Recovery, Board Report) | M2 | R3, Survey 2 |
| F5 | Persistent Getting Started Triggers | Header & sidebar controls to re-launch Getting Started at any time; per-org completion persistence | M2 | R3, Survey 2 |
| F6 | Contextual Demo Mode Guidance & Disclaimers | Prominent "DEMO ENVIRONMENT (SIMULATED DATA)" & staged contextual guidance across Today, Triage, Recovery, Docs, Governance | M2 | R4, Survey 2 |
| F7 | "Explain for Leadership" Backend Integration | Dual Executive vs Technical presentation consuming backend `/api/v1/clinic/{org_id}/explain` & `DailyReadinessReport` without client LLMs | M3 | R5, Survey 2 |
| F8 | Report Center Backend Integration & History | Connect Reports to `/api/v1/reports`, `/api/v1/reports/generate`, `/api/v1/reports/{id}/download`, live progress, timestamps | M4 | R6, Survey 2 |
| F9 | Documents Vault Modernization | Transform Documents into Evidence-Backed Readiness & Audit Vault matching Stitch templates | M5 | R7, Survey 2 |
| F10 | Governance Framework Alignment Framing | Frame frameworks (NIST CSF 2.0, NIST AI RMF, CIS, SOC 2, ISO 27001, HIPAA) as "Readiness evidence aligned to..." | M5 | R7, Survey 2 |
| F11 | Purge Legacy Phrasing | Remove legacy V1 "five domains" / questionnaire assessment phrasing across all components | M5 | R7, Survey 2 |
| F12 | Design Consistency & Icon Standardization | Migrate all Material Symbols font icons to `lucide-react`, unify badge styling | M6 | R8, Survey 3 |
| F13 | Mobile Drawer & Responsive Layout (375px) | Fix `AppSidebar.tsx` hidden class in mobile drawer, ensure horizontal table scroll wrappers | M6 | R8, Survey 3 |
| F14 | WCAG AA Accessibility & Motion Support | Visible focus rings, ARIA labels on icon buttons, `@media (prefers-reduced-motion)` support | M6 | R8, Survey 3 |
| F15 | Comprehensive 4-Tier E2E Test Suite | 4-tier opaque-box test suite (Tiers 1-4) + Tier 5 adversarial hardening (124 passed tests) | E2E/M7 | R8, Survey 3 |

---

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | E2E Testing Track Infrastructure & Test Suites | Setup Vitest test runner, test utilities, Tier 1-4 test suites, publish `TEST_READY.md` | none | DONE |
| M1 | Visual Identity & Today/Dashboard Narrative Overhaul | Refactor `TodayPage.tsx`, `StatusCard.tsx`, `AIDrawer.tsx`, Stitch styling (F1, F2, F3) | none | DONE |
| M2 | Guided 6-Step Onboarding & Contextual Demo Guidance | 6-step onboarding wizard, persistent launcher, demo banners across primary pages (F4, F5, F6) | none | DONE |
| M3 | Leadership Simplified Explanation & Dual Presentation | "Explain for leadership" modals/drawers consuming backend contracts (F7) | M1 | DONE |
| M4 | Report Center Backend Integration & History Management | Wire Reports page to backend report endpoints, generation progress & history (F8) | none | DONE |
| M5 | Documents Vault & Governance Modernization | Transform Documents into Audit Vault, modernize Governance with framework alignment framing, purge 5-domain copy (F9, F10, F11) | none | DONE |
| M6 | Design Consistency, A11y & Mobile Responsiveness | Fix mobile sidebar drawer, migrate Lucide icons, WCAG AA ARIA labels & focus, 375px support (F12, F13, F14) | none | DONE |
| M7 | Final Integration, 100% E2E Pass & Coverage Hardening | Run all test tiers (Tiers 1-4), adversarial hardening, verify TypeScript build (F15) | E2E, M1-M6 | DONE |

---

## Interface Contracts

### 1. `DailyReadinessReport` & `ExecutiveExplanation` Contract (`src/types/readiness.ts` & `src/api.ts`)
```typescript
export interface ExecutiveExplanation {
  status: 'ready' | 'attention_required' | 'critical' | 'unknown';
  business_label: string;
  technical_label: string;
  what_it_means: string;
  why_it_matters: string;
  what_to_do_next: string;
  evidence_state: string;
  last_verified_at: string;
  evidence_hash?: string;
  source_connector?: string;
}

export interface ReadinessCheckItem {
  id: string;
  title: string;
  severity: 'critical' | 'warning' | 'info' | 'verified';
  category: 'data_recovery' | 'access_control' | 'device_security' | 'threat_monitoring';
  explanation: ExecutiveExplanation;
  raw_telemetry?: Record<string, any>;
  source_connector: string;
  last_verified_at: string;
  evidence_hash: string;
}
```

### 2. Onboarding Workflow Contract (`src/types/onboarding.ts`)
```typescript
export type OnboardingStepNumber = 1 | 2 | 3 | 4 | 5 | 6;

export interface OnboardingStepState {
  currentStep: OnboardingStepNumber;
  completedSteps: OnboardingStepNumber[];
  isDismissed: boolean;
  isCompleted: boolean;
  mode: 'demo' | 'real';
}
```

### 3. Report Management Contract (`src/types/reports.ts`)
```typescript
export interface BackendReport {
  id: string;
  title: string;
  type: 'board_story' | 'monthly_ops' | 'hipaa_audit' | 'technical_telemetry';
  format: 'pdf' | 'json' | 'csv';
  status: 'ready' | 'generating' | 'failed';
  generated_at: string;
  size_bytes?: number;
  organization_id: string;
  download_url: string;
  summary?: string;
}
```

---

## Code Layout
```
frontend/
├── src/
│   ├── api.ts                               # Centralized API client & mock fallbacks
│   ├── App.tsx                              # Application routes (includes /reports)
│   ├── components/
│   │   ├── common/                          # ContextualDemoBanner, SimulatedTelemetryBanner
│   │   ├── layout/                          # AppLayout, AppSidebar (mobile drawer support), ReadinessHeader
│   │   ├── onboarding/                      # 6-Step Getting Started modal, stepper & step views
│   │   ├── readiness/                       # TodayPage sections, AIDrawer, StatusCard, Arc gauges
│   │   ├── evidence/                        # ExecutiveExplanation 4-tier cards, Provenance widgets
│   │   └── ui/                              # Atoms (Badge, Button, Card, Modal, Input)
│   ├── features/
│   │   ├── readiness/TodayPage.tsx          # 5-Stage narrative Morning Brief dashboard
│   │   ├── triage/NeedsAttentionPage.tsx    # Active incident triage & remediation
│   │   └── recovery/RecoveryReadinessPage.tsx # Continuity & backup immutability
│   ├── pages/
│   │   ├── Documents.tsx                    # Evidence-Backed Readiness & Audit Vault
│   │   ├── Governance.tsx                   # Framework Alignment Posture & Non-Certification Framing
│   │   ├── Reports.tsx                      # Report Center & History Management
│   │   └── Onboarding.tsx                   # Guided Getting Started page
│   ├── lib/
│   │   └── design-tokens.ts                 # Stitch color & typography tokens
│   └── test/
│       ├── setup.ts                         # Vitest DOM polyfills & matchers
│       ├── tier1/tier1-feature-coverage.test.tsx # Tier 1 Feature Tests (40 tests)
│       ├── tier2/tier2-boundary-corner.test.tsx  # Tier 2 Boundary Tests (40 tests)
│       ├── tier2/tier2-onboarding.test.tsx       # Tier 2 Onboarding Tests (13 tests)
│       ├── tier3/tier3-cross-feature.test.tsx    # Tier 3 Cross-Feature Tests (12 tests)
│       ├── tier4/tier4-real-world-scenarios.test.tsx # Tier 4 Scenarios (5 tests)
│       ├── tier4/tier4-report-center.test.tsx    # Tier 4 Report Center Tests (5 tests)
│       └── challenger-adversarial-stress.test.tsx # Challenger Stress Tests (9 tests)
```
