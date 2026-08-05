# Specification Report: ResilAI Frontend Refactoring Audit

**Target Project:** ResilAI Frontend (`P:\projects\AIRS\frontend`)  
**Auditor Agent:** Spec Miner 1 (`.agents\teamwork_preview_spec_miner_survey_1`)  
**Timestamp:** 2026-08-03T20:15:00Z  

---

## Executive Summary & Audit Overview

This specification report provides the authoritative audit, feature inventory, design token taxonomy, route migration matrix, component variant hierarchy, and dual-workspace architectural blueprint for refactoring the ResilAI frontend (`P:\projects\AIRS\frontend`).

The refactoring transforms the legacy ResilAI frontend into a unified, executive-grade SaaS application featuring a **Dual Workspace Architecture**:
1. **Business Workspace**: Tailored for healthcare executives, C-suite, and clinic directors. Focuses on high-level operational readiness ("Can clinic open today?"), plain-English AI translations, 30-second time-to-insight, and key business metrics.
2. **Operations Workspace**: Tailored for IT operations, SecOps, compliance officers, and system engineers. Preserves deep technical tools (Evidence Network, Compliance Drift, Tech Stack Lifecycle, Reliability, Remediation Ledger) as drill-down views without disconnecting from the business context.
3. **Admin Workspace**: Manages organization profiles, integrations, audit calendars, user settings, and environment configurations.

---

## Detailed Requirements Breakdown (R0 – R15)

| Req ID | Requirement Title | Core Technical & Architectural Specification | Verification & Target Deliverable |
|---|---|---|---|
| **R0** | **Product Audit** | Audit every page by Target Persona, Business Question, Workspace Alignment (Business, Operations, Admin, External), Duplication Status, and ResilAI Vision Alignment. | Documented in `UI_INVENTORY.md`. |
| **R1** | **UI Component Audit** | Exhaustive classification of all existing pages, views, and components into `Keep`, `Improve`, `Merge`, or `Retire` with strict justification. | Output: `UI_INVENTORY.md`. |
| **R2** | **Dual Workspace Layout** | Single unified app with two progressive layers (Business executive summary vs. Operations technical depth) and a unified left sidebar covering Dashboard, Operations, and Administration. | Layout implementation in `src/components/layout/`. |
| **R3** | **Component Preservation & Variant Strategy** | Avoid duplicating components for different workspaces. Refactor shared components (`StatusCard`, `NorthStarHero`, `StoryActionCard`, `TrustBadge`) to support `compact`, `expanded`, and `technical` variants. Remap legacy components (`EvidenceNetwork`, `ComplianceDrift`, `TechnologyIntelligence`) into Operations. | Output: `COMPONENT_MAP.md` & component updates. |
| **R4** | **AI Translator Panel** | UI panel consuming deterministic backend contract `DailyReadinessReport` and rendering natural language explanations (Why readiness dropped, what changed, recommended actions). Uses realistic mock responses, strictly no frontend calculation. | AI Translator Panel component in Business Workspace. |
| **R5** | **Design System Standardization** | Extract spacing scales, typography scales, semantic colors, status colors, badges, shadows, border radius, animations, and icons into reusable design tokens. | Output: `DESIGN_SYSTEM.md` & `src/index.css`. |
| **R6** | **Preserve Navigation Flow** | Business and Operations must act as different zoom levels of the same application. Avoid modal app switching; support fluid inline drill-downs. | Unified Router & Navigation in `App.tsx`. |
| **R7** | **Progressive Disclosure** | 5-tier drill-down hierarchy: Clinic Ready (L1: Business) → Business Continuity (L2: Summary) → Verification (L3: Operational Check) → Connector (L4: Technical System) → Evidence (L5: Raw Telemetry & Graph). | Interactive Card expansions & SlideOvers. |
| **R8** | **Build a Real Design System** | Standardize Tailwind v4 theme, CSS variables, utility tokens, typography hierarchy, status colors, elevation tokens, and 12-column grid. | Token definitions in `DESIGN_SYSTEM.md`. |
| **R9** | **Feature Mapping** | Map Old Component → New Component → Reason → Status → Location to prevent regression or lost functionality. | Output: `FEATURE_MAP.md`. |
| **R10** | **Route Inventory** | Track Current Route → Future Route → Redirect → Deprecated → Owner Workspace to preserve all endpoints and backward compatibility. | Output: `ROUTE_MAP.md`. |
| **R11** | **State Management Audit** | Audit React Context (`AuthContext`, `DemoModeContext`, `PersonaContext`, `ThemeContext`), local state, in-memory API cache (`cache.ts`), and loading/error states. | Audit section in `FRONTEND_ARCHITECTURE.md`. |
| **R12** | **Accessibility Review** | Verify keyboard navigation, ARIA roles, focus rings, contrast ratios, responsive layouts, empty states, loading skeletons, unknown states, offline states. | Review section in `FRONTEND_ARCHITECTURE.md`. |
| **R13** | **Backend Contract Compliance** | Consume ONLY frozen `DailyReadinessReport` contract from backend (`api.ts`, `types/readiness.ts`). No frontend score calculation or derived readiness logic. | Strict schema enforcement. |
| **R14** | **Documentation Suite** | Produce 6 foundational specification documents: `UI_INVENTORY.md`, `DESIGN_SYSTEM.md`, `FEATURE_MAP.md`, `ROUTE_MAP.md`, `COMPONENT_MAP.md`, `FRONTEND_ARCHITECTURE.md`. | Documentation Suite files. |
| **R15** | **Final Deliverable** | Premium executive SaaS aesthetic, clean visual hierarchy, unified dark/light themes, zero cybersecurity-dashboard clutter. | Build validation (`npm run build`). |

