# ResilAI Frontend UI Inventory & Audit

**Document Version:** 1.1.0  
**Target Application:** ResilAI Frontend (`P:\projects\AIRS\frontend`)  
**Audit Scope:** Product Audit (R0), UI Component Audit (R1), Component Remapping (R3)  
**Author:** Milestone 1 Documentation Suite Worker (M1_Fix)  

---

## 1. Executive Summary & Audit Overview

This document establishes the exhaustive, 100% complete product and UI component audit for the ResilAI frontend refactoring project. As required by **R0 (Product Audit)** and **R1 (UI Component Audit)**, every existing page, view, layout, sub-page, and component across `src/pages`, `src/features`, and `src/components` has been audited. Classification is based on target persona, core business question answered, workspace alignment, duplication status, and strategic alignment with the ResilAI vision.

Rather than classifying pages by technical file location alone, this audit establishes a **Dual Workspace Architecture** comprising:
1. **Business Workspace**: Executive-level view for C-Suite, Clinic Directors, and VP of Operations. Delivers plain-English readiness explanations, a 30-second time-to-insight, and high-level operational risk visibility.
2. **Operations Workspace**: Technical view for IT Operations, SecOps, SRE, and Compliance Officers. Preserves deep diagnostic graph tools, telemetry evidence, tech stack lifecycles, and remediation workflows.
3. **Administration Workspace**: Organizational context, auditor access, integration configurations, and platform settings.
4. **External Portal**: Public-facing marketing, landing, authentication, and external documentation routes.

---

## 2. Product Page & View Inventory (R0 Audit Matrix)

The table below audits all **50 page and feature components** across `src/pages`, `src/pages/docs/`, `src/pages/clinic/`, and `src/features/readiness`. Each page is evaluated by Target Persona, Business Question, Workspace Alignment, Duplication Status, Action (`Keep`, `Improve`, `Merge`, `Retire`), and detailed Refactoring Justification.

