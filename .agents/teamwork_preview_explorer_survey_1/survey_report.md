# ResilAI Frontend Initial Codebase & UI Survey Report

**Project**: ResilAI Frontend Dual Workspace Refactoring  
**Author**: Explorer 1  
**Working Directory**: `P:\projects\AIRS\.agents\teamwork_preview_explorer_survey_1`  
**Repository Target**: `P:\projects\AIRS\frontend`  
**Date**: August 3, 2026  

---

## 1. Executive Summary & Overview

This report presents a comprehensive codebase and UI survey of the ResilAI frontend repository (`P:\projects\AIRS\frontend`). The primary objective is to lay the foundation for refactoring the existing codebase into a **Dual Workspace Architecture** (Business and Operations Workspaces) driven by progressive disclosure, maximizing component reuse, and avoiding unnecessary rewrites.

### Key Survey Discoveries
1. **Rich Feature Set & High Component Density**: The repository contains 34+ page components, 70+ reusable UI and feature components, and 2 separate product layouts (`DashboardLayout` and `ReadinessLayout`).
2. **Dual-Product Division**: Currently, `App.tsx` toggles between a legacy cybersecurity dashboard (`/dashboard/*`) and a newer readiness product (`/readiness/*`) via a feature flag (`IS_READINESS_PRODUCT = true`). Refactoring into Dual Workspaces will unify these two disparate navigation structures into a single cohesive experience.
3. **Legacy Components**: Key high-value legacy components exist and must be preserved by remapping them into the Operations workspace:
   - `EvidenceNetwork.tsx` (Telemetry, Splunk MCP, Wazuh integration, Webhooks, API keys)
   - `ComplianceDrift.tsx` (Drift timeline, signals, DIS gauge, Shadow AI monitoring)
   - `TechnologyIntelligence.tsx` (Tech stack inventory, LTS lifecycle, vulnerability exposure)
   - `ReliabilityDashboard.tsx` (Reliability Risk Index, downtime budget, SLA advisor)
   - `AIAttackSimulationLab.tsx` (Logic Firewall attack & exfiltration simulations)
   - `GovernanceProfile.tsx` & `AuditCalendar.tsx` (Enterprise compliance and audit forecasting)
   - `BoardStory.tsx` & `DecisionEngine.tsx` (10-section board narrative and remediation decision engine)
4. **Existing Persona Toggle**: `src/contexts/PersonaContext.tsx` already contains an `EXECUTIVE` vs `FORENSIC` state toggle stored in `localStorage`, which provides a perfect foundation for switching between Business and Operations levels of detail.
5. **Modern Tech Stack**: Built with React 18.3, React Router DOM 7.18, TypeScript 5.5, Vite 6.4, Tailwind CSS v4, Lucide React icons, Framer Motion animations, and Recharts.

---

## 2. Repository & Codebase Structure

