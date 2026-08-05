# ResilAI Component Map & Variant Specification (`COMPONENT_MAP.md`)

**Document Version:** 1.1.0  
**Target Application:** ResilAI Frontend (`P:\projects\AIRS\frontend`)  
**Requirement Mapping:** Requirement R3 (Component Preservation & Variants) & R7 (Progressive Disclosure)  
**Author:** Milestone 1 Documentation Suite Worker (M1_Fix)  

---

## 1. Executive Summary & Component Architecture

This document specifies the complete component tree, layout structure, variant matrix, and exhaustive catalog for all **63 shared component files** and **50 page/feature files** in the ResilAI frontend application. In accordance with **R3 (Component Preservation & Variant Strategy)**, components are not duplicated across different workspaces. Instead, core shared components are refactored to accept a standardized `variant` prop (`compact` | `expanded` | `technical`), enabling seamless visual and structural adaptation between executive summary views and deep operational diagnostic views.

---

## 2. Component Hierarchy Tree

```
App (AuthProvider, DemoModeProvider, PersonaProvider, ToastProvider, Router)
 ├── External Portal Shell (Public Navbar + Footer)
 │    ├── Landing Page (src/pages/Landing.tsx)
 │    ├── Login Portal (src/pages/Login.tsx)
 │    ├── About Page (src/pages/About.tsx)
 │    ├── Security & Trust Page (src/pages/Security.tsx)
 │    ├── Pilot Portal (src/pages/Pilot.tsx)
 │    ├── System Status (src/pages/Status.tsx)
 │    ├── Public Documentation (src/components/layout/DocsLayout.tsx)
 │    │    ├── Overview (src/pages/docs/Overview.tsx)
 │    │    ├── Methodology (src/pages/docs/Methodology.tsx)
 │    │    ├── Frameworks (src/pages/docs/Frameworks.tsx)
 │    │    ├── Security (src/pages/docs/Security.tsx)
 │    │    ├── API Reference (src/pages/docs/Api.tsx)
 │    │    └── Docs Index (src/pages/docs/index.ts)
 │    └── Auditor View (src/pages/AuditorView.tsx)
 │
 └── Authenticated Dual Workspace Shell (DualWorkspaceLayout)
      ├── Environment Banner (ApiConfigBanner / EnvironmentHeader / EnvironmentBanner)
      ├── Top Navigation Header (Header)
      │    ├── Organization Selector Dropdown
      │    ├── Workspace Zoom Toggle (WorkspaceToggle: Business <-> Operations)
      │    ├── Global Search Input
      │    ├── Persona Switcher (PersonaContext: Executive / Technical)
      │    └── Theme Toggle Button (ThemeToggle: Light / Dark)
      │
      ├── Left Sidebar Navigation (UnifiedSidebar)
      │    ├── Dashboard Group (Business Workspace)
      │    │    ├── Today's Readiness (/readiness - TodayPage)
      │    │    ├── Needs Attention (/readiness/actions - NeedsAttentionPage)
      │    │    ├── Recovery Readiness (/readiness/continuity - RecoveryReadinessPage)
      │    │    ├── Activity Feed (/readiness/activity - ActivityPage)
      │    │    └── Board Reports (/dashboard/board-story - BoardStory)
      │    │
      │    ├── Operations Group (Operations Workspace)
      │    │    ├── Operations Overview (/dashboard/operations - Dashboard / Analytics)
      │    │    ├── Evidence Network (/dashboard/operations/evidence - EvidenceNetwork)
      │    │    ├── Compliance Drift (/dashboard/operations/compliance - ComplianceDrift)
      │    │    ├── Tech Stack (/dashboard/operations/technology - TechnologyIntelligence)
      │    │    ├── Reliability (/dashboard/operations/reliability - ReliabilityDashboard)
      │    │    ├── Remediation Ledger (/dashboard/operations/remediation - RemediationLedger)
      │    │    ├── Decision Engine (/dashboard/operations/decision-engine - DecisionEngine)
      │    │    ├── AI Attack Simulation (/dashboard/operations/simulation - AIAttackSimulationLab)
      │    │    └── Assessment Management (/dashboard/operations/assessments - Assessments / Results)
      │    │
      │    └── Administration Group (Admin Workspace)
      │         ├── Organizations (/dashboard/admin/organizations - Organizations / NewOrg)
      │         ├── Risk Governance (/dashboard/admin/governance - GovernanceProfile)
      │         ├── Audit Calendar (/dashboard/admin/calendar - AuditCalendar)
      │         └── System Settings (/dashboard/admin/settings - SettingsPage / Settings)
      │
      └── Workspace View Container
           ├── Business Workspace Components
           │    ├── TodayPage (NorthStarHero, AITranslatorPanel, StatusCards, ExecutiveQuestionsGrid)
           │    ├── ExecutiveMondayMorning & ExecutiveRiskMatrix
           │    ├── GHIGauge & SuggestedQuestionsPanel
           │    ├── ReadinessDrivers & ReadinessHeader
           │    ├── RecoveryReadinessPage (RecoveryReadinessBanner)
           │    └── ActivityPage (ReadinessHistoryTimeline)
           │
           ├── Operations Workspace Components & Sub-Tabs
           │    ├── EvidenceNetwork & EvidenceGraph
           │    ├── EvidenceTimeline & TrustScore & ConfidenceGauge
           │    ├── VerificationSummaryGrid & ConnectorActivityPanel
           │    ├── EnterpriseRoadmap & RoadmapTracker & ScoreTrendChart
           │    ├── TechStackLifecycleMonitor & OrgEnrichmentCard
           │    ├── ResultsTabs & ResultsTabsConfig & CompetitorParityChart
           │    └── Tech Stack Sub-Tabs
           │         ├── InventoryTab (src/components/technology/InventoryTab.tsx)
           │         ├── DependenciesTab (src/components/technology/DependenciesTab.tsx)
           │         ├── ExposureTab (src/components/technology/ExposureTab.tsx)
           │         ├── LifecycleTab (src/components/technology/LifecycleTab.tsx)
           │         ├── TimelineTab (src/components/technology/TimelineTab.tsx)
           │         └── InsightsTab (src/components/technology/InsightsTab.tsx)
           │
           └── Shared UI Primitives, Layouts & Infrastructure
                ├── Layout Containers (DashboardLayout, ReadinessLayout, DocsLayout, Footer)
                ├── StatusCard (Variant: compact | expanded | technical)
                ├── StoryActionCard (Variant: compact | expanded | technical)
                ├── NorthStarHero (Variant: compact | expanded | technical)
                ├── TrustBadge (Variant: compact | expanded | technical)
                ├── Badge (Variant: compact | expanded | technical)
                ├── UI Primitives (Button, Card, Input, Select, Table, Tabs, Accordion, EmptyState, Skeleton, Toast, Tooltip)
                ├── Modals & Drawers (Modal, SlideOver, Common SlideOver, HowWeKnowDrawer, CoverageModal, ApiDiagnosticsPanel)
                ├── Utilities & Infrastructure (ProgressSteps, ErrorBoundary, ProtectedRoute)
                └── Barrel Exports (components/ui/index.ts, components/layout/index.ts)
```