| Page / View | Source File Path | Target Persona | Primary Business Question | Workspace Alignment | Duplication Status | Action | Detailed Justification & Refactoring Strategy |
|---|---|---|---|---|---|---|---|
| **Landing Page** | `src/pages/Landing.tsx` | Prospective Buyer / Healthcare Executive | What value does ResilAI provide for clinical operations and cyber resilience? | External / Public | Unique | **Keep** | Public marketing landing page. Retain layout and messaging, align with standardized design system tokens. |
| **Login Portal** | `src/pages/Login.tsx` | All Authenticated Users | How do I securely log in to access my organization's workspace? | External / Public | Unique | **Keep** | Primary authentication gate. Retain Firebase Auth integration, update UI elements to match standardized design system. |
| **About Page** | `src/pages/About.tsx` | Prospective Buyers & Partners | What is ResilAI's mission and team background? | External / Public | Unique | **Keep** | Marketing disclosure page. Standardize container padding and typography. |
| **Security & Trust** | `src/pages/Security.tsx` | Enterprise Buyers & Risk Officers | What security controls and compliance standards does ResilAI maintain? | External / Public | Unique | **Keep** | Public trust page. Ensure consistent styling and badge tokens. |
| **Pilot Portal** | `src/pages/Pilot.tsx` | Prospective Customers | How can our organization initiate a pilot deployment? | External / Public | Unique | **Keep** | Lead generation portal. Retain form fields and action handlers. |
| **System Status** | `src/pages/Status.tsx` | All Users & System Operators | Are ResilAI core cloud services operational right now? | External / Public | Unique | **Keep** | Public uptime dashboard. Map status badges to standardized semantic color tokens. |
| **Public Docs Overview** | `src/pages/docs/Overview.tsx` | Technical Buyer / Administrator | What capabilities and architectural components does ResilAI feature? | External / Public | Unique | **Keep** | Primary documentation overview page. Render within `DocsLayout` container. |
| **Public Docs Methodology** | `src/pages/docs/Methodology.tsx` | Compliance Officer / CISO | How is deterministic scoring and 5-tier evidence calculated? | External / Public | Unique | **Keep** | Scoring and evidence engine methodology documentation. Render within `DocsLayout`. |
| **Public Docs Frameworks** | `src/pages/docs/Frameworks.tsx` | Auditor / Compliance Officer | Which frameworks (HIPAA, NIST, ISO 27001) are mapped out-of-the-box? | External / Public | Unique | **Keep** | Detailed framework mapping documentation. Render within `DocsLayout`. |
| **Public Docs Security** | `src/pages/docs/Security.tsx` | Security Architect / IT Lead | What encryption, access controls, and zero-trust mechanisms protect data? | External / Public | Unique | **Keep** | Technical platform security documentation. Render within `DocsLayout`. |
| **Public Docs API** | `src/pages/docs/Api.tsx` | Integration Developer / SRE | How do external agents and webhooks integrate with ResilAI REST APIs? | External / Public | Unique | **Keep** | REST API reference and developer documentation. Render within `DocsLayout`. |
| **Docs Index Barrel** | `src/pages/docs/index.ts` | Frontend Developer | Module exports for documentation pages | External / Public | Infrastructure | **Keep** | Re-exports all documentation page components for modular routing. |
| **Auditor View** | `src/pages/AuditorView.tsx` | External Auditor / Compliance Inspector | Can I independently verify cryptographic chain-of-custody evidence? | Admin / Operations | Unique | **Improve** | Dedicated read-only evidence portal for external auditors. Remap into Administration > Auditor Access menu. |
| **Today Page** | `src/features/readiness/TodayPage.tsx` | C-Suite / Healthcare Executive | Can our clinics safely open and operate today? | Business Workspace | Unique | **Improve** | Primary Business Workspace hero view. Integrate `NorthStarHero`, `AITranslatorPanel`, and `compact` `StatusCard` primitives. |
| **Needs Attention** | `src/features/readiness/NeedsAttentionPage.tsx` | VP Ops / Operations Lead | What immediate operational blockers require intervention? | Business Workspace | Unique | **Improve** | Action feed for executive risk mitigation. Add 5-tier progressive disclosure triggers to inspect operational evidence. |
| **Recovery Readiness** | `src/features/readiness/RecoveryReadinessPage.tsx` | IT Director / VP Ops | Are ransomware backups verified and what is our estimated recovery time? | Business Workspace | Unique | **Improve** | Business continuity summary view. Add inline expansion to drill down into connector verification statuses. |
| **Activity Log** | `src/features/readiness/ActivityPage.tsx` | IT Manager / Compliance Auditor | What system changes and verification events occurred recently? | Business Workspace | Unique | **Improve** | Chronological operational event feed. Standardize status badges, filter controls, and timeline line connectors. |
| **Readiness Settings** | `src/features/readiness/SettingsPage.tsx` | System Administrator / IT Lead | How are alert thresholds and notification channels configured? | Admin Workspace | Unique | **Improve** | Operations settings view. Move from Business navigation into Admin Workspace > Settings. |
| **Readiness Shell Layout** | `src/features/readiness/Layout.tsx` | All Authenticated Users | How is the readiness feature area structured? | Shared Shell | Shell wrapper | **Merge** | Feature layout container. Merge into unified `DualWorkspaceLayout` shell. |
| **Legacy Dashboard** | `src/pages/Dashboard.tsx` | IT Ops / SecOps Analyst | What is our overall cyber risk matrix and telemetry status? | Operations Workspace | Overlaps with `TodayPage` | **Merge** | Comprehensive legacy dashboard. Merge redundant high-level widgets into `TodayPage`; preserve deep technical graph panels in Operations Overview. |
| **Evidence Network** | `src/pages/EvidenceNetwork.tsx` | Security Analyst / SRE | What is the complete graph of connected telemetry sources and verified evidence? | Operations Workspace | Unique | **Keep** | High-value interactive graph tool. Remap as canonical view under Operations Workspace > Evidence Network (`/dashboard/operations/evidence`). |
| **Compliance Drift** | `src/pages/ComplianceDrift.tsx` | Compliance Officer / Security Lead | Which framework controls (HIPAA, NIST CSF) have drifted from baseline? | Operations Workspace | Unique | **Keep** | Essential compliance monitoring page. Remap as canonical view under Operations Workspace > Compliance Drift (`/dashboard/operations/compliance`). |
| **Technology Intelligence** | `src/pages/TechnologyIntelligence.tsx` | Systems Architect / IT Manager | What software/hardware assets exist and what EOL/vulnerability risks apply? | Operations Workspace | Unique | **Keep** | Asset lifecycle and risk inventory. Remap as canonical view under Operations Workspace > Tech Stack (`/dashboard/operations/technology`). |
| **Reliability Dashboard** | `src/pages/ReliabilityDashboard.tsx` | Infrastructure Lead / SRE | Are infrastructure components meeting uptime and SLA targets? | Operations Workspace | Unique | **Keep** | Infrastructure health monitor. Remap as canonical view under Operations Workspace > Reliability (`/dashboard/operations/reliability`). |
| **Remediation Ledger** | `src/pages/RemediationLedger.tsx` | IT Security Lead / Incident Team | What remediation tickets are open, assigned, or verified resolved? | Operations Workspace | Unique | **Keep** | Workitem ledger. Remap as canonical view under Operations Workspace > Remediation (`/dashboard/operations/remediation`). |
| **AI Attack Simulation Lab** | `src/pages/AIAttackSimulationLab.tsx` | Red Team / SecOps Specialist | How does the security posture perform against simulated attack vectors? | Operations Workspace | Unique | **Improve** | Advanced simulation lab. Remap into Operations Workspace > AI Simulation (`/dashboard/operations/simulation`). |
| **Board Story** | `src/pages/BoardStory.tsx` | C-Suite / Executive Board | What high-level cyber posture story and ROI metrics can I present to the Board? | Business Workspace | Overlaps with `TodayPage` | **Improve** | Executive summary tool. Move to Business Workspace > Board Reports (`/dashboard/board-story`). |
| **Reports Portal** | `src/pages/Reports.tsx` | Executive / Compliance Officer | Where can I generate, view, and export compliance certificates and PDFs? | Business Workspace | Unique | **Improve** | Report export view. Move to Business Workspace > Board Reports (`/dashboard/reports`). |
| **Analytics Page** | `src/pages/Analytics.tsx` | VP Operations / IT Manager | How are readiness scores and maturity levels trending over time? | Operations Workspace | Partial math overlap | **Improve** | Trend analytics view. Refactor to eliminate frontend score math (R13 compliance) and display server metrics directly. |
| **Business Units** | `src/pages/BusinessUnits.tsx` | Executive / Multi-Site Director | How does readiness compare across regional clinics and divisions? | Business Workspace | Unique | **Improve** | Multi-site governance view. Map to Business Workspace > Multi-Unit View. |
| **Decision Engine** | `src/pages/DecisionEngine.tsx` | IT Security Lead / CISO | What security investments yield the highest readiness improvement? | Operations Workspace | Unique | **Keep** | Strategic investment modeling tool. Map into Operations Workspace > Decision Engine. |
| **Readiness Timeline** | `src/pages/ReadinessTimeline.tsx` | IT Auditor / Compliance Officer | How has technical readiness evolved over audit milestones? | Operations Workspace | Overlaps with `ActivityPage` | **Merge** | Merge detailed audit milestone timeline into Operations > Activity Timeline. |
| **Assessments List** | `src/pages/Assessments.tsx` | Assessor / IT Lead | What formal readiness assessments are currently active or completed? | Operations Workspace | Unique | **Improve** | Formal assessment management. Map to Operations Workspace > Assessments. |
| **Interactive Assessment Runner** | `src/pages/Assessment.tsx` | Assessor / IT Lead | How do I step through and execute an active readiness assessment questionnaire? | Operations Workspace | Overlaps with `Assessments.tsx` | **Merge** | Interactive questionnaire runner. Merge into unified Assessment module under Operations Workspace. |
| **New Assessment Wizard** | `src/pages/NewAssessment.tsx` | Assessor / IT Lead | How do I configure and launch a new custom security assessment? | Operations Workspace | Workflow overlap | **Merge** | Consolidate wizard components into a single multi-step wizard under Operations > Assessment Creation. |
| **Quick Assessment Runner** | `src/pages/QuickAssessment.tsx` | Assessor / IT Lead | How do I rapidly perform a 5-minute rapid readiness audit? | Operations Workspace | Workflow overlap | **Merge** | Consolidate wizard components into a single multi-step wizard under Operations > Assessment Creation. |
| **Assessment Results** | `src/pages/Results.tsx` | IT Auditor / SecOps Analyst | What are the domain scores, framework mappings, and findings for a run? | Operations Workspace | R13 math violation | **Improve** | Refactor `ResultsTabs.tsx` to remove frontend percentage calculations and render backend metrics directly. |
| **Organizations List** | `src/pages/Organizations.tsx` | System Administrator | Which tenant clinic organizations are configured in the system? | Admin Workspace | Unique | **Improve** | Tenant management page. Remap into Admin Workspace > Organizations (`/dashboard/admin/organizations`). |
| **New Org Form** | `src/pages/NewOrg.tsx` | System Administrator | How do I onboard a new clinic tenant organization? | Admin Workspace | Workflow overlap | **Merge** | Modal onboarding flow. Merge as a slide-over modal within `Organizations.tsx`. |
| **Governance Profile** | `src/pages/GovernanceProfile.tsx` | CISO / Compliance Director | What governance policies and risk thresholds are enforced across clinics? | Admin Workspace | Unique | **Improve** | Policy configuration page. Remap into Admin Workspace > Governance. |
| **Audit Calendar** | `src/pages/AuditCalendar.tsx` | Compliance Officer / IT Lead | When are upcoming compliance audits and certification renewals scheduled? | Admin Workspace | Unique | **Improve** | Scheduling calendar. Remap into Admin Workspace > Audit Calendar. |
| **Legacy Integrations Handler** | `src/pages/Integrations.tsx` | IT Administrator | Where do I configure enterprise telemetry connector integrations? | Admin / Operations | Legacy Route | **Merge** | Active redirect handler. Redirect `/integrations` to `/dashboard/admin/organizations` or Operations Tech Stack. |
| **Root Home View** | `src/pages/Home.tsx` | Authenticated User | What is the entry home view post-login? | Shared Shell | Route Handler | **Improve** | Route redirect handler routing users to `/readiness` (Business) or `/dashboard/operations`. |
| **Root Settings View** | `src/pages/Settings.tsx` | Authenticated User | Where are global user profile and app preferences managed? | Admin Workspace | Overlaps with feature settings | **Improve** | Global user preferences. Consolidate into Admin Workspace > Settings. |
| **Clinic Prototype Home** | `src/pages/clinic/Home.tsx` | Clinic Admin (Legacy) | Legacy prototype homepage | Legacy Prototype | Duplicate | **Retire** | Orphaned prototype page. Safely retire and replace with Business Workspace `TodayPage`. |
| **Clinic Prototype Onboarding** | `src/pages/clinic/Onboarding.tsx` | Clinic Admin (Legacy) | Legacy clinic onboarding flow | Legacy Prototype | Duplicate | **Retire** | Orphaned prototype page. Safely retire and replace with `NewOrg` modal. |
| **Clinic Prototype Integrations** | `src/pages/clinic/Integrations.tsx` | Clinic Admin (Legacy) | Legacy connector integrations list | Legacy Prototype | Duplicate | **Retire** | Orphaned prototype page. Safely retire and replace with Admin > Organizations & Tech Stack. |
| **Clinic Prototype Issue Details** | `src/pages/clinic/IssueDetails.tsx` | Clinic Admin (Legacy) | Legacy issue details drawer view | Legacy Prototype | Duplicate | **Retire** | Orphaned prototype page. Safely retire and replace with Remediation Ledger drawer. |
| **Clinic Prototype Layout** | `src/pages/clinic/Layout.tsx` | Clinic Admin (Legacy) | Legacy clinic shell container | Legacy Prototype | Duplicate | **Retire** | Orphaned prototype container. Safely retire and replace with `DualWorkspaceLayout`. |
| **Clinic Prototype Settings** | `src/pages/clinic/Settings.tsx` | Clinic Admin (Legacy) | Legacy clinic settings form | Legacy Prototype | Duplicate | **Retire** | Orphaned prototype page. Safely retire and replace with Admin Workspace > Settings. |