---

## 1. Specification Schema: `UI_INVENTORY.md`

### Target Page & View Inventory

| Page / View | File Path | Target Persona | Business Question | Workspace | Action | Justification & Refactoring Strategy |
|---|---|---|---|---|---|---|
| **Landing** | `pages/Landing.tsx` | Prospective Buyer / Executive | What is ResilAI and how does it protect my organization? | External / Public | **Keep** | Public marketing landing page. Retain layout, ensure design token alignment. |
| **Login** | `pages/Login.tsx` | All Users | How do I securely authenticate? | External / Public | **Keep** | Authentication portal. Retain Firebase auth integration, align with new tokens. |
| **About / Security / Pilot / Status** | `pages/About.tsx`, `Security.tsx`, `Pilot.tsx`, `Status.tsx` | Buyers & Auditors | What is ResilAI's trust, security, and uptime posture? | External / Public | **Keep** | Public trust and product landing pages. |
| **Auditor View** | `pages/AuditorView.tsx` | External Auditor / Compliance | Can I verify system compliance evidence independently? | Admin / Operations | **Improve** | Dedicated read-only view for auditors. Map into Administration workspace menu. |
| **Business Today / Dashboard** | `features/readiness/TodayPage.tsx` | C-Suite / Executive | Can our clinics open and operate safely today? | Business Workspace | **Improve** | Primary executive view. Integrate NorthStarHero, AI Translator Panel, and compact StatusCards. |
| **Needs Attention / Actions** | `features/readiness/NeedsAttentionPage.tsx` | Ops Lead / Executive | What immediate risks require intervention? | Business Workspace | **Improve** | Priority actions feed. Add progressive disclosure triggers to view technical evidence. |
| **Recovery Readiness** | `features/readiness/RecoveryReadinessPage.tsx` | VP Ops / IT Director | Are backups and ransomware recovery controls verified today? | Business Workspace | **Improve** | Business continuity summary. Add drill-down to technical verification checks. |
| **Activity Feed** | `features/readiness/ActivityPage.tsx` | IT Manager / Auditor | What system changes and verifications occurred recently? | Business Workspace | **Improve** | Chronological activity log. Enhance filtering and status badges. |
| **Readiness Settings** | `features/readiness/SettingsPage.tsx` | Admin / IT Lead | How are threshold alerts and connector frequencies configured? | Admin Workspace | **Improve** | Operational settings. Move to Admin workspace section. |
| **Legacy Dashboard** | `pages/Dashboard.tsx` | IT / SecOps | What is our overall posture and threat matrix? | Operations Workspace | **Merge** | Comprehensive legacy dashboard. Merge redundant widgets into Operations overview; retire duplicate metrics. |
| **Evidence Network** | `pages/EvidenceNetwork.tsx` | Security Analyst / IT Ops | What is the complete graph of verified evidence and connectors? | Operations Workspace | **Keep** | Crucial technical visualization. Map as primary view in Operations > Evidence Network. |
| **Compliance Drift** | `pages/ComplianceDrift.tsx` | Compliance Officer / IT | Where are we drifting from regulatory standards (HIPAA, NIST)? | Operations Workspace | **Keep** | Essential technical detail page. Map into Operations > Compliance Drift. |
| **Technology Intelligence** | `pages/TechnologyIntelligence.tsx` | Systems Architect / IT | What is the lifecycle and exposure state of software/hardware? | Operations Workspace | **Keep** | High-value tech inventory page. Map into Operations > Technology Stack. |
| **Reliability Dashboard** | `pages/ReliabilityDashboard.tsx` | Infrastructure Lead | Are system components meeting uptime & SLI SLA targets? | Operations Workspace | **Keep** | Technical infrastructure monitor. Map into Operations > Reliability. |
| **Remediation Ledger** | `pages/RemediationLedger.tsx` | IT Security Lead | What remediation tickets are open, in-progress, or verified closed? | Operations Workspace | **Keep** | Action tracking ledger. Map into Operations > Remediation. |
| **AI Attack Simulation Lab** | `pages/AIAttackSimulationLab.tsx` | Red Team / SecOps | How does the system behave under simulated attack scenarios? | Operations Workspace | **Improve** | Advanced simulation lab. Map into Operations > AI Simulation. |
| **Readiness Timeline / Board Story / Decision Engine / Business Units** | `pages/ReadinessTimeline.tsx`, `BoardStory.tsx`, `DecisionEngine.tsx`, `BusinessUnits.tsx` | Executive / Board | How has readiness trended over time and across business units? | Business Workspace | **Merge / Improve** | Executive reporting features. Retain as tabbed sub-views under Business Workspace Reports. |
| **Organizations & New Org** | `pages/Organizations.tsx`, `NewOrg.tsx` | System Admin | Which organization context am I managing? | Admin Workspace | **Improve** | Org selection and provisioning. Map to Admin > Organizations. |
| **Assessments & Quick/New Assessment** | `pages/Assessments.tsx`, `QuickAssessment.tsx`, `NewAssessment.tsx` | Auditor / IT Lead | How do I run or review formal readiness assessments? | Operations Workspace | **Improve** | Assessment workflow. Map to Operations > Assessments. |
| **Results & Reports** | `pages/Results.tsx`, `Reports.tsx` | Executive / Auditor | What are the generated audit reports and exportable artifacts? | Business / Admin | **Improve** | Reporting tab. Map to Business Workspace > Board Reports. |
| **Clinic Prototype Pages (`pages/clinic/*`)** | `pages/clinic/Home.tsx`, `Onboarding.tsx`, etc. | Clinic Admin | Orphaned prototype pages for clinic layout. | Legacy Prototype | **Retire** | Legacy isolated views superseded by `features/readiness`. Safely retire. |

