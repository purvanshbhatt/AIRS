# Frontend Codebase Survey & Audit Handoff Report

**Agent**: `teamwork_preview_explorer_m1_1`  
**Working Directory**: `P:\projects\AIRS\.agents\teamwork_preview_explorer_m1_1`  
**Target Directory**: `P:\projects\AIRS\frontend`  
**Timestamp**: `2026-08-04T15:25:20Z`

---

## 1. Observation

### Build Baseline
- Command: `npm run build` (runs `tsc -b && vite build`) inside `P:\projects\AIRS\frontend`.
- Result: **Exit Code 0** (Success).
- Output:
  - Chunks: `dist-production/index.html` (1.82 kB), `dist-production/assets/index-DOW6_XB0.css` (236.87 kB), `dist-production/assets/index-BvZsutPc.js` (1,208.13 kB).
  - Duration: `19.83s`.
  - Errors: `0` TypeScript compilation errors, `0` Vite build errors.

### Unused / Orphan Page Files (16 Files)
Automated reference audit across `src/` revealed 16 page files with zero imports or active route definitions:
1. `src/pages/## Chat Customization Diagnostics.md` — Non-code stray markdown file inside `src/pages/`.
2. `src/pages/AIAttackSimulationLab.tsx` — Unreferenced experimental page.
3. `src/pages/Analytics.tsx` — Unreferenced legacy analytics page.
4. `src/pages/BusinessUnits.tsx` — Unreferenced legacy organization page.
5. `src/pages/DecisionEngine.tsx` — Unreferenced legacy decision engine page.
6. `src/pages/GovernanceProfile.tsx` — Unreferenced legacy governance page.
7. `src/pages/Home.tsx` — Old home page (superseded by Morning Brief `/morning-brief`).
8. `src/pages/NewAssessment.tsx` — Unreferenced legacy assessment creation page.
9. `src/pages/NewOrg.tsx` — Unreferenced legacy organization setup page.
10. `src/pages/QuickAssessment.tsx` — Unreferenced legacy quick assessment page.
11. `src/pages/ReadinessTimeline.tsx` — Unreferenced legacy timeline page.
12. `src/pages/RemediationLedger.tsx` — Unreferenced legacy remediation ledger.
13. `src/pages/Reports.tsx` — Unreferenced legacy reports page.
14. `src/pages/clinic/Home.tsx` — Unreferenced legacy clinic mini-app page.
15. `src/pages/clinic/IssueDetails.tsx` — Unreferenced legacy clinic mini-app page.
16. `src/pages/clinic/Onboarding.tsx` — Unreferenced legacy clinic mini-app page.

### Imported Pages Lacking Active `<Route>` Mappings in `App.tsx` (4 Files)
1. `src/pages/ComplianceDrift.tsx` — Imported at `App.tsx:38`, but missing from `<Route>` elements. (*Note*: Requirement R3 highlights preserving `ComplianceDrift` by remapping into Operations).
2. `src/pages/ReliabilityDashboard.tsx` — Imported at `App.tsx:39`, but missing from `<Route>` elements.
3. `src/pages/TechnologyIntelligence.tsx` — Imported at `App.tsx:40`, but missing from `<Route>` elements. (*Note*: Requirement R3 highlights preserving `TechnologyIntelligence` by remapping into Operations).
4. `src/pages/Landing.tsx` — Imported at `App.tsx:13`, but root path `/` redirects directly to `/morning-brief`.

### Unused / Orphan UI & Specialized Components (15 Files)
Automated component reference audit across `src/` revealed 15 component files imported by 0 active components/pages:
1. `src/components/EnterpriseRoadmap.tsx`
2. `src/components/layout/DashboardLayout.tsx` (Duplicate legacy layout)
3. `src/components/OrgEnrichmentCard.tsx`
4. `src/components/readiness/HowWeKnowDrawer.tsx` (Superseded by `AIDrawer.tsx`)
5. `src/components/readiness/ReadinessHistoryTimeline.tsx`
6. `src/components/readiness/StoryActionCard.tsx`
7. `src/components/ResultsTabsConfig.ts`
8. `src/components/RoadmapTracker.tsx`
9. `src/components/SuggestedQuestionsPanel.tsx`
10. `src/components/technology/DomainSummaryCard.tsx` (Superseded by `src/components/common/SummaryCard.tsx`)
11. `src/components/ui/Accordion.tsx`
12. `src/components/ui/ApiDiagnosticsPanel.tsx`
13. `src/components/ui/EmptyState.tsx`
14. `src/components/ui/EnvironmentBanner.tsx`
15. `src/components/ui/Table.tsx`

### Layout & Provider Architecture Audit
- **Layouts**:
  - Primary Layout: `src/components/layout/AppLayout.tsx` (Active, wraps all protected routes in `App.tsx`).
  - Docs Layout: `src/components/layout/DocsLayout.tsx` (Active, wraps `/docs/*`).
  - Legacy/Duplicate Layout 1: `src/components/layout/DashboardLayout.tsx` (Unused).
  - Redundant Layout 2: `src/features/readiness/Layout.tsx` (Unused outer wrapper).
  - Clinic Legacy Layout: `src/pages/clinic/Layout.tsx` (Unused).