```
P:\projects\AIRS\frontend\
├── package.json               # Dependencies, scripts, and overrides
├── tsconfig.json              # TypeScript root configuration
├── tsconfig.app.json          # TS config for app source
├── vite.config.ts             # Vite build config (dist-${mode} outputs)
├── tailwind.config.js         # Custom Tailwind theme overrides
├── postcss.config.js          # Tailwind PostCSS plugin
├── index.html                 # Main HTML template with theme bootstrap script
├── .deprecated_routes.txt     # List of legacy deprecated routes
├── public/                    # Static public assets (logos, favicons)
└── src/                       # Application source code
    ├── main.tsx               # Application entrypoint
    ├── App.tsx                # Top-level routing & layout switcher
    ├── index.css              # Global styles, Tailwind v4 @theme, design tokens
    ├── api.ts                 # Single-source API client & backend contract
    ├── cache.ts               # In-memory TTL API response cache
    ├── config.ts              # Global environment configuration
    ├── runtimeConfig.ts       # Dynamic backend runtime config bootstrap
    ├── types.ts               # Complete TypeScript data model definitions
    ├── assets/                # Local SVG and media assets
    ├── contexts/              # Global React Contexts (Auth, DemoMode, Persona, Theme)
    ├── hooks/                 # Custom React hooks (useTelemetryWebSocket, useMockTrustData)
    ├── lib/                   # Utility modules (firebase, userData, utils)
    ├── types/                 # Specialized domain types (readiness.ts)
    ├── components/            # UI and domain components (70+ components)
    │   ├── common/            # Shared overlay components (SlideOver)
    │   ├── dashboard/         # Dashboard widgets (EvidenceTimeline, ReadinessDrivers, TrustScore)
    │   ├── evidence/          # Evidence widgets (ConfidenceGauge)
    │   ├── layout/            # App shell layouts (DashboardLayout, DocsLayout, Footer)
    │   ├── readiness/         # Readiness widgets (NorthStarHero, ExecutiveQuestionsGrid, StoryActionCard)
    │   ├── technology/        # Tech stack tabs (Inventory, Lifecycle, Exposure, Dependencies)
    │   └── ui/                # Core UI design system components (Button, Card, Badge, Table, Tabs)
    ├── features/              # Feature modules
    │   └── readiness/         # Readiness product views (Today, Actions, Continuity, Activity, Settings)
    └── pages/                 # Full top-level page components (33 pages)
        ├── clinic/            # Legacy Healthcare vertical prototype pages (6 pages)
        └── docs/              # Documentation portal pages (5 pages)
```

---

## 3. Build Setup & Tooling Audit

### Dependencies Breakdown (`package.json`)

| Package | Version | Purpose |
|---|---|---|
| `react` / `react-dom` | `^18.3.1` | UI Library |
| `react-router-dom` | `^7.18.0` | Client-side Routing |
| `lucide-react` | `^0.562.0` | SVG Icon Library |
| `framer-motion` | `^12.39.0` | Declarative UI Animations & SlideOvers |
| `recharts` | `^3.8.1` | Data Visualization Charts (Trend, Parity) |
| `clsx` | `^2.1.1` | Dynamic Classname Utility |
| `firebase` | `^12.8.0` | Authentication & Identity |
| `@tailwindcss/postcss` | `^4.1.18` | Tailwind v4 PostCSS integration |
| `tailwindcss` | `^4.1.18` | CSS Framework |
| `typescript` | `^5.5.3` | Type Safety |
| `vite` | `^6.4.3` | Development Server & Production Bundler |

### Build Scripts

- `npm run dev`: Launches Vite dev server with HMR.
- `npm run build`: Executes `tsc -b && vite build` for default production build.
- `npm run build:staging`: Builds using `--mode staging` (outputs to `dist-staging`).
- `npm run build:demo`: Builds using `--mode demo` (outputs to `dist-demo`).
- `npm run build:production`: Builds using `--mode production` (outputs to `dist-production`).
- `npm run lint`: Runs ESLint checks across the codebase.

---

## 4. Design Tokens & Styling Architecture

The project employs a hybrid Tailwind v4 configuration combining `src/index.css` `@theme` blocks and `tailwind.config.js`.

### Color Palette (Semantic Tokens)

- **Primary / Emerald Green**: `#00C853` (`primary-500`) — Represents readiness, safety, and health.
- **Secondary / Titanium Blue**: `#2979FF` (`blue-500`, `indigo-500`) — Represents executive trust and operational analytics.
- **Dark Mode Background**: `#1A1A1A` (`slate-900`, `gray-900`) — Deep Charcoal background.
- **Dark Mode Surface**: `#242424` (`slate-800`, `gray-800`) — Card and drawer surfaces.
- **Success**: `#00e676` (`success-500`) / `#00C853` (`success-600`) — Verified checks.
- **Warning**: `#f59e0b` (`warning-500`) — Degraded connectors and warnings.
- **Danger**: `#ef4444` (`danger-500`) — Critical readiness blockers and breaches.

### Typography Scale (Inter Font Family)