---

## 2. Specification Schema: `DESIGN_SYSTEM.md`

### Design Tokens Taxonomy

#### A. Spacing Scale (4px / 8px Base Grid)
```css
/* Standard spacing scale for layout alignment */
--spacing-1:  4px;   /* tight-gap: micro spacing between inline tags/badges */
--spacing-2:  8px;   /* inline-gap: standard gap between icons and labels */
--spacing-3: 12px;   /* compact padding inside small buttons/cards */
--spacing-4: 16px;   /* card-gap: default internal padding & card grid gap */
--spacing-6: 24px;   /* section-gap: spacing between dashboard widget sections */
--spacing-8: 32px;   /* container padding for desktop viewports */
--spacing-12: 48px;  /* major vertical page section spacing */
--spacing-16: 64px;  /* hero header vertical spacing */
```

#### B. Typography Scale (Inter Font Family)
```css
--font-family-sans: 'Inter', ui-sans-serif, system-ui, sans-serif;

/* Classes & Token Specs */
.text-display  { font-size: 2.25rem;  /* 36px */ line-height: 2.5rem;  /* 40px */ font-weight: 700; letter-spacing: -0.025em; }
.text-headline { font-size: 1.5rem;   /* 24px */ line-height: 2.0rem;  /* 32px */ font-weight: 700; letter-spacing: -0.015em; }
.text-title    { font-size: 1.125rem; /* 18px */ line-height: 1.75rem; /* 28px */ font-weight: 600; }
.text-body     { font-size: 0.875rem; /* 14px */ line-height: 1.25rem; /* 20px */ font-weight: 400; }
.text-caption  { font-size: 0.75rem;  /* 12px */ line-height: 1.0rem;  /* 16px */ font-weight: 500; letter-spacing: 0.02em; }
.text-overline { font-size: 0.625rem; /* 10px */ line-height: 0.75rem; /* 12px */ font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; }
```