- **Providers**:
  - `ThemeProvider` (`src/contexts/ThemeContext.tsx`): Mounted at root in `main.tsx:38`.
  - `AuthProvider` (`src/contexts/AuthContext.tsx`): Mounted in `App.tsx:146`.
  - `DemoModeProvider` (`src/contexts/DemoModeContext.tsx`): Mounted in `App.tsx:147`.
  - `PersonaProvider` (`src/contexts/PersonaContext.tsx`): Mounted in `App.tsx:148`.
  - `ToastProvider` (`src/components/ui/Toast.tsx`): Mounted in `App.tsx:149`.
  - **Misnomer**: `src/components/dashboard/PersonaContext.tsx` exports `PersonaSwitcher` component rather than a context provider, creating file naming collision with `src/contexts/PersonaContext.tsx`.

### Design Tokens & Theme Setup
- **Theme Engine**: Tailwind CSS v4 `@theme` configuration in `src/index.css`.
  - Class-based dark mode (`<html class="dark">`).
  - CSS variables for primary colors (`--color-primary-500: #00C853`), secondary colors (`--color-blue-500: #2979FF`), and dark surface colors (`--color-slate-900: #1A1A1A`).
- **Design Tokens**: Standardized token file at `src/lib/design-tokens.ts`:
  - `tokens.layout` (pageContainer, sectionGap, cardGap)
  - `tokens.typography` (hero, sectionTitle, cardTitle, body, small, label)
  - `tokens.surface` (base, glass, drawer)
  - `tokens.interaction` (hover, tap, focus)
  - `tokens.status` (ready, warning, error, neutral)
  - `tokens.button` (primary, secondary, ghost, aiExplain)

---

## 2. Logic Chain

1. **Observation 1 (Build Success)** -> The codebase builds cleanly with 0 TypeScript/Vite errors today (`tsc -b && vite build` exit code 0). Any proposed pruning must preserve this zero-error build state.
2. **Observation 2 (Unreferenced Pages & Components)** -> 16 page files and 15 component files have 0 import statements or usages in active routes. They represent dead code left over from prior iterations.
3. **Observation 3 (Unrouted Imports in `App.tsx`)** -> `ComplianceDrift.tsx`, `TechnologyIntelligence.tsx`, `ReliabilityDashboard.tsx`, and `Landing.tsx` are imported at the top of `App.tsx` but lack `<Route>` elements. Per requirement R3, `ComplianceDrift` and `TechnologyIntelligence` are high-value legacy components that should be remapped into Operations routes rather than deleted.
4. **Observation 4 (Duplicate Layouts & Misnamed Component)** -> `DashboardLayout.tsx` and `features/readiness/Layout.tsx` duplicate `AppLayout.tsx`. `src/components/dashboard/PersonaContext.tsx` contains component `PersonaSwitcher` and should be renamed to `PersonaSwitcher.tsx` to eliminate confusion with `src/contexts/PersonaContext.tsx`.
5. **Observation 5 (Design System Alignment)** -> Design tokens exist in `src/lib/design-tokens.ts` and Tailwind CSS v4 variables in `src/index.css`. Future component refactoring should consume these tokens directly.

---

## 3. Caveats

- **Preservation vs. Pruning**: `ComplianceDrift.tsx` and `TechnologyIntelligence.tsx` are currently unused in `App.tsx`, but requirement R3 explicitly requests preserving and remapping them into the Operations workspace. They MUST NOT be deleted; they must be re-routed.
- **Scope**: Backend code and cloud infrastructure deployments were not modified during this read-only frontend survey.

---

## 4. Conclusion

- **Baseline Status**: Clean build (`npm run build` succeeds in ~19.8s).
- **Pruning Opportunity**: 16 orphan pages (including 1 stray markdown file `pages/## Chat Customization Diagnostics.md`), 15 orphan UI components, and 2 unused layouts can be safely pruned after removing any dangling top-level imports.
- **Remapping Mandate**: Remap `ComplianceDrift` and `TechnologyIntelligence` to active Operations routes under `/activity` or `/technology/*`.
- **Naming Cleanup**: Rename `src/components/dashboard/PersonaContext.tsx` to `src/components/dashboard/PersonaSwitcher.tsx`.

---

## 5. Verification Method

### 1. Build Verification
Run from `P:\projects\AIRS\frontend`:
```bash
npm run build
```
*Expected Result*: Exit code 0, no TypeScript compilation errors, Vite completes build under 25s.

### 2. Orphan File Verification
Inspect the following files to confirm zero references across `P:\projects\AIRS\frontend\src`:
- `src/pages/## Chat Customization Diagnostics.md`
- `src/pages/AIAttackSimulationLab.tsx`
- `src/pages/Analytics.tsx`
- `src/components/layout/DashboardLayout.tsx`
- `src/components/readiness/HowWeKnowDrawer.tsx`

### 3. Route Verification
Open `src/App.tsx` and verify that all defined routes resolve to valid, active components without fallback wildcard triggering.