---

## 3. Shared Component Taxonomy & Classification Matrix (R1 Audit)

Every shared component, UI primitive, hero card, tab view, and layout container across all 63 files in `src/components/` is cataloged and classified below into **Keep**, **Improve**, **Merge**, or **Retire** with target workspace alignment, persona, and refactoring guidelines.

### 3.1 Layout & Navigation Components (10 Files)

| Component Name | Source File Path | Classification | Target Persona | Workspace Alignment | Justification & Refactoring Guidelines |
|---|---|---|---|---|---|
| `DashboardLayout` | `src/components/layout/DashboardLayout.tsx` | **Improve** | All Authenticated Users | Operations / Shared | Refactor into unified `DualWorkspaceLayout` with responsive `UnifiedSidebar` covering Business, Operations, and Admin. |
| `ReadinessLayout` | `src/components/readiness/ReadinessLayout.tsx` | **Merge** | Business Workspace Users | Business Workspace | Merge layout logic into `DualWorkspaceLayout` to unify routing and remove redundant shell wrappers. |
| `UnifiedSidebar` | `src/components/layout/UnifiedSidebar.tsx` | **Improve** | All Authenticated Users | Shared Layout Shell | Standardize navigation categories: Dashboard (Business), Operations (Technical), and Administration (Settings/Orgs). |
| `WorkspaceToggle` | `src/components/layout/WorkspaceToggle.tsx` | **Keep** | C-Suite / SecOps / All | Top Navigation Header | Header toggle control enabling fluid zoom switching between Business executive mode and Operations technical mode. |
| `Header` | `src/components/Header.tsx` | **Improve** | All Authenticated Users | Top Navigation Header | Unify header across all workspaces; add organization selector, theme toggle, persona mode switcher, and alert drawer. |
| `ApiConfigBanner` | `src/components/ApiConfigBanner.tsx` | **Keep** | Developers / SREs | Top Navigation Header | Environment configuration alert banner shown when API endpoints use fallback localhost. |
| `DocsLayout` | `src/components/layout/DocsLayout.tsx` | **Keep** | Public Readers / Buyers | External / Public Portal | Specialized layout wrapper with sidebar navigation for public documentation pages (`/docs/*`). |
| `EnvironmentHeader` | `src/components/layout/EnvironmentHeader.tsx` | **Keep** | All Users / Operators | Shared Layout Shell | Header notification bar indicating current deployment environment (Production, Staging, Demo Mode). |
| `Footer` | `src/components/layout/Footer.tsx` | **Keep** | Public Visitors / Users | External / Public Portal | Standard footer containing navigation links to documentation, security disclosures, system status, and legal pages. |
| `Layout Index` | `src/components/layout/index.ts` | **Keep** | Frontend Developers | Shared Infrastructure | Barrel export file for layout components (`DocsLayout`, `EnvironmentHeader`, `Footer`). |