#### C. Color Palette & Semantic Status Mapping
- **Primary Brand (Emerald Green)**: `--color-primary-500: #00C853`, `--color-primary-600: #00b047`, `--color-primary-50: #e5faf0`
- **Secondary Accent (Titanium Blue)**: `--color-blue-500: #2979FF`, `--color-blue-600: #1c64e6`, `--color-blue-50: #ecf3ff`
- **Surface & Background (Deep Charcoal Dark Theme / Off-White Light Theme)**:
  - Light Body Bg: `#f8fafc` | Light Card Bg: `#ffffff` | Light Border: `#e2e8f0`
  - Dark Body Bg: `#1A1A1A` | Dark Card Bg: `#242424` | Dark Canvas: `#121212` | Dark Border: `#2d2d2d`
- **Status Colors & Badges**:
  - `safe_to_open` / Success: Green (`bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800`)
  - `action_needed` / Warning: Amber (`bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800`)
  - `critical_risk` / Danger: Red (`bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-400 dark:border-red-800`)
  - `unknown` / Slate: Gray (`bg-slate-50 text-slate-700 border-slate-200 dark:bg-slate-900 dark:text-slate-400 dark:border-slate-800`)

#### D. Elevation, Shadows & Border Radius
- **Border Radius Scale**: `sm`: 4px, `md`: 6px, `lg`: 8px, `xl`: 12px, `2xl`: 16px, `full`: 9999px.
- **Shadow Scale**:
  - `--shadow-card`: `0 1px 3px 0 rgba(0,0,0,0.1), 0 1px 2px 0 rgba(0,0,0,0.06)`
  - `--shadow-soft`: `0 2px 15px -3px rgba(0,0,0,0.07), 0 10px 20px -2px rgba(0,0,0,0.04)`
  - `--shadow-medium`: `0 4px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)`

---

## 3. Specification Schema: `FEATURE_MAP.md`

