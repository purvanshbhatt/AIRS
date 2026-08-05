# ResilAI Frontend Architecture Specification (`FRONTEND_ARCHITECTURE.md`)

**Document Version:** 1.0.0  
**Target Application:** ResilAI Frontend (`P:\projects\AIRS\frontend`)  
**Requirement Mapping:** R2 (Dual Workspace), R6 (Navigation Flow), R7 (Progressive Disclosure), R11 (State Management), R12 (Accessibility & Resilience), R13 (Backend Contract Compliance)  
**Author:** Milestone 1 Documentation Suite Worker  

---

## 1. Executive Summary & Architectural Vision

The ResilAI Frontend Refactoring transforms the existing React single-page application into an executive-grade, unified SaaS product serving two distinct primary target personas: **Healthcare Executives / C-Suite** and **IT Operations / SecOps Teams**.

Rather than splitting the product into disconnected applications or using modal environment toggles, ResilAI implements a **Dual Workspace Architecture** linked by **5-Tier Progressive Disclosure**. Non-technical executives obtain a 30-second time-to-insight on clinical operational readiness, while technical engineers can drill directly from executive summary cards into deep diagnostic telemetry without leaving the application context.

---

## 2. Dual Workspace Architecture & Unified Navigation (R2, R6)

### 2.1 Workspace Hierarchy
The application shell (`DualWorkspaceLayout`) hosts three unified workspace sub-trees connected by a persistent `UnifiedSidebar` and top-level `WorkspaceToggle`:

```
DualWorkspaceLayout (Unified Application Shell)
 ├── Business Workspace (/readiness/*)
 │    ├── Persona: Healthcare Executive, C-Suite, Clinic Director
 │    ├── Focus: 30-second readiness assessment, plain-English AI explanations, ransomware recovery confidence
 │    └── Primary Pages: TodayPage, NeedsAttentionPage, RecoveryReadinessPage, ActivityPage, BoardReports
 │
 ├── Operations Workspace (/dashboard/operations/*)
 │    ├── Persona: IT Ops Lead, SecOps Analyst, SRE, Systems Architect
 │    ├── Focus: Deep evidence topology, compliance drift, tech stack lifecycle, SLA reliability, remediation
 │    └── Primary Pages: EvidenceNetwork, ComplianceDrift, TechStack, Reliability, RemediationLedger, Simulation
 │
 └── Administration Workspace (/dashboard/admin/*)
      ├── Persona: System Administrator, CISO, External Auditor
      ├── Focus: Tenant organization setup, risk threshold configuration, audit calendar, auditor access
      └── Primary Pages: Organizations, GovernanceProfile, AuditCalendar, Settings, AuditorPortal
```

### 2.2 Fluid Navigation & Zoom Mechanics (R6)
To satisfy **R6 (Preserve Navigation Flow)**, switching between Business and Operations workspaces behaves like changing the zoom level on a microscope rather than navigating to a different product:
- **Executive Zoom Level (Business Workspace)**: Displays aggregate status badges (`safe_to_open`), natural language summaries, and action item counters.
- **Operational Zoom Level (Operations Workspace)**: Displays full interactive D3/canvas graph nodes, framework violation tables, and raw telemetry payloads.
- **Navigation Rule**: Users can switch zoom levels at any time via the `WorkspaceToggle` control in the top header. Crucially, clicking an "Inspect Evidence" button on any Business card automatically transitions the workspace zoom to the exact corresponding node or report in the Operations Workspace, preserving selected tenant org context and filter states.

---

## 3. 5-Tier Progressive Disclosure Hierarchy (R7)

Progressive disclosure ensures that complex cybersecurity data is revealed gradually across 5 distinct depth tiers:

```
[Level 1: Executive Clinic Readiness Banner]
  │  Visual: StatusCard / NorthStarHero ("Safe to Open: 98% Clinic Readiness")
  │  Target Persona: Healthcare Executive / C-Suite
  │  Action: User clicks "Why did readiness change today?"
  ▼
[Level 2: Business Continuity & Summary Rationale]
  │  Visual: StoryActionCard (Expanded) + AI Translator Panel
  │  Target Persona: VP of Operations / IT Director
  │  Action: User clicks "View Verification Check"
  ▼
[Level 3: Operational Check Verification Summary]
  │  Visual: Verification Context Drawer / SlideOver Panel
  │  Target Persona: IT Manager / Compliance Lead
  │  Action: User clicks "Inspect Connector Telemetry"
  ▼
[Level 4: Technical System & Connector State]
  │  Visual: Tech Stack Lifecycle & Reliability Metric Card
  │  Target Persona: SecOps Analyst / Systems Engineer
  │  Action: User clicks "Trace Evidence Graph Node"
  ▼
[Level 5: Raw Evidence Telemetry & Graph Payload]
  │  Visual: EvidenceNetwork Canvas Node + Raw JSON Telemetry Payload
  │  Target Persona: Security Analyst / Forensic Auditor
```

Every executive summary component must implement event triggers enabling seamless inline expansion or slide-over activation down to Level 5 without page reloads.

---

## 4. AI Translator Panel Architecture & R13 Compliance (R4, R13)

### 4.1 Purpose & Role
The **AI Translator Panel** (`src/components/readiness/AITranslatorPanel.tsx`) bridges the gap between deterministic backend telemetry and executive decision-making. It consumes the backend's deterministic `DailyReadinessReport` object and presents plain-English natural language answers to three key executive questions:
1. *Why did readiness drop or change today?* (Narrative derived from `trend.narrative` and `timeline`).
2. *What is the operational impact on clinical workflows?* (Narrative derived from `business_continuity` blockers and `failed_checks`).
3. *What specific actions are recommended right now?* (Narrative derived from `immediate_actions`).

### 4.2 Backend Contract Integration
In strict compliance with **R13 (Backend Contract Compliance)**, the AI Translator Panel performs **zero client-side readiness score math or mock calculations**. It reads server-authoritative fields from `DailyReadinessReport` (`types/readiness.ts`) and formats realistic explanation streams.

```typescript
// Frozen Backend Contract Schema (src/types/readiness.ts)
export interface DailyReadinessReport {
  status: 'safe_to_open' | 'action_needed' | 'critical_risk' | 'unknown';
  clinic_health_pct: number;
  connector_health_pct: number;
  greeting: string;
  summary: string;
  timeline: TimelineEvent[];
  business_continuity: BusinessContinuity;
  passed_checks: ReadinessCheck[];
  failed_checks: ReadinessCheck[];
  warnings: ReadinessCheck[];
  unknowns: UnknownItem[];
  immediate_actions: ActionCard[];
  coverage: CoverageReport;
  connectors: ConnectorReadiness[];
  verification: VerificationContext;
  trend: ReadinessTrend;
  value: ValueSummary;
  generated_at: string;
}
```

---

## 5. State Management Audit & Modernization Architecture (R11)

### 5.1 Current State Management Inventory
An exhaustive audit of state management across the application revealed:
- **Global Contexts**:
  1. `AuthContext`: Manages Firebase user session, JWT token propagation, login/logout state.
  2. `ThemeContext`: Manages `light` / `dark` / `system` theme state and `document.documentElement` attributes.
  3. `DemoModeContext`: Intercepts `POST`/`PUT`/`DELETE` mutations in demo environments and dispatches read-only notifications.
  4. `PersonaContext`: Manages local `EXECUTIVE` vs. `FORENSIC` persona toggle.
  5. `ToastContext`: Manages transient notification toasts.
- **In-Memory Cache (`src/cache.ts`)**: Custom `ApiCache` class managing TTL-based cache entries (60s lists, 300s summaries). Used by legacy `ORGANIZATIONS`, `ASSESSMENTS`, and `REPORTS` API endpoints.
- **Local Component State**: Component-level `useState` and `useEffect` hooks across pages.

### 5.2 State Modernization Strategy
To prevent duplicate state and redundant network requests:
1. **Unified API Custom Hooks Layer**: Implement custom hooks (`useDailyReadinessReport`, `useOrganizations`, `useAssessments`) wrapping `api.ts` and `cache.ts` to centralize fetch state, loading flags, error handling, and TTL cache revalidation.
2. **Readiness Endpoint Cache Integration**: Extend `cache.ts` to cache `getDailyReadinessReport(orgId)` with a 30-second TTL, preventing duplicate refetches during rapid workspace zoom toggling.
3. **Global Persona Integration**: Elevate `PersonaContext` into `DualWorkspaceLayout` to drive routing defaults and component variant selection automatically.

