# Project: ResilAI Multi-Vertical Positioning Experiment (Staging Only)

## Architecture
- **Multi-Vertical Architecture**:
  - Frontend detects vertical context via `VerticalContext` supporting:
    1. Subdomain detection (`healthcare.staging.resilai.org`, `legal.staging.resilai.org`, `staging.resilai.org`).
    2. URL path fallback (`/healthcare`, `/legal`, `/`).
    3. URL query parameter fallback (`?vertical=healthcare`, `?vertical=legal`, `?vertical=general`).
  - Synchronous static fallback in `frontend/src/config/verticals.ts` ensures resilience even if backend public config API is unavailable.
- **Backend Public Config**:
  - `GET /api/public/product-config` exposes display metadata, industry labels, headlines, questions, focus areas, and demo org IDs.
- **Architectural Invariant (Shared Deterministic Engine)**:
  - Mathematical readiness calculation remains strictly centralized in `app/services/scoring.py` (`calculate_readiness_delta`).
  - Connectors (`SplunkConnector`, `EvidenceAdapter`) and control registries remain shared.
  - Zero duplicate scoring engines. Only narrative translations (`app/services/explanation.py`) and demo organization personas adapt to verticals.
- **Simulated Demo Sandbox**:
  - 3 Distinct Demo Personas:
    1. General: Acme Technologies (`demo-acme-technologies`, Alex Chen - VP Eng, Cloud/SaaS/Identity).
    2. Healthcare: Northstar Family Health (`demo-northstar-health`, Dr. Evelyn Reed - CMO, EHR/Veeam/Workstations).
    3. Legal: Northstar & Cole LLP (`demo-northstar-cole`, Marcus Cole - Managing Partner, NetDocuments/Elite 3E/Partner Laptops).
  - Unlocked organization switcher dropdown in `ReadinessHeader.tsx` by providing all 3 demo tenants when in demo mode.
  - Hardened mutation guard in `api.ts:141` (`|| localStorage.getItem('resilai_demo_user') === 'true'`) to guarantee 100% read-only sandbox isolation.
  - Global amber sticky banner (`bg-amber-500/10 border-b border-amber-500/20 text-amber-900 dark:text-amber-200`) across all demo routes in `AppLayout.tsx`.
- **Staging Deployment Isolation**:
  - Firebase Hosting targets `resilai-staging` and `staging` serving `frontend/dist-staging` (`staging.resilai.org`).
  - Cloud Run target `airs-api-staging`.
  - Zero modifications or deployments to production (`resilai-marketing`, `resilai.org`, `airs-api`).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Subdomain Vertical Detection | Parse hostname for `healthcare.staging.resilai.org`, `legal.staging.resilai.org`, `staging.resilai.org` | M1 | survey 1 & 3 |
| 2 | Path & Query Vertical Fallback | Route `/healthcare`, `/legal`, and query params `?vertical=healthcare`, `?vertical=legal` | M1 | survey 1 |
| 3 | VerticalContext Provider & Hook | Centralized state provider & `useVertical()` hook with TypeScript interfaces | M1 | survey 1 |
| 4 | Public Product Config Endpoint | `GET /api/public/product-config` returning display metadata and static frontend fallback | M1 | survey 3 |
| 5 | General Platform Landing Experience | Universal positioning headline, question, focus areas (Cloud, SaaS, Identity) | M2 | survey 1 |
| 6 | Healthcare Landing Experience | Healthcare positioning headline, ransomware question, focus areas (EHR, Veeam, M365) | M2 | survey 1 |
| 7 | Legal Landing Experience | Law firm positioning headline, client data question, focus areas (DMS, partner access, ABA) | M2 | survey 1 |
| 8 | Navbar & CTA Vertical Routing | Navigation links and demo CTAs preserve vertical context across public site | M2 | survey 1 |
| 9 | Multi-Vertical Demo Persona Registry | `demoPersonas.ts` defining Acme Technologies, Northstar Family Health, Northstar & Cole LLP | M3 | survey 2 |
| 10 | Demo Organization Switcher Activation | Return all 3 demo tenants in `useActiveOrg.ts` to unlock org switcher in `ReadinessHeader.tsx` | M3 | survey 2 |
| 11 | Demo Auth & Report Resolution | Synchronize user persona and resolve vertical-specific `DailyReadinessReport` in demo mode | M3 | survey 2 |
| 12 | Demo Sandbox Mutation Guard Hardening | Check `resilai_demo_user` in `api.ts:141` to prevent demo mutation requests | M3 | survey 2 |
| 13 | Global Amber Demo Banner | Persistent sticky amber demo banner across all demo routes in `AppLayout.tsx` & parameterized contextual banner | M3 | survey 2 |
| 14 | Frontend Test Suite Harmonization | Update banner matchers in `SimulatedTelemetryBanner` and mock timing so `npm test` achieves 100% pass | M3 | survey 1 & 2 |
| 15 | Scoring Engine Invariant Verification | Verify `scoring.py`, `calculate_readiness_delta`, AST LLM isolation, zero duplicate engines | M4 | survey 3 |
| 16 | Backend Pytest Harness Cleanliness | Update `pytest.ini:norecursedirs` for `scratch/` and verify pytest passing with 0 regressions | M4 | survey 3 |
| 17 | Staging-Only Build Verification | Run `tsc -b && vite build --mode staging` cleanly outputting `dist-staging/` | M5 | survey 1 & 3 |
| 18 | Production Isolation Verification | Verify Firebase `marketing` and Cloud Run `airs-api` production targets remain untouched | M5 | survey 3 |
| 19 | E2E Test Suite (Tiers 1-4) | Comprehensive opaque-box test suite verifying all features across all tiers | M6 | testing track |
| 20 | Adversarial Coverage Hardening (Tier 5) | White-box stress testing, gap analysis, and adversarial test cases | M6 | project pattern |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Host- and Route-Aware Vertical Architecture | `VerticalContext`, subdomain/path/query detection, `GET /api/public/product-config`, static fallback | Survey | DONE (types, config, context, backend public endpoint) |
| M2 | Distinct Landing & Positioning Experiences | General, Healthcare, Legal headlines, questions, focus areas in `Landing.tsx` & `PublicNavbar.tsx` | M1 | DONE (copy, positioning, non-looping router synchronization) |
| M3 | Vertical-Aware Demo Sandbox, Personas & Banners | `demoPersonas.ts`, `useActiveOrg`, `AuthContext`, `api.ts` mutation guard, global amber banner, vitest baseline fix | M1, M2 | IN_PROGRESS |
| M4 | Shared Deterministic Engine Invariant & Backend Tests | AST LLM isolation tests, shared scoring audit, backend test regression verification | none | PLANNED |
| M5 | Staging-Only Build, Deployment Isolation & Verification | `dist-staging` build, Firebase staging targets verification, production isolation audit | M1, M2, M3, M4 | PLANNED |
| M6 | E2E Test Suite Pass & Adversarial Hardening | Pass 100% of E2E tests (Tiers 1-4), then execute Phase 2 adversarial hardening (Tier 5) | M1..M5, TEST_READY | PLANNED |