| Old Component / Feature | New Component / Feature | Reason | Status | Target Location |
|---|---|---|---|---|
| `pages/Dashboard.tsx` | Business & Operations Dashboards | Split executive summary metrics from technical graph views. | Refactored | Business (`/readiness`) & Ops (`/dashboard/operations`) |
| `pages/EvidenceNetwork.tsx` | `EvidenceNetwork.tsx` | High value graph view preserved intact for deep evidence analysis. | Preserved | Operations (`/dashboard/evidence-network`) |
| `pages/ComplianceDrift.tsx` | `ComplianceDrift.tsx` | Regulatory tracking preserved for compliance officers. | Preserved | Operations (`/dashboard/compliance-drift`) |
| `pages/TechnologyIntelligence.tsx` | `TechnologyIntelligence.tsx` | Software/Hardware lifecycle and vulnerability monitor preserved. | Preserved | Operations (`/dashboard/tech-stack`) |
| `pages/ReliabilityDashboard.tsx` | `ReliabilityDashboard.tsx` | SLA/SLI system reliability monitor preserved for Ops. | Preserved | Operations (`/dashboard/reliability`) |
| `pages/RemediationLedger.tsx` | `RemediationLedger.tsx` | Action tracking ledger preserved for IT workflow. | Preserved | Operations (`/dashboard/remediation`) |
| `components/readiness/NorthStarHero.tsx` | `NorthStarHero.tsx` (Refactored) | Refactored to support `compact` and `expanded` status display. | Refactored | Business (`/readiness`) |
| `components/readiness/StoryActionCard.tsx` | `StoryActionCard.tsx` (Refactored) | Refactored to support `compact`, `expanded`, and `technical` drill-down. | Refactored | Business & Operations Workspaces |
| `pages/clinic/*` | Retired Prototype Pages | Replaced by unified `features/readiness` architecture. | Deprecated | Retired |

---

## 4. Specification Schema: `ROUTE_MAP.md`

| Current Route | Future Route | Redirect Rule | Deprecated? | Owner Workspace | Target Persona |
|---|---|---|---|---|---|
| `/` | `/` | Redirect to `/readiness` if authenticated | No | External / Common | Executive / Visitor |
| `/login` | `/login` | None | No | External / Common | All Users |
| `/readiness` | `/readiness` | Primary Business Workspace Index | No | Business Workspace | C-Suite / Executive |
| `/readiness/actions` | `/readiness/actions` | Business Needs Attention feed | No | Business Workspace | VP Ops / Executive |
| `/readiness/continuity` | `/readiness/continuity` | Business Recovery Readiness view | No | Business Workspace | Executive / IT Lead |
| `/readiness/activity` | `/readiness/activity` | Business Activity Timeline | No | Business Workspace | IT Ops / Auditor |
| `/dashboard` | `/dashboard/operations` | Redirect `/dashboard` -> `/readiness` | Legacy | Operations Workspace | IT Ops / SecOps |
| `/dashboard/evidence-network` | `/dashboard/operations/evidence` | Canonical route for Evidence Network | No | Operations Workspace | Security Analyst |
| `/dashboard/compliance-drift` | `/dashboard/operations/compliance` | Canonical route for Compliance Drift | No | Operations Workspace | Compliance Officer |
| `/dashboard/tech-stack` | `/dashboard/operations/technology` | Canonical route for Tech Intelligence | No | Operations Workspace | Infrastructure Lead |
| `/dashboard/reliability` | `/dashboard/operations/reliability` | Canonical route for Reliability | No | Operations Workspace | SRE / IT Ops |
| `/dashboard/remediation` | `/dashboard/operations/remediation` | Canonical route for Remediation | No | Operations Workspace | IT Security Lead |
| `/dashboard/settings` | `/dashboard/admin/settings` | Redirect `/settings` -> Admin settings | No | Admin Workspace | System Admin |
| `/docs/*` | `/docs/*` | Public Documentation Portal | No | External / Docs | All Users |
| `/integrations` | `/dashboard/evidence-network` | Hard redirect `301` to Evidence Network | Yes | Operations Workspace | Security Analyst |
| `/assessment/new` | `/dashboard/assessment/new` | Hard redirect `301` | Yes | Operations Workspace | IT Auditor |