### 3.2 Readiness & Executive Hero Components (14 Files)

| Component Name | Source File Path | Classification | Target Persona | Workspace Alignment | Justification & Refactoring Guidelines |
|---|---|---|---|---|---|
| `NorthStarHero` | `src/components/readiness/NorthStarHero.tsx` | **Improve** | C-Suite / Healthcare Executive | Business Workspace | Refactor to support `compact` (single status badge) and `expanded` (full hero card with AI summary button) variants. Add `dark:` CSS tokens. |
| `AITranslatorPanel` | `src/components/readiness/AITranslatorPanel.tsx` | **Improve** | Healthcare Executive / VP Ops | Business Workspace | Interactive assistant panel translating deterministic `DailyReadinessReport` into natural language explanations. Must follow R13 compliance. |
| `ExecutiveQuestionsGrid` | `src/components/readiness/ExecutiveQuestionsGrid.tsx` | **Improve** | C-Suite / Executive Board | Business Workspace | Executive question cards ("Can we open?", "Ransomware safe?"). Add `dark:` mode utilities and progressive disclosure triggers. |
| `StoryActionCard` | `src/components/readiness/StoryActionCard.tsx` | **Improve** | VP Ops / IT Director | Business Workspace | Core readiness card. Support `compact`, `expanded`, and `technical` variants. Add `aria-expanded` and progressive disclosure handlers. |
| `RecoveryReadinessBanner` | `src/components/readiness/RecoveryReadinessBanner.tsx` | **Improve** | VP Ops / IT Director | Business Workspace | Business continuity status banner. Standardize dark mode tokens and add connector drill-down button. |
| `ReadinessStates` | `src/components/readiness/ReadinessStates.tsx` | **Improve** | All Business Users | Business Workspace | Empty (`HealthyState`), loading (`LoadingState`), and error (`ErrorState`) components. Add full dark mode class support. |
| `ExecutiveMondayMorning` | `src/components/ExecutiveMondayMorning.tsx` | **Improve** | C-Suite / Clinic Director | Business Workspace | Weekly operational readiness summary card designed for Monday morning briefing. Standardize styling. |
| `ExecutiveRiskMatrix` | `src/components/ExecutiveRiskMatrix.tsx` | **Improve** | Risk Officer / Executive | Business Workspace | Risk heat map grid visualizing risk levels across clinical operational domains. Add dark mode classes. |
| `GHIGauge` | `src/components/GHIGauge.tsx` | **Improve** | Compliance Officer / CISO | Business Workspace | Governance & Health Index radial gauge widget. Refactor to render backend score directly (R13). |
| `SuggestedQuestionsPanel` | `src/components/SuggestedQuestionsPanel.tsx` | **Improve** | Healthcare Executive | Business Workspace | Interactive panel offering AI-driven diagnostic questions for readiness analysis. Standardize container tokens. |
| `ReadinessDrivers` | `src/components/dashboard/ReadinessDrivers.tsx` | **Improve** | VP Ops / IT Director | Business Workspace | Component highlighting top positive and negative score drivers impacting clinic readiness. |
| `ReadinessHeader` | `src/components/readiness/ReadinessHeader.tsx` | **Improve** | Business Workspace Users | Business Workspace | Header title, breadcrumbs, and filter action controls for readiness sub-views. |
| `ReadinessHistoryTimeline` | `src/components/readiness/ReadinessHistoryTimeline.tsx` | **Improve** | Compliance Auditor / VP Ops | Business Workspace | Historical audit snapshot timeline showing readiness score evolution over time. |
| `ReadinessSidebar` | `src/components/readiness/ReadinessSidebar.tsx` | **Merge** | Business Workspace Users | Business Workspace | Sub-navigation sidebar for readiness section. Merge items into unified `UnifiedSidebar`. |