---

## 3. Layout Component Breakdown

### 3.1 `DualWorkspaceLayout` (`src/components/layout/DualWorkspaceLayout.tsx`)
- **Purpose**: Unified layout wrapper managing persistent navigation, environment notifications, top header actions, and main route container.
- **Child Components**: `UnifiedSidebar`, `Header`, `ApiConfigBanner`, `EnvironmentHeader`, `Toast`.
- **Responsive Behavior**: Collapsible sidebar on mobile/tablet viewports (<1024px) with hamburger slide-over menu; fixed 256px width sidebar on desktop (>=1024px).

### 3.2 `UnifiedSidebar` (`src/components/layout/UnifiedSidebar.tsx`)
- **Purpose**: Persistent left navigation covering all three workspace tiers (**Dashboard/Business**, **Operations**, **Administration**).
- **Features**: Active route highlight, workspace category headers, unread action counter badges, and workspace zoom mode switcher link.

### 3.3 `WorkspaceToggle` (`src/components/layout/WorkspaceToggle.tsx`)
- **Purpose**: Header toggle control providing fluid transition between Business (executive zoom level) and Operations (technical zoom level).
- **Behavior**: Preserves current clinic/org context when switching workspaces; updates route smoothly without page reload.

### 3.4 `DocsLayout` (`src/components/layout/DocsLayout.tsx`)
- **Purpose**: Documentation layout container with sticky sidebar table of contents for `/docs/*` pages.
- **Child Pages**: `Overview.tsx`, `Methodology.tsx`, `Frameworks.tsx`, `Security.tsx`, `Api.tsx`.