---

## 5. Specification Schema: `COMPONENT_MAP.md`

### Component Hierarchy Tree
```
App (AuthProvider, DemoModeProvider, PersonaProvider, ToastProvider)
 ├── External Portal Layout (Landing, Login, About, Security, Pilot, Status, Docs Layout)
 └── Authenticated Shell Layout (Unified Sidebar + Environment Banner + Header)
      ├── Business Workspace Layout (/readiness/*)
      │    ├── TodayPage (Executive Hero, AI Translator Panel, Top Blockers, Quick Stats)
      │    ├── NeedsAttentionPage (Action Cards Feed with Progressive Disclosure)
      │    ├── RecoveryReadinessPage (Business Continuity Status & Drill-Down)
      │    └── ActivityPage (Verified Timeline & Event Filter)
      ├── Operations Workspace Layout (/dashboard/operations/*)
      │    ├── EvidenceNetwork (Graph canvas, node metadata, connector topology)
      │    ├── ComplianceDrift (Control drift, HIPAA/NIST frameworks, violation drawer)
      │    ├── TechnologyIntelligence (Asset lifecycle, exposure monitor, software tab)
      │    ├── ReliabilityDashboard (SLO/SLI metrics, incident logs, system uptime)
      │    └── RemediationLedger (Open tickets, verification status, action drawer)
      └── Admin Workspace Layout (/dashboard/admin/*)
           ├── Organizations & Provisioning
           ├── Audit Calendar & Auditor Access
           └── System & Threshold Settings
```

### Component Variant Specification Matrix

| Component Name | `compact` Variant Spec | `expanded` Variant Spec | `technical` Variant Spec |
|---|---|---|---|
| `StatusCard` | Single-line badge + status indicator (e.g. "Safe to Open: 98%"). | Executive summary card with metric change narrative and AI translation prompt. | Detailed operational state breakdown, raw response timestamps, and verification details. |
| `StoryActionCard` | Priority badge + action title + 1-click resolve button. | Full story narrative ("Why it matters"), impacted clinic system, recommendation. | Verification payload, raw evidence JSON trigger, connector log reference. |
| `NorthStarHero` | Hero score badge + greeting ("All Systems Safe"). | Comprehensive readiness banner with continuity status and AI explanation drawer button. | System breakdown metrics grid with confidence percentages and connector status counts. |
| `TrustBadge` | Pill badge with color indicator (`safe`, `warning`, `critical`). | Badge with inline tooltip showing verification confidence % and last verified time. | Complete verification badge with inspector certificate ID and raw evidence link. |

---

## 6. Specification Schema: `FRONTEND_ARCHITECTURE.md`

### A. Dual Workspace Architecture & Navigation
The application features a single React SPA (`react-router-dom` v7) with a unified, persistent navigation sidebar containing three primary collapsible menu groups:
1. **Business Workspace**: High-level executive summaryviews (Today, Needs Attention, Recovery Readiness, Board Reports). Optimized for <30-second time to insight.
2. **Operations Workspace**: Technical operational view (Evidence Network, Compliance Drift, Tech Stack, Reliability, Remediation Ledger, AI Simulation).
3. **Administration**: Workspace settings, organization enrichment, audit calendar, auditor access management.

### B. Progressive Disclosure Flow
Progressive disclosure allows non-technical executives to view high-level readiness while enabling IT engineers to drill down to raw evidence seamlessly:
```
[Level 1: Clinic Ready Status] -> Executive NorthStar Banner
       │ (Click "Why is readiness amber?")
       ▼
[Level 2: Business Continuity Summary] -> StoryActionCard (Expanded)
       │ (Click "View System Verification")
       ▼
[Level 3: Operational Check] -> Verification Summary Drawer
       │ (Click "Inspect Connector Health")
       ▼
[Level 4: Technical Connector State] -> Tech Stack Lifecycle & Activity Log
       │ (Click "Trace Evidence Graph")
       ▼
[Level 5: Raw Evidence Graph] -> EvidenceNetwork Graph Node & JSON Payload
```

