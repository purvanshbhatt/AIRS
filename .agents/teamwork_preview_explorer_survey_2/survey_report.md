# ResilAI Frontend Audit: State Management, Backend Contracts, Personas, and UX Mechanisms

**Survey Date**: August 3, 2026  
**Auditor**: Explorer 2 (State, Contract & Persona Explorer)  
**Target Workspace**: `P:\projects\AIRS\frontend`  

---

## Executive Summary

This comprehensive audit evaluates the current state management architecture, backend contract compliance, target persona alignment, accessibility, theme support, responsiveness, and error/offline handling within the ResilAI frontend application.

### Key Audit Findings
1. **State Management**: The application currently has **no centralized client state library** (neither Redux nor TanStack Query is installed). State is managed via 5 separate React Contexts (`ThemeContext`, `AuthContext`, `DemoModeContext`, `PersonaContext`, `ToastProvider`) and fragmented local state (`useState`/`useEffect`) across 30+ pages and components. An in-memory API cache (`apiCache` in `src/cache.ts`) exists for legacy list endpoints but is bypassed by the new Readiness endpoints.
2. **Backend Contract Compliance**: The frontend defines a strong contract for `DailyReadinessReport` (`src/types/readiness.ts`) and consumes it cleanly in the `/readiness` views. However, legacy components in `/dashboard` (e.g. `ResultsTabs.tsx`, `CompetitorParityChart.tsx`, `Analytics.tsx`, `useMockTrustData.ts`) perform derived calculations, percentage transformations, simulated top-performer scores, and local mock data generation, violating Requirement R13 (Frontend must display backend values directly without client-side calculations).
3. **Target Personas & Dual Workspace**: There are currently two disconnected application shells (`/readiness/*` using `ReadinessLayout` and `/dashboard/*` using `DashboardLayout`). Feature flag `IS_READINESS_PRODUCT = true` hard-redirects users to `/readiness`, completely obscuring the rich legacy technical views (`EvidenceNetwork`, `TechnologyIntelligence`, `ComplianceDrift`). `PersonaContext` only toggles a local flag between `EXECUTIVE` and `FORENSIC` in a few dashboard cards rather than driving a unified Dual Workspace (Business vs. Operations) with progressive zoom levels.
4. **Theme Support Defect**: While `ThemeContext` manages `light`/`dark`/`system` modes and sets `dark` class / `data-theme` on `document.documentElement`, **all newly written components in `src/components/readiness/` (`NorthStarHero`, `ExecutiveQuestionsGrid`, `StoryActionCard`, `RecoveryReadinessBanner`, `ReadinessStates`) hardcode white/slate CSS classes (`bg-white`, `border-slate-200`, `text-slate-900`) without `dark:` Tailwind utilities**. Switching to dark mode leaves the primary Readiness pages rendered with bright white backgrounds and unreadable text.
5. **Accessibility & Offline Gaps**: Component disclosers (`StoryActionCard`, `Accordion`) lack proper `aria-expanded` and keyboard navigation bindings. No offline detection (`navigator.onLine`) or offline fallback state exists; network drops lead to unhandled `ApiRequestError` toast/modal triggers.

---

## 1. State Management Audit

### 1.1 React Context Inventory
The application relies on 5 global React Contexts wrapped in `src/App.tsx` and `src/main.tsx`:

| Context Name | Provider Location | Managed State | Storage / Side Effects | Assessment |
|--------------|-------------------|---------------|------------------------|------------|
| **ThemeContext** | `src/contexts/ThemeContext.tsx` | `theme` (`light` \| `dark` \| `system`), `resolvedTheme` | Persists to `localStorage` (`resilai-theme`). Updates `document.documentElement` (`data-theme`, `.dark` class) & SVG favicon. | Well-structured core context, but UI components fail to consume dark classes. |
| **AuthContext** | `src/contexts/AuthContext.tsx` | Firebase `user`, `loading`, `error`, `isConfigured` | Injects Firebase ID token into API client via `setTokenProvider`. Handles Google popup & Email auth. Clears cache on logout via `clearUserData()`. | Functional auth layer. Correctly propagates JWT tokens to fetch calls. |
| **DemoModeContext** | `src/contexts/DemoModeContext.tsx` | `isDemoMode`, `isReadOnly`, `systemStatus`, `isLoading` | Fetches `/api/v1/status` on mount. Intercepts mutations (`POST`/`PUT`/`DELETE`) in demo mode, dispatches `resilai-readonly-action` event. | Clean read-only guard for demo environments. |
| **PersonaContext** | `src/contexts/PersonaContext.tsx` | `persona` (`EXECUTIVE` \| `FORENSIC`) | Persists to `localStorage` (`resilai-dashboard-persona`). | Superficial toggle; not integrated into routing or layout hierarchy. |
| **ToastContext** | `src/components/ui/Toast.tsx` | `toasts` array (`id`, `title`, `message`, `type`, `duration`) | Auto-dismiss timers (default 5000ms). Renders fixed toast container. | Functional UI notification store. |