---

## 4. Component Variant Specification Matrix (R3)

The contract interface for variant-enabled components is defined as:

```typescript
export type ComponentVariant = 'compact' | 'expanded' | 'technical';

export interface VariantProps {
  variant?: ComponentVariant;
}
```

The matrix below specifies the exact data props, visual appearance, interaction behavior, and Tailwind CSS tokens for each variant across core components:

| Component Name | Variant Key | Visual Specifications & Dimensions | Data Props & Displayed Fields | Interaction & Disclosure Mechanics | CSS Utility Class Pattern |
|---|---|---|---|---|---|
| **StatusCard** | `compact` | Height `40px` (`h-10`), padding `px-3 py-2`, horizontal flex layout, rounded `md`. | Title, Status Pill (`safe`, `warning`, `danger`), score %. | Hover focus ring; click triggers inline expansion or slide-over. | `flex items-center justify-between p-2 rounded-md bg-white border border-slate-200 dark:bg-slate-900 dark:border-slate-800` |
| **StatusCard** | `expanded` | Height `160px` (`h-40`), padding `p-5`, vertical layout with metric badge, rounded `xl`, shadow `card`. | Title, Score %, Trend Narrative, AI summary snippet, action link. | Click header to expand; click "Why?" button to open AI Translator Panel. | `flex flex-col justify-between p-5 rounded-xl bg-white border border-slate-200 shadow-sm dark:bg-slate-900 dark:border-slate-800` |
| **StatusCard** | `technical` | Height `220px` (`h-55`), padding `p-5`, dense grid layout, monospace metrics, rounded `lg`. | Title, Score %, Inspector ID, Last Verified Timestamp, Connector Latency ms, Raw JSON payload link. | Click "Trace Evidence" to open `HowWeKnowDrawer` at Level 5 raw evidence. | `grid grid-cols-2 gap-3 p-5 rounded-lg bg-slate-900 border border-slate-800 text-slate-100 font-mono` |
| **StoryActionCard** | `compact` | Height `48px` (`h-12`), padding `px-4 py-2.5`, single-line text with action button. | Priority Badge (`P1`, `P2`), Action Title, System Name, 1-Click Resolve button. | Click button triggers instant action modal; click row expands inline. | `flex items-center justify-between px-4 py-2.5 rounded-lg border border-slate-200 bg-white dark:bg-slate-900 dark:border-slate-800` |
| **StoryActionCard** | `expanded` | Height `auto` (`p-6`), card layout with rationale, impact explanation, and action drawer trigger. | Priority Badge, Action Title, "Why it matters" narrative, System impact list, Recommended fix. | Click "Inspect Verification" triggers Level 3 slide-over check. | `p-6 rounded-xl border border-slate-200 bg-white shadow-sm dark:bg-slate-900 dark:border-slate-800` |
| **StoryActionCard** | `technical` | Height `auto` (`p-6`), dense technical card with telemetry payload and connector log references. | Priority, Action Title, Target Host IP, CVE ID, Connector Log ID, Raw Verification Payload JSON. | Click "Open Evidence Graph" navigates to `/dashboard/operations/evidence?nodeId=X`. | `p-6 rounded-xl border border-slate-800 bg-slate-950 font-mono text-slate-200` |
| **NorthStarHero** | `compact` | Height `64px` (`h-16`), horizontal flex bar with greeting and overall readiness score. | Greeting string, overall readiness percentage, status pill. | Click status pill opens AI summary popover. | `flex items-center justify-between px-6 py-4 rounded-xl bg-emerald-900 text-white` |
| **NorthStarHero** | `expanded` | Height `240px` (`h-60`), gradient hero banner with greeting, readiness score, continuity indicators. | Greeting, Readiness %, Clinic Health %, Connector Health %, Executive Summary, AI Translator trigger button. | Click "Explain Readiness" button opens `AITranslatorPanel`. | `p-8 rounded-2xl bg-gradient-to-r from-emerald-900 to-slate-900 text-white shadow-lg` |
| **NorthStarHero** | `technical` | Height `300px`, dense multi-column telemetry header with connector counts and verification timelines. | Greeting, Overall %, Active Connectors Count, Failed Checks Count, Last Sync Timestamp, Raw Certificate Hash. | Click connector count navigates to `/dashboard/operations/technology`. | `p-8 rounded-2xl bg-slate-950 border border-slate-800 font-mono text-emerald-400` |
| **TrustBadge** | `compact` | Height `24px` (`h-6`), rounded pill with status color dot. | Status label (`safe`, `warning`, `critical`). | Hover shows inline tooltip. | `inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium` |
| **TrustBadge** | `expanded` | Height `32px` (`h-8`), rounded rectangle with icon and verification percentage. | Status label, Verification Confidence %. | Click opens `CoverageModal`. | `inline-flex items-center px-3 py-1 rounded-lg text-xs font-semibold border` |
| **TrustBadge** | `technical` | Height `36px` (`h-9`), dense technical pill with inspector certificate ID. | Status label, Verification %, Inspector ID, Timestamp. | Click opens raw verification log drawer. | `inline-flex items-center px-3.5 py-1.5 rounded-md text-xs font-mono border` |
| **Badge** | `compact` | Height `20px` (`h-5`), text badge with rounded corners. | Label text string. | Static display. | `inline-flex items-center px-2 py-0.5 rounded text-xs font-medium` |
| **Badge** | `expanded` | Height `24px` (`h-6`), text badge with semantic icon dot. | Status label, icon dot indicator. | Interactive hover popover. | `inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold` |
| **Badge** | `technical` | Height `28px` (`h-7`), monospace technical badge. | Metric key/value pair. | Monospace technical view. | `inline-flex items-center px-3 py-1 rounded font-mono text-xs border` |