- `.text-display`: `2.25rem` (36px), `700` weight, `-0.025em` tracking.
- `.text-headline`: `1.5rem` (24px), `700` weight, `-0.015em` tracking.
- `.text-title`: `1.125rem` (18px), `600` weight.
- `.text-body`: `0.875rem` (14px), `400` weight.
- `.text-caption`: `0.75rem` (12px), `500` weight, `0.02em` tracking.
- `.text-overline`: `0.625rem` (10px), `600` weight, `0.08em` tracking, uppercase.

### Spacing Scale (4px / 8px Grid Helpers)

- `.section-gap`: `24px` (8 × 3)
- `.card-gap`: `16px` (8 × 2)
- `.inline-gap`: `8px` (8 × 1)
- `.tight-gap`: `4px` (4 × 1)

### Box Shadows & Elevation

- `shadow-card`: `0 1px 3px 0 rgba(0,0,0,0.1), 0 1px 2px 0 rgba(0,0,0,0.06)`
- `shadow-soft`: `0 2px 15px -3px rgba(0,0,0,0.07), 0 10px 20px -2px rgba(0,0,0,0.04)`
- `shadow-medium`: `0 4px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)`

---

## 5. Comprehensive Page & Component Audit

### Page Inventory & Product Audit

| Page Component | Path | Current Purpose | Target Persona | Target Workspace | Duplication Status | Audit Category |
|---|---|---|---|---|---|---|
| `Landing.tsx` | `/` | Product marketing landing page | Public / Visitor | Public | Unique | **Keep** |
| `Login.tsx` | `/login` | Firebase authentication page | All Users | Auth | Unique | **Keep** |
| `About.tsx` | `/about` | Product overview and vision | Public / Visitor | Public | Unique | **Keep** |
| `Security.tsx` | `/security` | Compliance & security commitment | Public / Enterprise | Public | Unique | **Keep** |
| `Pilot.tsx` | `/pilot` | Enterprise pilot request form | Prospects | Public | Unique | **Keep** |
| `Status.tsx` | `/status` | Public system status dashboard | Public / Operations | Public | Unique | **Keep** |
| `AuditorView.tsx` | `/auditor` | Read-only external auditor view | External Auditor | Admin | Unique | **Keep** |
| `TodayPage.tsx` | `/readiness` | Executive daily readiness report | Executive / Board | **Business** | Overlaps with Dashboard.tsx | **Merge** (into Business Summary) |
| `NeedsAttentionPage.tsx` | `/readiness/actions` | Readiness action items list | Executive / Manager | **Business** | Overlaps with RemediationLedger | **Improve** (Business Actions) |
| `RecoveryReadinessPage.tsx` | `/readiness/continuity` | Ransomware & recovery verification | Executive / IT Dir | **Business** | Overlaps with ReliabilityDashboard | **Improve** (Business Continuity) |
| `ActivityPage.tsx` | `/readiness/activity` | Live verification activity feed | IT Ops / SecOps | **Operations** | Overlaps with EvidenceTimeline | **Merge** (into Operations Feed) |
| `SettingsPage.tsx` | `/readiness/settings` | Readiness engine thresholds | Admin / IT Lead | **Admin** | Overlaps with Settings.tsx | **Merge** (into Unified Settings) |
| `Dashboard.tsx` | `/dashboard` | Legacy GHI security dashboard | CISO / IT Lead | **Operations** | Dense monolitihic overview | **Merge** (Split Business/Ops) |
| `Organizations.tsx` | `/dashboard/organizations` | Organization directory | Admin | **Admin** | Unique | **Keep** |
| `NewOrg.tsx` | `/dashboard/org/new` | Organization creation modal/form | Admin | **Admin** | Unique | **Keep** |
| `Assessments.tsx` | `/dashboard/assessments` | Assessment history & list | Compliance Lead | **Operations** | Unique | **Keep** |
| `NewAssessment.tsx` | `/dashboard/assessment/new` | Full questionnaire assessment | Compliance Lead | **Operations** | Overlaps with QuickAssessment | **Merge** (Single Assessment Flow) |
| `QuickAssessment.tsx` | `/dashboard/assessment/quick` | Rapid 5-minute assessment | Manager / Auditor | **Operations** | Overlaps with NewAssessment | **Merge** (Single Assessment Flow) |
| `Results.tsx` | `/dashboard/results/:id` | Assessment results detail | Compliance / CISO | **Operations** | Unique | **Keep** |
| `Analytics.tsx` | `/dashboard/analytics` | Risk & attack path analytics | SecOps / Analyst | **Operations** | Unique | **Keep** |
| `Reports.tsx` | `/dashboard/reports` | Board report snapshot library | Executive / CISO | **Business** | Unique | **Keep** |
| `Settings.tsx` | `/dashboard/settings` | General workspace settings | Admin | **Admin** | Overlaps with ReadinessSettings | **Merge** (Unified Settings) |
| `EvidenceNetwork.tsx` | `/dashboard/evidence-network` | Telemetry & connector hub | Systems / SecOps | **Operations** | Legacy core | **Keep & Remap** |
| `ComplianceDrift.tsx` | `/dashboard/compliance-drift` | Compliance drift & Shadow AI | Compliance / Ops | **Operations** | Staging-only core | **Keep & Remap** |
| `TechnologyIntelligence.tsx` | `/dashboard/tech-stack` | Tech stack LTS & vulnerabilities | Enterprise Arch / Ops | **Operations** | Legacy core | **Keep & Remap** |
| `ReliabilityDashboard.tsx` | `/dashboard/reliability` | Downtime budget & RRI score | DevOps / Site Eng | **Operations** | Staging-only core | **Keep & Remap** |
| `GovernanceProfile.tsx` | `/dashboard/governance` | Framework applicability profile | Compliance / Legal | **Admin** | Unique | **Keep & Remap** |
| `AuditCalendar.tsx` | `/dashboard/audit-calendar` | Compliance audit forecast | Compliance Manager | **Admin** | Unique | **Keep & Remap** |
| `AIAttackSimulationLab.tsx` | `/dashboard/ai-attack-simulation-lab` | AI attack & firewall simulator | AI SecOps / Red Team | **Operations** | Unique lab | **Keep & Remap** |
| `BoardStory.tsx` | `/dashboard/board-story` | 10-section AI board narrative | Executive / CISO | **Business** | Unique | **Keep** |
| `DecisionEngine.tsx` | `/dashboard/decision-engine` | Remediation priority engine | CISO / IT Manager | **Operations** | Unique | **Keep** |
| `BusinessUnits.tsx` | `/dashboard/business-units` | Subsidiary risk hierarchy | Enterprise Arch | **Business** | Unique | **Keep** |
| `ReadinessTimeline.tsx` | `/dashboard/readiness-timeline` | Historical score trend | Executive / Manager | **Business** | Unique | **Keep** |
| `RemediationLedger.tsx` | `/dashboard/remediation` | Remediation task backlog | SecOps / IT Team | **Operations** | Unique | **Keep** |
| `clinic/*` (6 files) | `/clinic/*` | Legacy healthcare prototype | Demo | Legacy | Dead prototype code | **Retire** |
| `docs/*` (5 files) | `/docs/*` | Methodology & Framework docs | All Users | Documentation | Unique | **Keep** |