### 1.2 Query & Central Store Audit
- **TanStack Query (@tanstack/react-query)**: **NOT INSTALLED**. Zero usage in `package.json` or source files.
- **Redux / Redux Toolkit**: **NOT INSTALLED**. No central store or slice architecture.
- **Data Fetching Pattern**: Imperative `useEffect` + `useState` fetching on component mount. Results in:
  - Redundant refetching on every route navigation.
  - No background revalidation or window focus re-fetching.
  - Race conditions during rapid navigation.
  - Lack of global state cache sharing between sibling pages.

### 1.3 API Caching Architecture (`src/cache.ts`)
- **Implementation**: Custom `ApiCache` singleton class wrapping an in-memory `Map<string, CacheEntry<T>>`.
- **Features**: TTL-based expiration (default 60s for lists, 5m for summaries), manual invalidation by key or prefix (`invalidateAfterMutation('org' | 'assessment' | 'report')`).
- **Usage**: Used via `cachedFetch()` for `ORGANIZATIONS`, `ASSESSMENTS`, `REPORTS`, and `SUMMARY` in legacy API wrappers.
- **Gap**: The new `getDailyReadinessReport(orgId)` call bypasses `apiCache` and makes raw `request()` fetches every time, missing caching opportunities.

### 1.4 Loading State Mechanisms
- `LoadingState` component (`src/components/readiness/ReadinessStates.tsx`): Displays a centered `Loader2` spinner.
- `Skeleton` component (`src/components/ui/Skeleton.tsx`): Reusable pulse placeholders.
- **Inconsistency**: Pages inconsistently choose between `Skeleton`, `LoadingState`, full-page spinners, or plain text "Loading...".

---

## 2. Backend Contract Compliance Audit

### 2.1 DailyReadinessReport Frozen Contract Compliance
- **Contract Specification**: `src/types/readiness.ts` defines `DailyReadinessReport`:
  - `status`: `'safe_to_open' | 'action_needed' | 'critical_risk' | 'unknown'`
  - `clinic_health_pct`: `number` (0-100)
  - `connector_health_pct`: `number` (0-100)
  - `greeting`: `string`
  - `summary`: `string`
  - `timeline`: `TimelineEvent[]`
  - `business_continuity`: `BusinessContinuity` (`ransomware_safe`, `can_operate_today`, `can_recover_today`, `blockers`, `estimated_recovery_hours`, `last_backup_verified_at`, `verified_systems`, `assumed_systems`)
  - `passed_checks`, `failed_checks`, `warnings`: `ReadinessCheck[]`
  - `unknowns`: `UnknownItem[]`
  - `immediate_actions`: `ActionCard[]`
  - `coverage`: `CoverageReport`
  - `connectors`: `ConnectorReadiness[]`
  - `verification`: `VerificationContext`
  - `trend`: `ReadinessTrend`
  - `value`: `ValueSummary`
  - `generated_at`: ISO timestamp string
- **Backend API**: `getDailyReadinessReport(orgId)` calls `/api/clinic/readiness/${orgId}`.
- **Compliance Assessment**: The `/readiness` views (`TodayPage`, `NeedsAttentionPage`, `RecoveryReadinessPage`, `ActivityPage`) render backend-supplied fields without client-side score re-computation.

### 2.2 Contract Violations in Legacy & Shared Components (R13 Audit)
The following files violate Requirement R13 (No client-side calculations or score derivations):

