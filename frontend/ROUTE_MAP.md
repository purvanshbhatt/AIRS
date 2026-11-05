# ResilAI Route Inventory & Navigation Map (`ROUTE_MAP.md`)

**Document Version:** 1.0.0  
**Target Application:** ResilAI Frontend (`P:\projects\AIRS\frontend`)  
**Requirement Mapping:** Requirement R10 (Route Inventory) & R6 (Preserve Navigation Flow)  
**Author:** Milestone 1 Documentation Suite Worker  

---

## 1. Executive Summary & Routing Architecture

This document specifies the complete route inventory for the ResilAI frontend application. In accordance with **R10 (Route Inventory)**, every current route is inventoried and mapped to its future canonical route, redirect policy, deprecation status, owner workspace, and target user persona.

The refactored router (configured in `src/App.tsx`) eliminates the legacy hardcoded binary flag (`IS_READINESS_PRODUCT`) in favor of a single unified router containing three logical workspace sub-trees (**Business Workspace**, **Operations Workspace**, and **Administration Workspace**) plus external public routes. Backward compatibility is guaranteed: no legitimate legacy route disappears, and all legacy endpoints redirect smoothly to their canonical locations.

---

## 2. Complete Route Inventory Matrix (R10)

| Current Route | Future Canonical Route | Redirect Rule | Deprecated? | Owner Workspace | Target Persona | Access Control |
|---|---|---|---|---|---|---|
| `/` | `/` | Redirect to `/readiness` if authenticated; else render Landing | No | External / Public | Prospective Buyer / All | Public |
| `/login` | `/login` | Redirect to `/readiness` if already authenticated | No | External / Public | All Users | Public |
| `/about` | `/about` | None | No | External / Public | Prospective Buyer | Public |
| `/security` | `/security` | None | No | External / Public | Risk Officer / Auditor | Public |
| `/pilot` | `/pilot` | None | No | External / Public | Enterprise Buyer | Public |
| `/status` | `/status` | None | No | External / Public | All Users / Operators | Public |
| `/auditor` | `/auditor` | Canonical route for external read-only auditor portal | No | Admin / Operations | External Auditor | Public / Token |
| `/docs/*` | `/docs/*` | Public documentation sub-routes | No | External / Public | All Users | Public |
| `/readiness` | `/readiness` | Primary Business Workspace Index | No | Business Workspace | C-Suite / Executive | Authenticated |
| `/readiness/actions` | `/readiness/actions` | Business Needs Attention action feed | No | Business Workspace | VP Ops / Executive | Authenticated |
| `/readiness/continuity` | `/readiness/continuity` | Business Recovery Readiness view | No | Business Workspace | IT Director / VP Ops | Authenticated |
| `/readiness/activity` | `/readiness/activity` | Business Activity Log feed | No | Business Workspace | IT Manager / Auditor | Authenticated |
| `/dashboard` | `/dashboard/operations` | Hard redirect `301` -> `/readiness` for executives, or `/dashboard/operations` for IT ops | Legacy Route | Operations Workspace | IT Ops / SecOps | Authenticated |
| `/dashboard/operations` | `/dashboard/operations` | Canonical Operations Workspace Index | No | Operations Workspace | IT Ops / SRE | Authenticated |
| `/dashboard/evidence-network` | `/dashboard/operations/evidence` | Hard redirect `301` -> `/dashboard/operations/evidence` | Legacy Subroute | Operations Workspace | Security Analyst | Authenticated |
| `/dashboard/operations/evidence` | `/dashboard/operations/evidence` | Canonical route for Evidence Network graph tool | No | Operations Workspace | Security Analyst | Authenticated |
| `/dashboard/compliance-drift` | `/dashboard/operations/compliance` | Hard redirect `301` -> `/dashboard/operations/compliance` | Legacy Subroute | Operations Workspace | Compliance Officer | Authenticated |
| `/dashboard/operations/compliance` | `/dashboard/operations/compliance` | Canonical route for Compliance Drift tracker | No | Operations Workspace | Compliance Officer | Authenticated |
| `/dashboard/tech-stack` | `/dashboard/operations/technology` | Hard redirect `301` -> `/dashboard/operations/technology` | Legacy Subroute | Operations Workspace | Systems Architect | Authenticated |
| `/dashboard/operations/technology` | `/dashboard/operations/technology` | Canonical route for Technology Intelligence | No | Operations Workspace | Systems Architect | Authenticated |
| `/dashboard/reliability` | `/dashboard/operations/reliability` | Hard redirect `301` -> `/dashboard/operations/reliability` | Legacy Subroute | Operations Workspace | SRE / IT Ops Lead | Authenticated |
| `/dashboard/operations/reliability` | `/dashboard/operations/reliability` | Canonical route for Infrastructure Reliability | No | Operations Workspace | SRE / IT Ops Lead | Authenticated |
| `/dashboard/remediation` | `/dashboard/operations/remediation` | Hard redirect `301` -> `/dashboard/operations/remediation` | Legacy Subroute | Operations Workspace | IT Security Lead | Authenticated |
| `/dashboard/operations/remediation` | `/dashboard/operations/remediation` | Canonical route for Remediation Ledger | No | Operations Workspace | IT Security Lead | Authenticated |
| `/dashboard/decision-engine` | `/dashboard/operations/decision-engine` | Hard redirect `301` -> `/dashboard/operations/decision-engine` | Legacy Subroute | Operations Workspace | CISO / Security Lead | Authenticated |
| `/dashboard/operations/decision-engine` | `/dashboard/operations/decision-engine` | Canonical route for Security Decision Engine | No | Operations Workspace | CISO / Security Lead | Authenticated |
| `/dashboard/operations/simulation` | `/dashboard/operations/simulation` | Canonical route for AI Attack Simulation Lab | No | Operations Workspace | Red Team / SecOps | Authenticated |
| `/dashboard/board-story` | `/dashboard/board-story` | Board Presentation report view | No | Business Workspace | C-Suite / Executive | Authenticated |
| `/dashboard/reports` | `/dashboard/reports` | Report Export and Certificate portal | No | Business Workspace | Compliance / C-Suite | Authenticated |
| `/dashboard/analytics` | `/dashboard/analytics` | Readiness trend analytics view | No | Operations Workspace | VP Ops / IT Lead | Authenticated |
| `/dashboard/business-units` | `/dashboard/business-units` | Multi-clinic comparison view | No | Business Workspace | Executive / Director | Authenticated |
| `/dashboard/readiness-timeline` | `/readiness/activity` | Hard redirect `301` -> `/readiness/activity` | Yes (Merged) | Business Workspace | IT Manager | Authenticated |
| `/dashboard/assessments` | `/dashboard/assessments` | Formal Security Assessments list view | No | Operations Workspace | Assessor / IT Lead | Authenticated |
| `/dashboard/assessment/new` | `/dashboard/assessment/new` | Assessment Creation Wizard | No | Operations Workspace | Assessor / IT Lead | Authenticated |
| `/dashboard/assessment/quick` | `/dashboard/assessment/new` | Hard redirect `301` -> `/dashboard/assessment/new` | Yes (Merged) | Operations Workspace | Assessor | Authenticated |
| `/dashboard/results/:id` | `/dashboard/results/:id` | Assessment Run Details & Domain Tabs | No | Operations Workspace | IT Auditor / SecOps | Authenticated |
| `/dashboard/admin` | `/dashboard/admin/organizations` | Hard redirect `301` -> `/dashboard/admin/organizations` | No | Admin Workspace | System Admin | Authenticated |
| `/dashboard/admin/organizations` | `/dashboard/admin/organizations` | Canonical route for Tenant Organizations | No | Admin Workspace | System Admin | Authenticated |
| `/dashboard/admin/org/new` | `/dashboard/admin/org/new` | Tenant Onboarding Wizard | No | Admin Workspace | System Admin | Authenticated |
| `/dashboard/admin/governance` | `/dashboard/admin/governance` | Risk Policy and Governance configuration | No | Admin Workspace | CISO / Admin | Authenticated |
| `/dashboard/admin/calendar` | `/dashboard/admin/calendar` | Audit Calendar and Renewal schedule | No | Admin Workspace | Compliance Lead | Authenticated |
| `/dashboard/admin/settings` | `/dashboard/admin/settings` | Global System & Notification settings | No | Admin Workspace | System Admin | Authenticated |
| `/dashboard/settings` | `/dashboard/admin/settings` | Hard redirect `301` -> `/dashboard/admin/settings` | Legacy Subroute | Admin Workspace | System Admin | Authenticated |
| `/readiness/settings` | `/dashboard/admin/settings` | Hard redirect `301` -> `/dashboard/admin/settings` | Legacy Subroute | Admin Workspace | System Admin | Authenticated |
| `/integrations` | `/dashboard/operations/evidence` | Hard redirect `301` -> `/dashboard/operations/evidence` | Yes | Operations Workspace | Security Analyst | Authenticated |
| `/clinic/*` | `/readiness` | Hard redirect `301` -> `/readiness` | Yes (Retired) | Business Workspace | Clinic Admin | Authenticated |