## Interface Contracts
### `frontend/src/types/vertical.ts` ↔ Components & Hooks
```typescript
export type VerticalKey = 'general' | 'healthcare' | 'legal';

export interface VerticalConfig {
  key: VerticalKey;
  displayName: string;
  industryLabel: string;
  tagline: string;
  headline: string;
  coreQuestion: string;
  focusAreas: string[];
  demoOrgId: string;
  demoOrgName: string;
  demoPersonaName: string;
  demoPersonaRole: string;
  criticalSystems: string[];
}
```

### `GET /api/public/product-config` Contract
- **Method**: `GET`
- **Path**: `/api/public/product-config`
- **Query Params**: `vertical` (optional: `general` | `healthcare` | `legal`)
- **Headers**: `X-ResilAI-Vertical` (optional)
- **Response**:
```json
{
  "vertical_key": "healthcare",
  "display_name": "ResilAI Healthcare",
  "industry_label": "Healthcare",
  "headline": "Incident readiness for healthcare organizations",
  "core_question": "If ransomware hits your clinic tomorrow morning, can you keep operating and prove you're ready?",
  "focus_areas": [
    "Ransomware resilience",
    "EHR clinical operations continuity",
    "Microsoft 365 & Entra ID protection",
    "Veeam immutable backup integrity",
    "Recovery readiness SLAs",
    "Executive board visibility"
  ],
  "demo_org_id": "demo-northstar-health",
  "demo_org_name": "Northstar Family Health"
}
```

### Code Layout
- `frontend/src/types/vertical.ts` — Vertical TypeScript types
- `frontend/src/config/verticals.ts` — Synchronous static vertical configuration registry
- `frontend/src/contexts/VerticalContext.tsx` — Vertical context provider, subdomain & route detector, `useVertical()` hook
- `frontend/src/data/demoPersonas.ts` — Vertical demo personas (Acme Technologies, Northstar Family Health, Northstar & Cole LLP)
- `frontend/src/hooks/useActiveOrg.ts` — Active organization hook supporting multi-tenant demo switcher
- `frontend/src/components/layout/AppLayout.tsx` — Global persistent amber demo banner
- `frontend/src/components/common/ContextualDemoBanner.tsx` — Parameterized contextual demo banner
- `frontend/src/pages/Landing.tsx` — Dynamic multi-vertical landing page
- `frontend/src/components/layout/PublicNavbar.tsx` — Public navigation with vertical context preservation
- `frontend/src/api.ts` — Demo mutation guard hardening & vertical-specific readiness report routing
- `app/api/public.py` (or `app/api/v1/config.py`) — `GET /api/public/product-config`
- `tests/` — Scoring delta, LLM isolation, backend contract tests
- `frontend/src/test/` — Vitest unit & integration tests