---

## 6. Legacy Component Preservation & Variant Strategy

The prompt explicitly requires preserving key legacy components by remapping them into the Operations workspace and standardizing UI components with variant props:

### Key Legacy Components to Remap into Operations Workspace

1. **`EvidenceNetwork.tsx`** → Remap to `/operations/integrations`.
   - Preserves: Splunk MCP integration, Wazuh agent status, Webhook manager, API Key generation, Evidence Confidence Gauge (`ConfidenceGauge.tsx`), and `ConnectorActivityPanel.tsx`.
2. **`ComplianceDrift.tsx`** → Remap to `/operations/compliance-drift`.
   - Preserves: Drift Timeline chart, active signals list, DIS impact score gauge, CSI index, and Shadow AI governance alerts.
3. **`TechnologyIntelligence.tsx`** → Remap to `/operations/technology`.
   - Preserves: Tech Stack Inventory, LTS Lifecycle Monitor, Vulnerability Exposure tab, Framework Coverage tab, and Dependencies tab.
4. **`ReliabilityDashboard.tsx`** → Remap to `/operations/reliability`.
   - Preserves: Reliability Risk Index (RRI), Breach Exposure badge, Downtime budget calculator, SLA Advisor, and Board simulation mode.
5. **`AIAttackSimulationLab.tsx`** → Remap to `/operations/simulation-lab`.
   - Preserves: Logic Firewall simulation, prompt injection testing, and exfiltration trace log.