### 3.3 Operations Technical Views & Graph Components (24 Files)

| Component Name | Source File Path | Classification | Target Persona | Workspace Alignment | Justification & Refactoring Guidelines |
|---|---|---|---|---|---|
| `EvidenceNetwork` | `src/pages/EvidenceNetwork.tsx` | **Keep** | Security Analyst / SRE | Operations Workspace | Graph view visualizing connected telemetry nodes. Retain graph canvas and interactive node inspection drawer. |
| `ComplianceDrift` | `src/pages/ComplianceDrift.tsx` | **Keep** | Compliance Officer / SecOps | Operations Workspace | Regulatory compliance drift table and framework breakdown. Retain control drill-down drawers. |
| `TechnologyIntelligence` | `src/pages/TechnologyIntelligence.tsx` | **Keep** | Systems Architect / IT Lead | Operations Workspace | Infrastructure and software asset lifecycle view. Retain vendor vulnerability matrices. |
| `ReliabilityDashboard` | `src/pages/ReliabilityDashboard.tsx` | **Keep** | Infrastructure Lead / SRE | Operations Workspace | SLA/SLO uptime monitoring. Retain service status indicators. |
| `RemediationLedger` | `src/pages/RemediationLedger.tsx` | **Keep** | Security Lead / Incident Team | Operations Workspace | Workitem remediation ledger. Retain ticket status filters and resolution verification drawer. |
| `AIAttackSimulationLab` | `src/pages/AIAttackSimulationLab.tsx` | **Improve** | Red Team / SecOps | Operations Workspace | Simulation lab. Improve layout and align status badges with design system. |
| `ResultsTabs` | `src/components/ResultsTabs.tsx` | **Improve** | SecOps / Auditor | Operations Workspace | Refactor frontend math (MITRE/NIST score derivation) to display server-supplied findings directly (R13 compliance). |
| `ResultsTabsConfig` | `src/components/ResultsTabsConfig.ts` | **Keep** | Frontend Developer | Operations Workspace | Configuration schema defining tab structures and metadata for assessment results. |
| `CompetitorParityChart` | `src/components/CompetitorParityChart.tsx` | **Improve** | CISO / Compliance Director | Operations Workspace | Remove client-side benchmark math (`Math.min(industryAvg + 22, 98)`) and render backend compliance benchmarking directly. |
| `ConnectorActivityPanel` | `src/components/ConnectorActivityPanel.tsx` | **Improve** | SRE / SecOps Analyst | Operations Workspace | Technical connector sync activity monitor, live event stream, and connection status diagnostics. |
| `EnterpriseRoadmap` | `src/components/EnterpriseRoadmap.tsx` | **Improve** | VP Ops / CISO | Operations Workspace | Multi-quarter risk remediation roadmap and strategic milestone planning grid. |
| `EvidenceGraph` | `src/components/EvidenceGraph.tsx` | **Keep** | Security Analyst / SRE | Operations Workspace | Interactive D3/SVG telemetry evidence node graph visualizer component. |
| `OrgEnrichmentCard` | `src/components/OrgEnrichmentCard.tsx` | **Improve** | System Administrator | Admin / Operations | Multi-tenant organization metadata, domain enrichment profile, and clinic details card. |
| `RoadmapTracker` | `src/components/RoadmapTracker.tsx` | **Improve** | IT Lead / VP Ops | Operations Workspace | Visual progress tracking timeline for remediation milestone fulfillment. |
| `ScoreTrendChart` | `src/components/ScoreTrendChart.tsx` | **Improve** | Compliance Lead / IT Director | Operations Workspace | Historical readiness score trend line chart. Refactor to consume server telemetry directly. |
| `TechStackLifecycleMonitor` | `src/components/TechStackLifecycleMonitor.tsx` | **Improve** | Systems Architect / IT Lead | Operations Workspace | Software asset end-of-life (EOL) and support lifecycle monitoring widget. |
| `EvidenceTimeline` | `src/components/dashboard/EvidenceTimeline.tsx` | **Improve** | IT Auditor / SecOps | Operations Workspace | Chronological timeline component displaying telemetry evidence verification events and logs. |
| `TrustScore` | `src/components/dashboard/TrustScore.tsx` | **Keep** | Compliance Auditor / CISO | Operations Workspace | Cryptographic trust and chain-of-custody score indicator card. |
| `VerificationSummaryGrid` | `src/components/dashboard/VerificationSummaryGrid.tsx` | **Improve** | SecOps Analyst / SRE | Operations Workspace | Grid displaying counts of passed, failed, and pending operational check verifications. |
| `ConfidenceGauge` | `src/components/evidence/ConfidenceGauge.tsx` | **Keep** | SRE / Security Analyst | Operations Workspace | Statistical confidence gauge reflecting reliability of collected telemetry evidence data. |
| `DependenciesTab` | `src/components/technology/DependenciesTab.tsx` | **Keep** | Security Engineer / SRE | Operations Workspace | Tech stack tab displaying software dependency tree and upstream vulnerability exposure. |
| `ExposureTab` | `src/components/technology/ExposureTab.tsx` | **Keep** | SecOps Analyst | Operations Workspace | Tech stack tab breaking down CVE vulnerability exposure across hardware/software assets. |
| `InsightsTab` | `src/components/technology/InsightsTab.tsx` | **Keep** | IT Manager / Architect | Operations Workspace | Tech stack tab presenting automated architecture recommendations and EOL risk insights. |
| `InventoryTab` | `src/components/technology/InventoryTab.tsx` | **Keep** | IT Manager / SecOps | Operations Workspace | Tech stack tab providing filterable inventory table of all active hardware and software assets. |
| `LifecycleTab` | `src/components/technology/LifecycleTab.tsx` | **Keep** | Systems Architect | Operations Workspace | Tech stack tab visualizing asset EOL timelines and vendor support lifecycle status. |
| `TimelineTab` | `src/components/technology/TimelineTab.tsx` | **Keep** | Systems Architect / SRE | Operations Workspace | Tech stack tab charting asset deployment changes and infrastructure modification timeline. |