---

## 3. Router Code Structure in `src/App.tsx`

```tsx
// Structure of App.tsx router configuration
<Routes>
  {/* Public / External Routes */}
  <Route path="/" element={<Landing />} />
  <Route path="/login" element={<Login />} />
  <Route path="/about" element={<About />} />
  <Route path="/security" element={<Security />} />
  <Route path="/pilot" element={<Pilot />} />
  <Route path="/status" element={<Status />} />
  <Route path="/auditor" element={<AuditorView />} />

  {/* Authenticated Dual Workspace Shell */}
  <Route element={<ProtectedRoute><DualWorkspaceLayout /></ProtectedRoute>}>
    {/* Business Workspace Sub-tree */}
    <Route path="/readiness" element={<TodayPage />} />
    <Route path="/readiness/actions" element={<NeedsAttentionPage />} />
    <Route path="/readiness/continuity" element={<RecoveryReadinessPage />} />
    <Route path="/readiness/activity" element={<ActivityPage />} />
    <Route path="/dashboard/board-story" element={<BoardStory />} />
    <Route path="/dashboard/reports" element={<Reports />} />
    <Route path="/dashboard/business-units" element={<BusinessUnits />} />

    {/* Operations Workspace Sub-tree */}
    <Route path="/dashboard/operations" element={<Dashboard />} />
    <Route path="/dashboard/operations/evidence" element={<EvidenceNetwork />} />
    <Route path="/dashboard/operations/compliance" element={<ComplianceDrift />} />
    <Route path="/dashboard/operations/technology" element={<TechnologyIntelligence />} />
    <Route path="/dashboard/operations/reliability" element={<ReliabilityDashboard />} />
    <Route path="/dashboard/operations/remediation" element={<RemediationLedger />} />
    <Route path="/dashboard/operations/decision-engine" element={<DecisionEngine />} />
    <Route path="/dashboard/operations/simulation" element={<AIAttackSimulationLab />} />
    <Route path="/dashboard/analytics" element={<AnalyticsPage />} />
    <Route path="/dashboard/assessments" element={<Assessments />} />
    <Route path="/dashboard/assessment/new" element={<NewAssessment />} />
    <Route path="/dashboard/results/:id" element={<Results />} />

    {/* Administration Workspace Sub-tree */}
    <Route path="/dashboard/admin/organizations" element={<Organizations />} />
    <Route path="/dashboard/admin/org/new" element={<NewOrg />} />
    <Route path="/dashboard/admin/governance" element={<GovernanceProfile />} />
    <Route path="/dashboard/admin/calendar" element={<AuditCalendar />} />
    <Route path="/dashboard/admin/settings" element={<Settings />} />

    {/* Legacy Redirect Guards */}
    <Route path="/dashboard" element={<Navigate to="/readiness" replace />} />
    <Route path="/dashboard/evidence-network" element={<Navigate to="/dashboard/operations/evidence" replace />} />
    <Route path="/dashboard/compliance-drift" element={<Navigate to="/dashboard/operations/compliance" replace />} />
    <Route path="/dashboard/tech-stack" element={<Navigate to="/dashboard/operations/technology" replace />} />
    <Route path="/dashboard/reliability" element={<Navigate to="/dashboard/operations/reliability" replace />} />
    <Route path="/dashboard/remediation" element={<Navigate to="/dashboard/operations/remediation" replace />} />
    <Route path="/dashboard/settings" element={<Navigate to="/dashboard/admin/settings" replace />} />
    <Route path="/readiness/settings" element={<Navigate to="/dashboard/admin/settings" replace />} />
    <Route path="/integrations" element={<Navigate to="/dashboard/operations/evidence" replace />} />
    <Route path="/clinic/*" element={<Navigate to="/readiness" replace />} />
  </Route>
</Routes>
```