1. `src/components/ResultsTabs.tsx` (Lines 860-880):
   - Computes MITRE, CIS, OWASP, and NIST CSF coverage percentages directly on the frontend:
     `const mitrePct = mitreTotal > 0 ? (mitreCount / mitreTotal * 100) : 0`
   - Generates summary text strings dynamically based on finding counts rather than using backend narrative summaries.
2. `src/components/CompetitorParityChart.tsx` (Line 57):
   - Simulates top 10% industry benchmark using client-side math: `Math.min(industryAvg + 22, 98)`.
3. `src/hooks/useMockTrustData.ts`:
   - Hardcodes client-side mock trust data objects rather than fetching server-authoritative readiness data.
4. `src/pages/Analytics.tsx` (Lines 145, 155, 225):
   - Infers readiness level strings from numeric scores using frontend helper `getReadinessLevel(score)`.

---

## 3. Target Persona & Page Inventory Audit

The following table categorizes every page and view in `src/pages` and `src/features/readiness` by Target Persona, Core Business Question, Current State, and Target Dual Workspace Placement.

| Page / Route | Target Persona | Primary Business Question | Current State / Component | Target Workspace & Placement |
|--------------|----------------|---------------------------|---------------------------|------------------------------|
| `TodayPage` (`/readiness`) | **Business Executive** | "Is our clinic safe to open today? Can we operate and recover from ransomware?" | `src/features/readiness/TodayPage.tsx` | **Business Workspace** (Main Dashboard) |
| `NeedsAttentionPage` (`/readiness/actions`) | **Business Executive / Operations** | "What critical problems or security blockers require action today?" | `src/features/readiness/NeedsAttentionPage.tsx` | **Business Workspace** (Action Center / Drilldown) |
| `RecoveryReadinessPage` (`/readiness/continuity`) | **Business Executive / Operations** | "Are our backups verified and what is our estimated recovery time?" | `src/features/readiness/RecoveryReadinessPage.tsx` | **Business Workspace** (Continuity Tab) |
| `ActivityPage` (`/readiness/activity`) | **Technical Operations** | "What security events, verifications, and system updates occurred recently?" | `src/features/readiness/ActivityPage.tsx` | **Operations Workspace** (Activity & Event Log) |
| `ReadinessSettingsPage` (`/readiness/settings`) | **Administration** | "How are operational thresholds, alerts, and notification preferences configured?" | `src/features/readiness/SettingsPage.tsx` | **Administration Workspace** |
| `Dashboard` (`/dashboard`) | **Technical Operations** | "What is our overall risk matrix, GHI score, and connector activity status?" | `src/pages/Dashboard.tsx` | **Operations Workspace** (Technical Overview) |
| `BoardStory` (`/dashboard/board-story`) | **Business Executive** | "What high-level security posture story and ROI metrics can I present to the Board?" | `src/pages/BoardStory.tsx` | **Business Workspace** (Executive Reports / Board View) |
| `Reports` (`/dashboard/reports`) | **Business Executive / Admin** | "Where can I generate and export compliance certificates and executive PDFs?" | `src/pages/Reports.tsx` | **Business Workspace** (Reports) |
| `AnalyticsPage` (`/dashboard/analytics`) | **Business Executive / Operations** | "How are our readiness scores and maturity levels trending across time?" | `src/pages/Analytics.tsx` | **Business Workspace** (Executive Analytics) / **Ops** |
| `BusinessUnits` (`/dashboard/business-units`) | **Business Executive / Admin** | "How does readiness compare across our regional clinics and business divisions?" | `src/pages/BusinessUnits.tsx` | **Business Workspace** (Multi-Unit View) |
| `EvidenceNetwork` (`/dashboard/evidence-network`) | **Technical Operations** | "Which automated telemetry integrations (Splunk, CrowdStrike, Sentinel) are active?" | `src/pages/EvidenceNetwork.tsx` | **Operations Workspace** (Evidence Network) |
| `TechnologyIntelligence` (`/dashboard/tech-stack`) | **Technical Operations** | "What software assets, infrastructure dependencies, and EOL risks exist?" | `src/pages/TechnologyIntelligence.tsx` | **Operations Workspace** (Tech Stack Intelligence) |
| `ComplianceDrift` (`/dashboard/compliance-drift`) | **Technical Operations** | "Which framework controls have drifted out of compliance since the last baseline?" | `src/pages/ComplianceDrift.tsx` | **Operations Workspace** (Compliance Drift) |
| `ReliabilityDashboard` (`/dashboard/reliability`) | **Technical Operations** | "What is the uptime, latency, and operational health of our core IT infrastructure?" | `src/pages/ReliabilityDashboard.tsx` | **Operations Workspace** (Reliability & Uptime) |
| `RemediationLedger` (`/dashboard/remediation`) | **Technical Operations** | "What security remediation tickets are open, assigned, or pending resolution?" | `src/pages/RemediationLedger.tsx` | **Operations Workspace** (Remediation Ledger) |
| `DecisionEngine` (`/dashboard/decision-engine`) | **Technical Operations** | "What specific security investments yield the highest readiness improvement?" | `src/pages/DecisionEngine.tsx` | **Operations Workspace** (Decision Engine) |
| `ReadinessTimeline` (`/dashboard/readiness-timeline`) | **Technical Operations** | "How has technical readiness evolved over specific audit milestones?" | `src/pages/ReadinessTimeline.tsx` | **Operations Workspace** (Timeline) |
| `Assessments` (`/dashboard/assessments`) | **Technical Operations / Assessor** | "What formal security audits have been executed, and what are their statuses?" | `src/pages/Assessments.tsx` | **Operations Workspace** (Assessments List) |
| `NewAssessment` / `QuickAssessment` | **Technical Operations** | "How do I launch and complete a new security audit questionnaire?" | `src/pages/NewAssessment.tsx`, `QuickAssessment.tsx` | **Operations Workspace** (Assessment Wizard) |
| `Results` (`/dashboard/results/:id`) | **Technical Operations** | "What are the domain scores, NIST/MITRE mappings, and detailed findings for run X?" | `src/pages/Results.tsx` | **Operations Workspace** (Assessment Results) |
| `AIAttackSimulationLab` (`/dashboard/...`) | **Technical Operations** | "How do our security controls hold up against simulated AI attack vectors?" | `src/pages/AIAttackSimulationLab.tsx` | **Operations Workspace** (Attack Simulation) |
| `AuditorView` (`/auditor`) | **Compliance Auditor** | "Where is the read-only evidence package and cryptographic chain of custody for external audit?" | `src/pages/AuditorView.tsx` | **Operations Workspace** (Auditor Portal) |
| `Organizations` (`/dashboard/organizations`) | **Administration** | "Which tenant organizations and clinic sites are managed in ResilAI?" | `src/pages/Organizations.tsx` | **Administration Workspace** (Tenant Orgs) |
| `NewOrg` (`/dashboard/org/new`) | **Administration** | "How do I onboard a new clinic or business entity into the system?" | `src/pages/NewOrg.tsx` | **Administration Workspace** (Org Creation) |
| `GovernanceProfile` (`/dashboard/governance`) | **Administration** | "What governance policies, risk targets, and compliance frameworks are configured?" | `src/pages/GovernanceProfile.tsx` | **Administration Workspace** (Governance) |
| `AuditCalendar` (`/dashboard/audit-calendar`) | **Administration** | "When are upcoming compliance audits, renewals, and policy reviews scheduled?" | `src/pages/AuditCalendar.tsx` | **Administration Workspace** (Calendar) |
| `Settings` (`/dashboard/settings`) | **Administration** | "What are global user management, API keys, and security settings?" | `src/pages/Settings.tsx` | **Administration Workspace** (Settings) |