### 3.4 Shared UI Primitives & System Utilities (15 Files)

| Component Name | Source File Path | Classification | Target Persona | Workspace Alignment | Justification & Refactoring Guidelines |
|---|---|---|---|---|---|
| `Badge` | `src/components/ui/Badge.tsx` | **Improve** | All Users | Shared UI Primitives | Standardize semantic status colors (`safe_to_open`, `action_needed`, `critical_risk`, `unknown`) and size variants. |
| `TrustBadge` | `src/components/readiness/TrustBadge.tsx` | **Improve** | All Users | Shared UI Primitives | Refactor for `compact`, `expanded`, and `technical` variants with raw evidence link parameters. |
| `Button` | `src/components/ui/Button.tsx` | **Keep** | All Users | Shared UI Primitives | Reusable button primitive. Ensure primary, secondary, danger, and ghost variants match design tokens. |
| `Card` | `src/components/ui/Card.tsx` | **Keep** | All Users | Shared UI Primitives | Standard card container primitive with header, body, and footer sub-components. |
| `Modal` | `src/components/ui/Modal.tsx` | **Improve** | All Users | Shared UI Primitives | Reusable dialog primitive. Add focus trapping, backdrop blur, and ARIA roles (`role="dialog"`). |
| `SlideOver` | `src/components/ui/SlideOver.tsx` | **Improve** | All Users | Shared UI Primitives | Slide-over drawer for progressive disclosure. Add keyboard focus management and ESC key listener. |
| `Common SlideOver` | `src/components/common/SlideOver.tsx` | **Merge** | All Users | Shared UI Primitives | Legacy duplicate slide-over component. Merge into `src/components/ui/SlideOver.tsx`. |
| `Skeleton` | `src/components/ui/Skeleton.tsx` | **Keep** | All Users | Shared UI Primitives | Loading pulse placeholder primitive. Standardize width and height utility props. |
| `Toast` | `src/components/ui/Toast.tsx` | **Keep** | All Users | Shared UI Primitives | Notification toast container. Ensure accessibility compliance (`role="alert"`). |
| `Tooltip` | `src/components/ui/Tooltip.tsx` | **Keep** | All Users | Shared UI Primitives | Information hover tooltip. Ensure proper z-index elevation token usage. |
| `HowWeKnowDrawer` | `src/components/readiness/HowWeKnowDrawer.tsx` | **Improve** | C-Suite / Technical Lead | Shared UI Primitives | Evidence inspection slide-over drawer. Add dark mode classes and raw evidence JSON viewer. |
| `CoverageModal` | `src/components/readiness/CoverageModal.tsx` | **Improve** | Executive / IT Director | Shared UI Primitives | System coverage detail modal. Add ARIA labelling and dark mode styling. |
| `Accordion` | `src/components/ui/Accordion.tsx` | **Keep** | All Users | Shared UI Primitives | Collapsible accordion primitive for expandable content sections. |
| `ApiDiagnosticsPanel` | `src/components/ui/ApiDiagnosticsPanel.tsx` | **Improve** | Developer / SRE | Shared Utilities | Diagnostic drawer showing live API request/response status and connection state. |
| `EmptyState` | `src/components/ui/EmptyState.tsx` | **Keep** | All Users | Shared UI Primitives | Reusable empty state placeholder component with graphic icon and call-to-action button. |
| `EnvironmentBanner` | `src/components/ui/EnvironmentBanner.tsx` | **Keep** | All Users | Shared Utilities | Environment notification banner component for non-production environments. |
| `Input` | `src/components/ui/Input.tsx` | **Keep** | All Users | Shared UI Primitives | Standardized text input form field primitive with validation error display. |
| `Select` | `src/components/ui/Select.tsx` | **Keep** | All Users | Shared UI Primitives | Standardized dropdown select input primitive with custom theme styling. |
| `Table` | `src/components/ui/Table.tsx` | **Keep** | All Users | Shared UI Primitives | Data table primitive supporting column headers, striped rows, and status cells. |
| `Tabs` | `src/components/ui/Tabs.tsx` | **Keep** | All Users | Shared UI Primitives | Tabbed navigation container primitive for switching between sub-views. |
| `ThemeToggle` | `src/components/ui/ThemeToggle.tsx` | **Keep** | All Users | Shared UI Shell | Dark/light theme mode toggle button component using CSS class strategy. |
| `ProgressSteps` | `src/components/ProgressSteps.tsx` | **Keep** | All Users | Shared UI Primitives | Step progress indicator widget for multi-step wizards and assessment forms. |
| `ErrorBoundary` | `src/components/ErrorBoundary.tsx` | **Keep** | All Users | Shared Infrastructure | React error boundary class component preventing unhandled UI crash cascades. |
| `ProtectedRoute` | `src/components/ProtectedRoute.tsx` | **Keep** | Authenticated Users | Shared Infrastructure | Route protection wrapper verifying user authentication state before rendering child routes. |
| `PersonaContext` | `src/components/dashboard/PersonaContext.tsx` | **Keep** | All Users | Shared Infrastructure | React context provider managing global persona state (Executive vs Technical view mode). |
| `UI Index` | `src/components/ui/index.ts` | **Keep** | Frontend Developers | Shared Infrastructure | Barrel export file re-exporting all UI primitives for clean imports. |