---

## 6. Accessibility, Theme Hardening, & Resilience Specification (R12)

### 6.1 Accessibility (a11y) Review & Standards
All refactored pages and components must meet WCAG 2.1 AA accessibility guidelines:
- **Keyboard Navigation**: Interactive elements (`Button`, `StoryActionCard`, table rows) must support `Tab` keyboard focus, visible focus rings (`focus:ring-2 focus:ring-blue-500`), and `Enter`/`Space` keypress handlers.
- **ARIA Attributes**:
  - Slide-overs and drawers must include `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, and `aria-describedby`.
  - Expandable components (`StoryActionCard`, `Accordion`) must include explicit `aria-expanded={isExpanded}` and `aria-controls` properties.
  - Toast alerts must include `role="alert"` and `aria-live="polite"`.
- **Color Contrast**: All text elements across both Light (`#F8FAFC`) and Dark (`#121212`) themes must maintain minimum contrast ratios of **4.5:1** for standard body text and **3:1** for headings and badges.

### 6.2 Critical Theme Defect Remediation
The audit identified a critical theme defect: components in `src/components/readiness/` (`NorthStarHero`, `ExecutiveQuestionsGrid`, `StoryActionCard`, `RecoveryReadinessBanner`, `ReadinessStates`) hardcoded white background classes (`bg-white`, `border-slate-200`, `text-slate-900`) without dark mode utility overrides.

**Remediation Rule**: Every white or light background utility class MUST be paired with its dark mode counterpart:
```html
<!-- Example Dual-Theme Compliant Card Styling -->
<div class="bg-white border border-slate-200 text-slate-900 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-100 shadow-sm rounded-xl p-6">
  ...
</div>
```

### 6.3 Offline & Error Resilience Mechanics
- **Offline State Detection**: The root application wrapper will subscribe to `window.addEventListener('online')` and `window.addEventListener('offline')`. When `navigator.onLine === false`, an `OfflineBanner` component will notify the user and serve stale responses from `cache.ts`.
- **Loading Skeleton Standard**: Pages must render matching structural pulse skeletons (`Skeleton.tsx`) rather than full-page spinners to avoid layout shift during data fetching.
- **Empty & Error Fallbacks**: When backend endpoints return empty check lists or network errors, `HealthyState` or `ErrorState` components must provide user-friendly explanation messages and retry controls.

---

## 7. Strict Backend Contract Compliance Audit (R13)

### 7.1 Requirement R13 Core Mandate
The frontend must act purely as a presentation layer consuming server-authoritative readiness data. **Zero client-side readiness score calculation, risk score derivation, percentage transformation, or mock math is permitted on the frontend.**

### 7.2 Violation Audit & Remediation Plan

The table below lists the 4 legacy files violating R13 and the mandatory remediation steps:

| File Path | Violating Code Snippet / Logic | Remediation Plan (R13 Compliance) |
|---|---|---|
| `src/components/ResultsTabs.tsx` | Lines 860-880: Client-side score math `mitreTotal > 0 ? (mitreCount / mitreTotal * 100) : 0` and dynamic string construction. | Remove client-side math loop. Replace with backend-supplied `domain_scores` and framework coverage objects directly from `DailyReadinessReport.coverage`. |
| `src/components/CompetitorParityChart.tsx` | Line 57: Simulates benchmark math `Math.min(industryAvg + 22, 98)`. | Remove client-side addition. Display server-provided peer benchmark object directly from `DailyReadinessReport.value`. |
| `src/hooks/useMockTrustData.ts` | Hardcodes local client mock trust calculation objects. | Deprecate hook. Replace with server-authoritative `useDailyReadinessReport` custom hook. |
| `src/pages/Analytics.tsx` | Lines 145, 155, 225: Infers readiness levels from numeric scores via frontend helper `getReadinessLevel(score)`. | Remove frontend helper. Render server-supplied `status` and `trend` strings directly from backend report object. |