---

## 4. Accessibility, Theme, Responsive Layout, and UX Mechanics Audit

### 4.1 Accessibility (a11y) Review
- **Aria Attributes**: `Toast.tsx` correctly sets `role="alert"`. However, modal dialogs (`CoverageModal.tsx`, `SlideOver.tsx`) and expandable accordion items (`StoryActionCard.tsx`) lack `aria-expanded`, `aria-controls`, and `aria-labelledby` attributes.
- **Keyboard Navigation**: Buttons and links have default focus rings, but custom interactive elements (such as confidence pills in `NorthStarHero.tsx` or table row clicks) rely on `onClick` without `onKeyDown` (Enter/Space) handlers or explicit `tabIndex`.
- **Color Contrast**: Subtle text colors (e.g. `text-slate-400` uppercase headers on light slate backgrounds) fall below WCAG AAA contrast guidelines.

### 4.2 Theme Support Defect (Critical Finding)
- **Architecture**: `ThemeContext` provides clean `theme` state (`light` \| `dark` \| `system`) and updates `document.documentElement` attribute `data-theme` and class `.dark`.
- **Defect**: Every single component in `src/components/readiness/` was written using fixed light-mode Tailwind classes without dark mode overrides:
  - `NorthStarHero.tsx`: `bg-white`, `border-slate-200`, `text-slate-600` (missing `dark:bg-slate-900`, `dark:border-slate-800`, `dark:text-slate-300`).
  - `ExecutiveQuestionsGrid.tsx`: `bg-white`, `border-slate-200`, `text-slate-700` (missing `dark:...`).
  - `StoryActionCard.tsx`: `bg-white`, `border-slate-200`, `text-slate-900` (missing `dark:...`).
  - `RecoveryReadinessBanner.tsx`: `bg-white`, `border-slate-200` (missing `dark:...`).
  - `ReadinessStates.tsx`: `bg-emerald-50/50`, `bg-slate-50`, `bg-red-50` (missing dark variants).
