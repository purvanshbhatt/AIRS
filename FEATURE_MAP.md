# ResilAI Feature Migration Map (`FEATURE_MAP.md`)

**Document Version:** 1.0.0  
**Target Application:** ResilAI Frontend (`P:\projects\AIRS\frontend`)  
**Requirement Mapping:** Requirement R9 (Feature Mapping Matrix) & R3 (Component Preservation)  
**Author:** Milestone 1 Documentation Suite Worker  

---

## 1. Executive Summary

This feature migration map explicitly tracks the transformation of every legacy page, component, feature view, and helper function during the ResilAI frontend refactoring into the **Dual Workspace Architecture**. To ensure zero loss of technical functionality (Requirement **R9**), every legacy component is mapped to its new location with a migration reason, refactoring status (`Preserved`, `Refactored`, `Merged`, `Deprecated`, `New`), target workspace, and target route.

---

## 2. Feature Migration Matrix (R9 Audit)

| Old Component / Feature | New Component / Feature | Migration Reason | Refactoring Status | Target Workspace | Target Location / Route |
|---|---|---|---|---|---|
| `pages/Dashboard.tsx` | Business Dashboard (`TodayPage`) & Operations Overview | Legacy dashboard mixed executive status and technical telemetry. Split into high-level executive readiness and technical graph panels. | **Refactored / Merged** | Business & Operations | `/readiness` (Business) & `/dashboard/operations` (Ops) |
| `pages/EvidenceNetwork.tsx` | `EvidenceNetwork.tsx` | High-value interactive telemetry graph must be preserved intact for security analysts (R3 requirement). | **Preserved** | Operations Workspace | `/dashboard/operations/evidence` |
| `pages/ComplianceDrift.tsx` | `ComplianceDrift.tsx` | Framework regulatory drift tracker (HIPAA, NIST CSF) preserved for compliance officers. | **Preserved** | Operations Workspace | `/dashboard/operations/compliance` |
| `pages/TechnologyIntelligence.tsx` | `TechnologyIntelligence.tsx` | Infrastructure & software asset lifecycle monitor preserved for IT managers. | **Preserved** | Operations Workspace | `/dashboard/operations/technology` |
| `pages/ReliabilityDashboard.tsx` | `ReliabilityDashboard.tsx` | Infrastructure SLA/SLI uptime monitor preserved for SRE and IT ops team. | **Preserved** | Operations Workspace | `/dashboard/operations/reliability` |
| `pages/RemediationLedger.tsx` | `RemediationLedger.tsx` | Security remediation ticket ledger preserved for incident response workflows. | **Preserved** | Operations Workspace | `/dashboard/operations/remediation` |
| `pages/DecisionEngine.tsx` | `DecisionEngine.tsx` | Security ROI investment modeler preserved for IT security leads. | **Preserved** | Operations Workspace | `/dashboard/operations/decision-engine` |
| `pages/AIAttackSimulationLab.tsx` | `AIAttackSimulationLab.tsx` | Red team attack simulation lab preserved and updated with design system tokens. | **Refactored** | Operations Workspace | `/dashboard/operations/simulation` |
| `pages/BoardStory.tsx` | `BoardStory.tsx` | Executive presentation cards moved under Business Workspace reporting. | **Refactored** | Business Workspace | `/dashboard/board-story` |
| `pages/Reports.tsx` | `Reports.tsx` | Report generation and PDF export portal moved under Business Workspace reporting. | **Refactored** | Business Workspace | `/dashboard/reports` |
| `pages/Analytics.tsx` | `Analytics.tsx` | Trend analytics page refactored to consume backend readiness trend objects without client math (R13). | **Refactored** | Operations Workspace | `/dashboard/analytics` |
| `pages/BusinessUnits.tsx` | `BusinessUnits.tsx` | Multi-clinic governance comparison view mapped into Business Workspace. | **Refactored** | Business Workspace | `/dashboard/business-units` |
| `pages/ReadinessTimeline.tsx` | `ActivityPage.tsx` | Consolidated duplicate timeline into unified activity feed (`ActivityPage`). | **Merged** | Business & Operations | `/readiness/activity` |
| `pages/Assessments.tsx` | `Assessments.tsx` | Formal security assessment list view mapped to Operations Workspace. | **Refactored** | Operations Workspace | `/dashboard/assessments` |
| `pages/NewAssessment.tsx` & `QuickAssessment.tsx` | Assessment Creation Wizard (`NewAssessment.tsx`) | Merged redundant assessment creation forms into a unified multi-step wizard. | **Merged** | Operations Workspace | `/dashboard/assessment/new` |
| `pages/Results.tsx` & `ResultsTabs.tsx` | `Results.tsx` | Assessment domain result view refactored to display backend scores without frontend calculation (R13). | **Refactored** | Operations Workspace | `/dashboard/results/:id` |
| `pages/Organizations.tsx` & `NewOrg.tsx` | `Organizations.tsx` & `NewOrg.tsx` | Tenant management pages mapped to Administration Workspace. | **Refactored** | Admin Workspace | `/dashboard/admin/organizations` |
| `pages/GovernanceProfile.tsx` | `GovernanceProfile.tsx` | Risk policy configuration mapped to Administration Workspace. | **Refactored** | Admin Workspace | `/dashboard/admin/governance` |
| `pages/AuditCalendar.tsx` | `AuditCalendar.tsx` | Audit scheduling calendar mapped to Administration Workspace. | **Refactored** | Admin Workspace | `/dashboard/admin/calendar` |
| `pages/Settings.tsx` | `Settings.tsx` & `SettingsPage.tsx` | Global user and system settings consolidated into Admin Workspace. | **Merged** | Admin Workspace | `/dashboard/admin/settings` |
| `pages/AuditorView.tsx` | `AuditorView.tsx` | Read-only auditor evidence view mapped into Admin / Auditor access section. | **Refactored** | Admin Workspace | `/auditor` |
| `pages/clinic/*` (Prototype pages) | Retired Prototype Views | Orphaned prototype pages built before unified readiness model. Superseded by `features/readiness`. | **Deprecated / Retired** | None (Retired) | None (Safely Removed) |
| `components/readiness/NorthStarHero.tsx` | `NorthStarHero.tsx` | Hero banner refactored to support `compact` and `expanded` status variants with dark theme tokens. | **Refactored** | Business Workspace | `/readiness` |
| `components/readiness/StoryActionCard.tsx` | `StoryActionCard.tsx` | Action card refactored to support `compact`, `expanded`, and `technical` variants with 5-tier progressive disclosure. | **Refactored** | Business & Operations | Shared Primitive |
| `components/readiness/ExecutiveQuestionsGrid.tsx` | `ExecutiveQuestionsGrid.tsx` | Grid of 4 core executive questions updated with dark mode styles and drill-down expanders. | **Refactored** | Business Workspace | `/readiness` |
| `components/readiness/RecoveryReadinessBanner.tsx` | `RecoveryReadinessBanner.tsx` | Continuity banner updated with dark theme tokens and connector drill-down triggers. | **Refactored** | Business Workspace | `/readiness/continuity` |
| `components/readiness/TrustBadge.tsx` | `TrustBadge.tsx` | Verification badge updated to support `compact`, `expanded`, and `technical` variant props. | **Refactored** | Shared Primitive | Shared Primitive |
| `components/ResultsTabs.tsx` | `ResultsTabs.tsx` | Refactored to eliminate client-side MITRE/NIST percentage calculations (R13 compliance). | **Refactored** | Operations Workspace | `/dashboard/results/:id` |
| `components/CompetitorParityChart.tsx` | `CompetitorParityChart.tsx` | Refactored to eliminate client-side benchmark math (`industryAvg + 22`) (R13 compliance). | **Refactored** | Business / Operations | Shared Chart Component |
| `hooks/useMockTrustData.ts` | `useDailyReadinessReport` Hook | Deprecated client-side mock trust generator in favor of server-authoritative readiness report hook. | **Deprecated** | Data Hook Layer | `src/api.ts` |
| AI Translator Panel | `AITranslatorPanel.tsx` | **NEW FEATURE** (R4): Interactive panel translating deterministic readiness report into natural language. | **New** | Business Workspace | `/readiness` |
| Dual Workspace Layout | `DualWorkspaceLayout.tsx` | **NEW FEATURE** (R2): Unified layout shell with progressive workspace toggle and sidebar navigation. | **New** | Layout Shell | Global Shell |

---

## 3. Preserved Legacy Features Verification (R3 Guarantee)

The table below explicitly confirms that **zero** legacy operational tools are lost during the refactoring:

```
Legacy Tool                  Remapped Operations Workspace Route            Verification Status
--------------------------------------------------------------------------------------------------
Evidence Network             /dashboard/operations/evidence                 Preserved 100%
Compliance Drift             /dashboard/operations/compliance               Preserved 100%
Technology Intelligence      /dashboard/operations/technology               Preserved 100%
Reliability Dashboard        /dashboard/operations/reliability              Preserved 100%
Remediation Ledger           /dashboard/operations/remediation              Preserved 100%
Decision Engine              /dashboard/operations/decision-engine          Preserved 100%
AI Attack Simulation Lab     /dashboard/operations/simulation               Preserved 100%
```

All 7 legacy operational tools remain fully functional, accessible from the Operations menu group in the unified sidebar, and linked to executive summary cards via progressive disclosure expanders.