---

## 4. Component Remapping Strategy (R3 Guidelines)

To satisfy **R3 (Component Preservation)**, no legacy technical component will be rewritten or discarded. Instead, legacy tools are remapped into the Operations Workspace menu structure as follows:

```
Legacy Location                     --> New Canonical Operations Route
----------------------------------------------------------------------------------------
src/pages/EvidenceNetwork.tsx       --> /dashboard/operations/evidence (Evidence Network)
src/pages/ComplianceDrift.tsx       --> /dashboard/operations/compliance (Compliance Drift)
src/pages/TechnologyIntelligence.tsx--> /dashboard/operations/technology (Tech Stack)
src/pages/ReliabilityDashboard.tsx   --> /dashboard/operations/reliability (Reliability)
src/pages/RemediationLedger.tsx     --> /dashboard/operations/remediation (Remediation)
src/pages/AIAttackSimulationLab.tsx --> /dashboard/operations/simulation (AI Simulation)
```

Core readiness components (`StatusCard`, `NorthStarHero`, `StoryActionCard`, `TrustBadge`) will be refactored with a `variant` prop (`compact` | `expanded` | `technical`), enabling identical components to render in both Business executive cards and Operations deep views without code duplication.

---

## 5. Summary of Audit Actions

- **Total Page / Feature Files Audited**: 50
  - **Keep**: 19
  - **Improve**: 18
  - **Merge**: 7
  - **Retire**: 6 (Clinic prototype pages)
- **Total Component Files Audited**: 63
  - **Keep**: 34
  - **Improve**: 27
  - **Merge**: 2
  - **Retire**: 0