- **User Impact**: Toggling dark mode renders the main Readiness view with stark white boxes, dark text on dark backgrounds in expanded sections, and broken aesthetic balance.

### 4.3 Responsive Layout Review
- **Grid Systems**: Layouts use fluid Tailwind breakpoint grids (`grid-cols-1 md:grid-cols-2 lg:grid-cols-4`), adapting cleanly from 1440px down to 768px.
- **Mobile Viewport Deficiencies (<640px)**:
  - Tables in `RemediationLedger.tsx`, `Organizations.tsx`, and `ResultsTabs.tsx` overflow horizontally without an explicit `overflow-x-auto` container, causing viewport stretching.
  - `NorthStarHero.tsx` padding (`p-8 md:p-12`) is slightly oversized on narrow mobile screens (375px width).

### 4.4 Loading, Error, Empty, and Offline Mechanics
- **Loading State**: `LoadingState` component (`src/components/readiness/ReadinessStates.tsx`) renders a spinner. However, page loading triggers layout reflow because skeletons are not consistently sized to match destination content.
- **Error Handling**: `ErrorState` provides a user-facing error message with a "Try Again" retry callback. Global `ErrorBoundary` catches React render errors. `ApiRequestError` formats backend HTTP status codes.
- **Empty States**: `HealthyState` serves as a positive empty state when zero items require attention. `EmptyState.tsx` exists for generic empty tables.
- **Offline Mechanisms (Deficiency)**: The application has **no offline detector** (`navigator.onLine`), offline banner, or service worker cache. Disconnecting from network causes unhandled API request exceptions with network failure toasts.

---

## 5. Strategic Recommendations for Implementation Phase

1. **State Management Modernization**:
   - Introduce TanStack Query (`@tanstack/react-query`) or expand `apiCache` with a unified custom hook layer (`useDailyReadinessReport`, `useOrganizations`, `useAssessments`) to eliminate duplicate page fetches and enable seamless cache revalidation.
2. **Unified Dual Workspace Shell**:
   - Replace the fragmented routes (`IS_READINESS_PRODUCT` binary switch) with a single application layout containing a top navigation or sidebar mode switcher between **Business Workspace** (Executive summary, readiness status, board story, ROI) and **Operations Workspace** (Technical depth, Evidence Network, Tech Stack, Compliance Drift, Assessments, Decision Engine).
3. **Strict Backend Contract Enforcement**:
   - Refactor `ResultsTabs.tsx`, `CompetitorParityChart.tsx`, and `Analytics.tsx` to remove client-side math and derived readiness levels, consuming backend payload properties directly.
4. **Design System & Theme Tokens Standardization**:
   - Extract design tokens into `DESIGN_SYSTEM.md` and systematically add `dark:` utility variants to all readiness components (`NorthStarHero`, `ExecutiveQuestionsGrid`, `StoryActionCard`, `RecoveryReadinessBanner`, `ReadinessStates`).
5. **a11y & Offline Resilience**:
   - Add ARIA attributes (`aria-expanded`, `aria-controls`) to expandable disclosers. Add `navigator.onLine` window listeners with an offline banner indicator.