### C. AI Translator Panel Architecture
- **Purpose**: Translates complex, multi-system deterministic readiness data (`DailyReadinessReport`) into clear, human-readable explanations.
- **Contract**: Consumes strictly the frozen `DailyReadinessReport` object (`types/readiness.ts`).
- **Functionality**: Answers 3 core questions:
  1. *Why did readiness change today?* (Narrative derived from `trend.narrative` and `timeline`).
  2. *What is the business impact?* (Derived from `business_continuity.blockers` and `failed_checks`).
  3. *What specific actions should be taken?* (Derived from `immediate_actions`).
- **Constraint Compliance**: Zero client-side computation of scores. Pure presentation layer.

### D. State Management Audit
- **Context API**: `AuthContext` (Firebase auth token provider), `DemoModeContext` (Staging vs. Demo mode toggle), `PersonaContext` (Executive vs. IT view preference), `ThemeContext` (Dark/Light mode).
- **In-Memory Cache**: `cache.ts` (`apiCache` singleton using TTL-based cache for list/summary endpoints).
- **API Client**: `api.ts` handles centralized fetches, token injection, and automatic `401` navigation.

### E. Accessibility & Quality Audit
- **Keyboard Nav**: Focus rings (`focus-ring`), escape key traps on drawers (`SlideOver.tsx`, `HowWeKnowDrawer.tsx`).
- **Color Contrast**: Compliant text contrast across Light (`#f8fafc`) and Deep Charcoal (`#1A1A1A`) dark mode.
- **Empty / Loading / Error States**: Handled via `Skeleton.tsx`, `EmptyState.tsx`, and `ErrorBoundary.tsx`.

---

## Features Discovered & Edge Cases

### Features Discovered
| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|---|---|---|---|---|---|---|
| 1 | Architecture | Dual Workspace Navigation | Dual layer (Business vs Operations) with unified sidebar. | User persona / route selection | Filtered navigation menu | Fallback to default route | `App.tsx`, `DashboardLayout.tsx` |
| 2 | Component | AI Translator Panel | Natural language explanation of deterministic readiness. | `DailyReadinessReport` backend object | Natural language explanation UI | Displays fallback mock explanation | `features/readiness/TodayPage.tsx` |
| 3 | State | In-Memory API Cache | TTL-based caching for list and summary endpoints. | Cache key & TTL ms | Cached data or fetch promise | Invalidate on mutation | `src/cache.ts` |
| 4 | Component | Evidence Network Graph | Interactive graph representation of evidence nodes. | System evidence nodes | D3/React graph canvas | Empty graph state with banner | `pages/EvidenceNetwork.tsx` |
| 5 | Component | Compliance Drift Tracker | Real-time regulatory framework drift monitoring. | Framework compliance rules | Drift percentage & violation list | Empty state message | `pages/ComplianceDrift.tsx` |

### Edge Cases
| # | Feature | Input | Observed Behavior |
|---|---|---|---|
| 1 | API Base URL Missing | `VITE_API_BASE_URL` unset in env | `ApiConfigBanner` displays warning banner at top of viewport; API falls back to `http://localhost:8000`. |
| 2 | Authenticated Session Expiration | API returns `401 Unauthorized` | `setUnauthorizedHandler` in `api.ts` catches response and triggers router redirect to `/login`. |
| 3 | Unknown Backend Readiness State | `status: 'unknown'` in `DailyReadinessReport` | UI renders gray status badge and triggers `UnknownItem` list drawer. |
| 4 | Environment Domain Redirect | Accessing default Firebase domain (`*.web.app`) | App automatically replaces window location with custom domain (`resilai.org` or `staging.resilai.org`). |

---
*Report compiled by Spec Miner 1 for the ResilAI Frontend Refactoring Project.*