### Component Standardization & Variant Strategy

To support progressive disclosure without duplicating code, existing UI components will be refactored with `variant` props:

- **`StatusCard.tsx`** (Refactored `StoryActionCard` / `Card`):
  - `variant="compact"`: Business view — displays high-level status badge, title, and key metric (e.g. Clinic Ready: 98%).
  - `variant="expanded"`: Expanded business card — includes impact narrative, recommendation, and "Why" summary.
  - `variant="technical"`: Operations view — exposes underlying telemetry source, connector health, confidence score, raw evidence, and verification timestamp.
- **`GHIGauge.tsx` / `ConfidenceGauge.tsx`**:
  - `variant="summary"`: Single score badge for executive header.
  - `variant="detailed"`: Full radial gauge with breakdown breakdown for operational dashboards.

---

## 7. State Management & Data Flow Audit

### React Context State
1. **`AuthContext.tsx`**: Manages Firebase auth state (`user`, `loading`, `error`), provides `getToken()`, and injects bearer tokens into `api.ts`.
2. **`DemoModeContext.tsx`**: Polls `/api/v1/system-status` on mount; exposes `isDemoMode` and `isReadOnly` flags to disable mutation buttons in interactive demos.
3. **`PersonaContext.tsx`**: Manages `persona` (`EXECUTIVE` | `FORENSIC`), persisting selection in `localStorage` under `resilai-dashboard-persona`.
4. **`ThemeContext.tsx`**: Manages application theme (`light` | `dark` | `system`), persisting in `localStorage` under `resilai-theme`.

### API & Data Fetching Layer (`src/api.ts` & `src/cache.ts`)
- **No External State Library**: The project does NOT use Redux, MobX, or TanStack Query.
- **Single API Client**: All backend calls pass through `src/api.ts`, which uses standard `fetch` with token injection and error wrapping (`ApiRequestError`).
- **In-Memory Cache (`src/cache.ts`)**: Implements `apiCache` with TTL-based expiration (60 seconds for list endpoints, 5 minutes for summaries). Mutations invoke `invalidateAfterMutation()`.
- **Backend Contract Compliance (R13)**: The frontend derives NO readiness scores or business logic locally. It strictly renders values served by the backend endpoints (e.g., `DailyReadinessReport`, `AssessmentSummary`, `GHIResponse`).

---

## 8. Verification & Build Health

### Build Verification Command Output
Running `npm run build` in `P:\projects\AIRS\frontend`:
- Command: `tsc -b && vite build`
- TypeScript Compilation: Clean pass (exit code 0).
- Bundler Output: Generated production assets in `dist/`.

---

## 9. Conclusion & Next Steps

The codebase is well-structured, modular, and in good health. The refactoring into a Dual Workspace Architecture can proceed smoothly by:
1. Extracting design tokens into `DESIGN_SYSTEM.md`.
2. Generating `UI_INVENTORY.md`, `FEATURE_MAP.md`, `ROUTE_MAP.md`, `COMPONENT_MAP.md`, and `FRONTEND_ARCHITECTURE.md`.
3. Creating the unified Dual Workspace shell sidebar (`Dashboard`, `Operations`, `Administration`).
4. Remapping legacy components into the Operations workspace without rewriting them.