---

## 5. Legacy Technical Component Remapping Specification

The legacy technical components are preserved and remapped into the Operations Workspace menu as specified below:

| Legacy Component Name | Original File Path | New Workspace Route | Container Component Wrapper | Preserved Technical Features |
|---|---|---|---|---|
| `EvidenceNetwork` | `src/pages/EvidenceNetwork.tsx` | `/dashboard/operations/evidence` | `OperationsLayout` | D3 canvas node graph, interactive evidence inspection, connector topology tree. |
| `ComplianceDrift` | `src/pages/ComplianceDrift.tsx` | `/dashboard/operations/compliance` | `OperationsLayout` | Framework drift progress bars, HIPAA/NIST control breakdown, violation drawer. |
| `TechnologyIntelligence` | `src/pages/TechnologyIntelligence.tsx` | `/dashboard/operations/technology` | `OperationsLayout` | Asset lifecycle matrix, EOL vulnerability monitor, software dependency graph. |
| `ReliabilityDashboard` | `src/pages/ReliabilityDashboard.tsx` | `/dashboard/operations/reliability` | `OperationsLayout` | SLA/SLO metric cards, latency timeline, infrastructure component health grid. |
| `RemediationLedger` | `src/pages/RemediationLedger.tsx` | `/dashboard/operations/remediation` | `OperationsLayout` | Ticket status table, assignee filter, resolution verification evidence drawer. |
| `AIAttackSimulationLab` | `src/pages/AIAttackSimulationLab.tsx` | `/dashboard/operations/simulation` | `OperationsLayout` | Red team attack scenario runner, control resilience score matrix. |

---

## 6. Exhaustive Shared Component Catalog (All 63 Component Files)

The table below catalogs every single file in `src/components/` (63 files total), providing source file path, classification action, target workspace alignment, persona, and refactoring strategy.

