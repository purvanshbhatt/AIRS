## Task Assignment for teamwork_preview_worker_m2_1

**Mission**: Execute Milestone 2 (Phases 1-4 Platform Consolidation & Safe Pruning).

**Instructions**:
1. Read `P:\projects\AIRS\.agents\ORIGINAL_REQUEST.md` completely.
2. Read `P:\projects\AIRS\.agents\teamwork_preview_explorer_m1_1\handoff.md` for exact file paths and pruning instructions.
3. Safe Pruning (Remove unused orphan pages):
   - `src/pages/## Chat Customization Diagnostics.md`
   - `src/pages/AIAttackSimulationLab.tsx`
   - `src/pages/Analytics.tsx`
   - `src/pages/BusinessUnits.tsx`
   - `src/pages/DecisionEngine.tsx`
   - `src/pages/GovernanceProfile.tsx`
   - `src/pages/Home.tsx`
   - `src/pages/NewAssessment.tsx`
   - `src/pages/NewOrg.tsx`
   - `src/pages/QuickAssessment.tsx`
   - `src/pages/ReadinessTimeline.tsx`
   - `src/pages/RemediationLedger.tsx`
   - `src/pages/Reports.tsx`
   - `src/pages/clinic/Home.tsx`
   - `src/pages/clinic/IssueDetails.tsx`
   - `src/pages/clinic/Onboarding.tsx`
4. Safe Pruning (Remove unused orphan components and layouts):
   - `src/components/EnterpriseRoadmap.tsx`
   - `src/components/layout/DashboardLayout.tsx`
   - `src/components/OrgEnrichmentCard.tsx`
   - `src/components/readiness/HowWeKnowDrawer.tsx`
   - `src/components/readiness/ReadinessHistoryTimeline.tsx`
   - `src/components/readiness/StoryActionCard.tsx`
   - `src/components/ResultsTabsConfig.ts`
   - `src/components/RoadmapTracker.tsx`
   - `src/components/SuggestedQuestionsPanel.tsx`
   - `src/components/technology/DomainSummaryCard.tsx`
   - `src/components/ui/Accordion.tsx`
   - `src/components/ui/ApiDiagnosticsPanel.tsx`
   - `src/components/ui/EmptyState.tsx`
   - `src/components/ui/EnvironmentBanner.tsx`
   - `src/components/ui/Table.tsx`
   - `src/features/readiness/Layout.tsx`
   - `src/pages/clinic/Layout.tsx`
5. Remap Legacy Components in `App.tsx`:
   - DO NOT DELETE `src/pages/ComplianceDrift.tsx` or `src/pages/TechnologyIntelligence.tsx`!
   - Remap `ComplianceDrift` to route `/activity/compliance-drift` and `TechnologyIntelligence` to route `/technology/intelligence` in `src/App.tsx`.
6. Naming Refactoring:
   - Rename `src/components/dashboard/PersonaContext.tsx` to `src/components/dashboard/PersonaSwitcher.tsx` and update imports in `AppHeader.tsx` or other callers.
7. Fix Router Issue in `src/App.tsx`:
   - Remove the `window.location.replace` logic forcing `*.web.app` to `staging.resilai.org` (lines 130-142).
8. Verification:
   - Run `npm run build` in `P:\projects\AIRS\frontend`.
   - Verify exit code 0 and zero TypeScript / build errors.
9. MANDATORY INTEGRITY WARNING:
   DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
10. Write detailed handoff report to `P:\projects\AIRS\.agents\teamwork_preview_worker_m2_1\handoff.md` and send message to parent.