| # | Component File | Exact File Path | Classification | Workspace Alignment | Target Persona | Refactoring Strategy & Notes |
|---|---|---|---|---|---|---|
| 1 | `CompetitorParityChart` | `src/components/CompetitorParityChart.tsx` | **Improve** | Operations Workspace | CISO / Compliance Director | Remove client-side benchmark math (`Math.min(industryAvg + 22, 98)`) and render backend compliance benchmarking directly. |
| 2 | `ConnectorActivityPanel` | `src/components/ConnectorActivityPanel.tsx` | **Improve** | Operations Workspace | SRE / SecOps Analyst | Technical connector sync activity monitor, live event stream, and connection status diagnostics. |
| 3 | `EnterpriseRoadmap` | `src/components/EnterpriseRoadmap.tsx` | **Improve** | Operations Workspace | VP Ops / CISO | Multi-quarter risk remediation roadmap and strategic milestone planning grid. |
| 4 | `ErrorBoundary` | `src/components/ErrorBoundary.tsx` | **Keep** | Shared Infrastructure | All Users | React error boundary class component preventing unhandled UI crash cascades. |
| 5 | `EvidenceGraph` | `src/components/EvidenceGraph.tsx` | **Keep** | Operations Workspace | Security Analyst / SRE | Interactive D3/SVG telemetry evidence node graph visualizer component. |
| 6 | `ExecutiveMondayMorning` | `src/components/ExecutiveMondayMorning.tsx` | **Improve** | Business Workspace | C-Suite / Clinic Director | Weekly operational readiness summary card designed for Monday morning briefing. |
| 7 | `ExecutiveRiskMatrix` | `src/components/ExecutiveRiskMatrix.tsx` | **Improve** | Business Workspace | Risk Officer / Executive | Risk heat map grid visualizing risk levels across clinical operational domains. |
| 8 | `GHIGauge` | `src/components/GHIGauge.tsx` | **Improve** | Business Workspace | Compliance Officer / CISO | Governance & Health Index radial gauge widget. Refactor to render backend score directly. |
| 9 | `OrgEnrichmentCard` | `src/components/OrgEnrichmentCard.tsx` | **Improve** | Admin / Operations | System Administrator | Multi-tenant organization metadata, domain enrichment profile, and clinic details card. |
| 10 | `ProgressSteps` | `src/components/ProgressSteps.tsx` | **Keep** | Shared UI Primitives | All Users | Step progress indicator widget for multi-step wizards and assessment forms. |
| 11 | `ProtectedRoute` | `src/components/ProtectedRoute.tsx` | **Keep** | Shared Infrastructure | Authenticated Users | Route protection wrapper verifying user authentication state before rendering child routes. |
| 12 | `ResultsTabs` | `src/components/ResultsTabs.tsx` | **Improve** | Operations Workspace | SecOps / Auditor | Refactor frontend math (MITRE/NIST score derivation) to display server-supplied findings directly. |
| 13 | `ResultsTabsConfig` | `src/components/ResultsTabsConfig.ts` | **Keep** | Operations Workspace | Frontend Developer | Configuration schema defining tab structures and metadata for assessment results. |
| 14 | `RoadmapTracker` | `src/components/RoadmapTracker.tsx` | **Improve** | Operations Workspace | IT Lead / VP Ops | Visual progress tracking timeline for remediation milestone fulfillment. |
| 15 | `ScoreTrendChart` | `src/components/ScoreTrendChart.tsx` | **Improve** | Operations Workspace | Compliance Lead / IT Director | Historical readiness score trend line chart. Refactor to consume server telemetry directly. |
| 16 | `SuggestedQuestionsPanel` | `src/components/SuggestedQuestionsPanel.tsx` | **Improve** | Business Workspace | Healthcare Executive | Interactive panel offering AI-driven diagnostic questions for readiness analysis. |
| 17 | `TechStackLifecycleMonitor` | `src/components/TechStackLifecycleMonitor.tsx` | **Improve** | Operations Workspace | Systems Architect / IT Lead | Software asset end-of-life (EOL) and support lifecycle monitoring widget. |
| 18 | `SlideOver` (Common) | `src/components/common/SlideOver.tsx` | **Merge** | Shared UI Primitives | All Users | Legacy duplicate slide-over component. Merge into `src/components/ui/SlideOver.tsx`. |
| 19 | `EvidenceTimeline` | `src/components/dashboard/EvidenceTimeline.tsx` | **Improve** | Operations Workspace | IT Auditor / SecOps | Chronological timeline component displaying telemetry evidence verification events and logs. |
| 20 | `PersonaContext` | `src/components/dashboard/PersonaContext.tsx` | **Keep** | Shared Infrastructure | All Users | React context provider managing global persona state (Executive vs Technical view mode). |
| 21 | `ReadinessDrivers` | `src/components/dashboard/ReadinessDrivers.tsx` | **Improve** | Business Workspace | VP Ops / IT Director | Component highlighting top positive and negative score drivers impacting clinic readiness. |
| 22 | `TrustScore` | `src/components/dashboard/TrustScore.tsx` | **Keep** | Operations Workspace | Compliance Auditor / CISO | Cryptographic trust and chain-of-custody score indicator card. |
| 23 | `VerificationSummaryGrid` | `src/components/dashboard/VerificationSummaryGrid.tsx` | **Improve** | Operations Workspace | SecOps Analyst / SRE | Grid displaying counts of passed, failed, and pending operational check verifications. |
| 24 | `ConfidenceGauge` | `src/components/evidence/ConfidenceGauge.tsx` | **Keep** | Operations Workspace | SRE / Security Analyst | Statistical confidence gauge reflecting reliability of collected telemetry evidence data. |
| 25 | `DashboardLayout` | `src/components/layout/DashboardLayout.tsx` | **Improve** | Operations / Shared | All Authenticated Users | Refactor into unified `DualWorkspaceLayout` with responsive `UnifiedSidebar`. |
| 26 | `DocsLayout` | `src/components/layout/DocsLayout.tsx` | **Keep** | External / Public Portal | Public Readers / Buyers | Specialized layout wrapper with sidebar navigation for public documentation pages. |
| 27 | `EnvironmentHeader` | `src/components/layout/EnvironmentHeader.tsx` | **Keep** | Shared Layout Shell | All Users / Operators | Header notification bar indicating current deployment environment. |
| 28 | `Footer` | `src/components/layout/Footer.tsx` | **Keep** | External / Public Portal | Public Visitors / Users | Standard footer containing navigation links to documentation, security, and status pages. |
| 29 | `Layout Index` | `src/components/layout/index.ts` | **Keep** | Shared Infrastructure | Frontend Developers | Barrel export file for layout components (`DocsLayout`, `EnvironmentHeader`, `Footer`). |
| 30 | `CoverageModal` | `src/components/readiness/CoverageModal.tsx` | **Improve** | Shared UI Primitives | Executive / IT Director | System coverage detail modal. Add ARIA labelling and dark mode styling. |
| 31 | `ExecutiveQuestionsGrid` | `src/components/readiness/ExecutiveQuestionsGrid.tsx` | **Improve** | Business Workspace | C-Suite / Executive Board | Executive question cards ("Can we open?", "Ransomware safe?"). |
| 32 | `HowWeKnowDrawer` | `src/components/readiness/HowWeKnowDrawer.tsx` | **Improve** | Shared UI Primitives | C-Suite / Technical Lead | Evidence inspection slide-over drawer. Add dark mode classes and raw evidence JSON viewer. |
| 33 | `NorthStarHero` | `src/components/readiness/NorthStarHero.tsx` | **Improve** | Business Workspace | C-Suite / Healthcare Executive | Refactor to support `compact` and `expanded` variants. Add `dark:` CSS tokens. |
| 34 | `ReadinessHeader` | `src/components/readiness/ReadinessHeader.tsx` | **Improve** | Business Workspace | Business Workspace Users | Header title, breadcrumbs, and filter action controls for readiness sub-views. |
| 35 | `ReadinessHistoryTimeline` | `src/components/readiness/ReadinessHistoryTimeline.tsx` | **Improve** | Business Workspace | Compliance Auditor / VP Ops | Historical audit snapshot timeline showing readiness score evolution over time. |
| 36 | `ReadinessSidebar` | `src/components/readiness/ReadinessSidebar.tsx` | **Merge** | Business Workspace | Business Workspace Users | Sub-navigation sidebar for readiness section. Merge items into `UnifiedSidebar`. |
| 37 | `ReadinessStates` | `src/components/readiness/ReadinessStates.tsx` | **Improve** | Business Workspace | All Business Users | Empty (`HealthyState`), loading (`LoadingState`), and error (`ErrorState`) components. |
| 38 | `RecoveryReadinessBanner` | `src/components/readiness/RecoveryReadinessBanner.tsx` | **Improve** | Business Workspace | VP Ops / IT Director | Business continuity status banner. Standardize dark mode tokens. |
| 39 | `StoryActionCard` | `src/components/readiness/StoryActionCard.tsx` | **Improve** | Business Workspace | VP Ops / IT Director | Core readiness card. Support `compact`, `expanded`, and `technical` variants. |
| 40 | `TrustBadge` | `src/components/readiness/TrustBadge.tsx` | **Improve** | Shared UI Primitives | All Users | Refactor for `compact`, `expanded`, and `technical` variants. |
| 41 | `DependenciesTab` | `src/components/technology/DependenciesTab.tsx` | **Keep** | Operations Workspace | Security Engineer / SRE | Tech stack tab displaying software dependency tree and vulnerability exposure. |
| 42 | `ExposureTab` | `src/components/technology/ExposureTab.tsx` | **Keep** | Operations Workspace | SecOps Analyst | Tech stack tab breaking down CVE vulnerability exposure across assets. |
| 43 | `InsightsTab` | `src/components/technology/InsightsTab.tsx` | **Keep** | Operations Workspace | IT Manager / Architect | Tech stack tab presenting automated recommendations and EOL risk insights. |
| 44 | `InventoryTab` | `src/components/technology/InventoryTab.tsx` | **Keep** | Operations Workspace | IT Manager / SecOps | Tech stack tab providing filterable inventory table of hardware and software assets. |
| 45 | `LifecycleTab` | `src/components/technology/LifecycleTab.tsx` | **Keep** | Operations Workspace | Systems Architect | Tech stack tab visualizing asset EOL timelines and vendor support lifecycle status. |
| 46 | `TimelineTab` | `src/components/technology/TimelineTab.tsx` | **Keep** | Operations Workspace | Systems Architect / SRE | Tech stack tab charting asset deployment changes and infrastructure modifications. |
| 47 | `Accordion` | `src/components/ui/Accordion.tsx` | **Keep** | Shared UI Primitives | All Users | Collapsible accordion primitive for expandable content sections. |
| 48 | `ApiDiagnosticsPanel` | `src/components/ui/ApiDiagnosticsPanel.tsx` | **Improve** | Shared Utilities | Developer / SRE | Diagnostic drawer showing live API request/response status and connection state. |
| 49 | `Badge` | `src/components/ui/Badge.tsx` | **Improve** | Shared UI Primitives | All Users | Standardize semantic status colors and size variants. |
| 50 | `Button` | `src/components/ui/Button.tsx` | **Keep** | Shared UI Primitives | All Users | Reusable button primitive. Primary, secondary, danger, and ghost variants. |
| 51 | `Card` | `src/components/ui/Card.tsx` | **Keep** | Shared UI Primitives | All Users | Standard card container primitive with header, body, and footer sub-components. |
| 52 | `EmptyState` | `src/components/ui/EmptyState.tsx` | **Keep** | Shared UI Primitives | All Users | Reusable empty state placeholder component with graphic icon and action button. |
| 53 | `EnvironmentBanner` | `src/components/ui/EnvironmentBanner.tsx` | **Keep** | Shared Utilities | All Users | Environment notification banner component for non-production environments. |
| 54 | `Input` | `src/components/ui/Input.tsx` | **Keep** | Shared UI Primitives | All Users | Standardized text input form field primitive with validation error display. |
| 55 | `Select` | `src/components/ui/Select.tsx` | **Keep** | Shared UI Primitives | All Users | Standardized dropdown select input primitive with custom theme styling. |
| 56 | `Skeleton` | `src/components/ui/Skeleton.tsx` | **Keep** | Shared UI Primitives | All Users | Loading pulse placeholder primitive. Standardize width and height utility props. |
| 57 | `SlideOver` | `src/components/ui/SlideOver.tsx` | **Improve** | Shared UI Primitives | All Users | Slide-over drawer for progressive disclosure. Add keyboard focus management. |
| 58 | `Table` | `src/components/ui/Table.tsx` | **Keep** | Shared UI Primitives | All Users | Data table primitive supporting column headers, striped rows, and status cells. |
| 59 | `Tabs` | `src/components/ui/Tabs.tsx` | **Keep** | Shared UI Primitives | All Users | Tabbed navigation container primitive for switching between sub-views. |
| 60 | `ThemeToggle` | `src/components/ui/ThemeToggle.tsx` | **Keep** | Shared UI Shell | All Users | Dark/light theme mode toggle button component using CSS class strategy. |
| 61 | `Toast` | `src/components/ui/Toast.tsx` | **Keep** | Shared UI Primitives | All Users | Notification toast container. Ensure accessibility compliance. |
| 62 | `Tooltip` | `src/components/ui/Tooltip.tsx` | **Keep** | Shared UI Primitives | All Users | Information hover tooltip. Ensure proper z-index elevation token usage. |
| 63 | `UI Index` | `src/components/ui/index.ts` | **Keep** | Shared Infrastructure | Frontend Developers | Barrel export file re-exporting all UI primitives for clean imports. |
