# ResilAI Principal Security & Architecture Audit

- **Audit scope:** Files modified by the Sprint 1.8 / Sprint 2 milestones declared in `SESSION_HANDOFF.md` (S1.8-C5, S2-A4, S2-B5, S2-B6, S2-C3).
- **Source of truth:** `implementation_specification.md` aligned to `PRODUCT_MOAT.md`.
- **Authority basis:** `AGENT_START.md` invariants and the ADRs under `docs/architecture/ADR/`.
- **Verification method:** Targeted file inspection of the SESSION_HANDOFF-listed files (no general repo scan) plus cross-reference against `CODE_INDEX.md` / `OWNERSHIP_MAP.md`.

## 1. Severity legend

- **CRITICAL** — violates `PRODUCT_MOAT.md`, breaks the Trust Invariants, or ships a frontend-to-backend drift that erodes user trust.
- **HIGH** — architectural or security defect, future-state leakage, or premature coupling.
- **MEDIUM** — quality / consistency / type-safety gap; works today but lends itself to future regression.
- **LOW** — cosmetic / consistency notice; safer than the existing baseline.

## 2. Verdict per SESSION_HANDOFF milestone

| Milestone | Verdict | Top issues |
|---|---|---|
| S1.8-C5 `EvidenceNetwork.tsx` | **CONDITIONAL PASS** with HIGH + MEDIUM items. |
| S2-A4 `BoardStory.tsx` | **FAIL / NOT PASS** — CRITICAL client-side score derivation by an AI-shaped LLM-emitted PDF. |
| S2-B5 `DecisionEngine.tsx` | **PASS** with MEDIUMs. |
| S2-B6 `BusinessUnits.tsx` + `PersonaSwitcher` | **PASS** with HIGH and LOW. |
| S2-C3 orphaned route removal | **FAIL / NOT PASS** — backup file references routes that don't exist; live pages still link to deleted paths. |

**Overall PASS:** **NO** — both S2-A4 and S2-C3 remain non-compliant against `PRODUCT_MOAT.md` (LLM never scores, dead-route discipline). The builder must address every CRITICAL and HIGH item before re-audit.

---

## 3. Findings

### F-001 · Client-side narrative-backed score fabrication in Board Story
- **Severity:** CRITICAL
- **File:** `frontend/src/pages/BoardStory.tsx`
- **Lines:** 79–151 (`handleDownloadPDF`)
- **Cited contracts:** `PRODUCT_MOAT.md` Trust Principle 1 (LLMs never score); `implementation_specification.md` Feature A "Acceptance: Every score change creates an immutable ledger row" — i.e., the Board Story narrative layer must never insert or imply a new score; the implementation_specification.md calls this out via the anti-hallucination numeric-trace validator; S2-A2 acceptance in `TASK_QUEUE.md` ("Any numeric in narrative must trace back to source scoring snapshot").
- **Problem:** `BoardStory.tsx` ships a "**Download PDF Story**" button that constructs the entire PDF as a hand-rolled PDF binary string in the browser using `(${date}) Tj` PDF operators and the section JSON fetched from `/api/v1/reports/board-story`. The frontend then *truncates each line at 80 characters* (`cleanLine.substring(0, 80)`) and emits hand-typed executive phrases between sections (e.g., `(ResilAI Board Story - Complete Narrative Briefing) Tj`, stale hardcoded characters). This makes the PDF the **client-derived** "Board Story" — the same endpoint's CSS/scroll UI is the trusted rendering path, but the PDF download path bakes UI-side assumptions about numeric/structured content into a PDF the user treats as auditable. This is exactly the failure mode the spec's "All 10 sections render with section-aware scroll" AC plus ADR "Board Story is narrative-only" forbid.
- Additionally, `Enabled subdomain` injection (`${dateStr.toUpperCase()}`) into the PDF stream is fine, but `(Tj\n` is hand-typed between sections without trusting the server-emitted section IDs, and the `cleanLine` strips `(` and `)` characters — so the PDF can omit truth-bearing characters from the narrative.
- **Recommendation:** Disable the client-built PDF path. Either (a) move PDF rendering server-side via a `_backend_state.py`-style endpoint that returns the PDF bytes the spec calls for (and the rest of the audit fix list), or (b) drop this client-built PDF entirely and rely on the in-app structured view, which is what the spec explicitly requires ("structured, multi-section Board Story view (not just a PDF download)").
- **Fix scope:** Larger refactor — see Task T-A01 below.

### F-002 · The same client-side PDF fabrication lives in `ExecutiveRiskMatrix.tsx` and Dashboard
- **Severity:** CRITICAL
- **File 1:** `frontend/src/components/ExecutiveRiskMatrix.tsx` (`handleDownloadBoardStory` ~L86–L210)
- **File 2:** `frontend/src/pages/Dashboard.tsx` (`handleDownloadBoardStory` L487–end of function)
- **Cited contracts:** Same as F-001.
- **Problem:** The hand-rolled PDF generation pattern is duplicated in two additional places. Notably, `Dashboard.tsx` injects literals such as `(- Wazuh Integration Status: ${wazuhStatus.toUpperCase()}) Tj`, `(Average Response Velocity: 3.0 Days (mitigated from 14.0 days)) Tj`, and "Total Systemic Exposure: Mitigated to Moderate" — KPIs equivilant to scoring language about risk exposure. This is the EXACT failure pattern PRODUCT_MOAT.md warns against: numbers in narrative that did NOT come from deterministic scoring. These numbers are synthesized in the browser.
- **Recommendation:** Same as F-001 — centralize PDF generation server-side, or remove the PDF feature.
- **Fix scope:** Combined with F-001.

### F-003 · `Integrations.tsx` silently aliases to EvidenceNetwork — no historical redirect
- **Severity:** MEDIUM
- **File:** `frontend/src/pages/Integrations.tsx`
- **Lines:** 1–2
- **Cited contracts:** Implementation directive #3 strict-typing/mapping; SPEC Feature C ux objective ("Transform 'Integrations' into an 'Evidence Graph'").
- **Problem:** `Integrations.tsx` is now `export default EvidenceNetwork` (after the alias). `App.tsx` still mounts `path="/integrations"` (root-level) AND `path="/settings/integrations"` AND inside `DashboardRoutes > path="/integrations"`. Any user navigating to `/integrations` lands on the same UI as `/dashboard/integrations` without explanation; this hides from the user that the route was renamed. The spec calls for an explicit `redirect` ("Integrations route redirects to EvidenceNetwork") — this is an alias, not a redirect.
- **Recommendation:** Convert the alias to a 301 redirect from `/integrations` → `/dashboard/evidence-network` (preferred name) using React Router `<Navigate replace to="..." />`. Update `DashboardLayout.tsx` link to use the canonical path. Keep `Integrations.tsx` as the redirect source for as long as the legacy URL is referenced, then remove after one release.
- **Fix scope:** Task T-B01.

### F-004 · "AI Threat Lab" links remain pointed at the now-deprecated `/dashboard/pilot-program`
- **Severity:** HIGH
- **File 1:** `frontend/src/pages/Dashboard.tsx` L933 (`<Link to="/dashboard/pilot-program">AI Threat Lab</Link>`)
- **File 2:** `frontend/src/pages/GovernanceProfile.tsx` L510 (`to={\`/dashboard/pilot-program?org=${selectedOrgId}\`}`)
- **Cited contracts:** S2-C3 acceptance ("Removed routes 404; remaining routes unaffected."), AGENT_START.md deletion discipline.
- **Problem:** `S2-C3` claims to have removed the `PilotDashboard` route, but consumers in `Dashboard.tsx` and `GovernanceProfile.tsx` still produce `<Link to="/dashboard/pilot-program">`. Per spec, deletion must not break remaining UX; here the link still exists but routes to a nonexistent component — the page will 404 in the browser. The .deprecated_routes.txt file even *records* `/pilot-program` and `SentinelDashboard` paths but **never lists `SentinelDashboard`'s actual route** in App.tsx (only `/sentinel` was hinted at; the actual departure was referenced under line 4 of the backup).
- **Recommendation:** Replace the link with one to `/dashboard/ai-attack-simulation-lab` (an existing route found in CODE_INDEX — `frontend/src/pages/AIAttackSimulationLab.tsx`). Audit any other Link href referencing removed components. Refresh `.deprecated_routes.txt` with the actual historical route map.
- **Fix scope:** Task T-C01.

### F-005 · Top-level duplicate routes (`/board-story`, `/decision-engine`, `/business-units`, `/integrations`, `/readiness-timeline`)
- **Severity:** MEDIUM
- **File:** `frontend/src/App.tsx`
- **Lines:** 74–80 (top-level) plus nested under `DashboardRoutes` would have been the editorial-correct path — except the parent `<Route path="/dashboard/*">` already mounts them as children.
- **Cited contracts:** AC Knowledge Index "Top-level routes resolve consistently"; S2-A4/S2-B5/S2-B6 acceptance pages must be reached via stable URLs. SPEC: "Frontend Implementer consumes APIs and builds Phase A, B, C, and D UIs" — route surface should be unambiguous.
- **Problem:** Routes are mounted twice in two different prefixes — the page is reachable via two different URLs. The legacy top-level `/board-story` path was likely debris. Coupling two URLs to one component makes future auditing ambiguous.
- **Recommendation:** Pick one canonical prefix. Keep `/dashboard/{board-story|decision-engine|business-units|integrations|readiness-timeline}` (matches the rest of the dashboard routes) and remove the top-levels. Make the redirect from the unmounted path explicit (uses `<Navigate replace>`). Update all `Link`s.
- **Fix scope:** Task T-D01.

### F-006 · Dead-code inheritance: PersonaSwitcher lives in `components/dashboard/PersonaContext.tsx`
- **Severity:** LOW
- **File:** `frontend/src/components/dashboard/PersonaContext.tsx`
- **Lines:** 1–50
- **Cited contracts:** Strict typing / maintainability (Knowledge Index).
- **Problem:** The file is named `PersonaContext.tsx` but it exports a *component* named `PersonaSwitcher`. The actual context lives at `frontend/src/contexts/PersonaContext.tsx`. This dual use of the same name is a maintainability hazard — readers will look for the switcher in `contexts/` and find nothing.
- **Recommendation:** Rename the file `PersonaSwitcher.tsx` and update the import in `Dashboard.tsx` L84 and `components/dashboard/` index if any.
- **Fix scope:** Task T-E01.

### F-007 · `getEvidenceConfidence()` ignores `org_id` — required by spec
- **Severity:** MEDIUM
- **File:** `frontend/src/api.ts` L1460
- **Cited contracts:** Implementation Specification Feature C: "Returns per-connector confidence + org-level aggregate, 0-100; **422 missing org_id**" (from TASK_QUEUE.md S1.8-C4 acceptance).
- **Problem:** Both `EvidenceNetwork.tsx` (L178) and `Dashboard.tsx` (L299) call `getEvidenceConfidence()` without `org_id`. The dashboard snapshot is therefore org-scope ambiguous: tenant-isolation risk if more than one org is in scope; also the spec acceptance requires 422 on missing org_id but frontend never sends org.
- **Recommendation:** Add `orgId: string` parameter to `getEvidenceConfidence(orgId)`; update callers.
- **Fix scope:** Task T-F01.

### F-008 · `PersonaSwitcher` toggle has **no effect on widget visibility**
- **Severity:** HIGH
- **File:** `frontend/src/pages/Dashboard.tsx` L660 (`persona === 'EXECUTIVE' ? (...) : (... for forensic)`)
- **Cited contracts:** S2-B6 Acceptance: "Persona context filters visible widgets; default = 'Executive' (all)."
- **Problem:** Only the **top branch** (EXECUTIVE) is materialized in the Dashboard.tsx file. Inspection shows the entire 1,417-line file has just a single `persona === 'EXECUTIVE'` conditional containing the dashboard cards, and a single `else` branch granting the technical hero (a more detailed forensic view of GHI). That's likely correct as a feature. However, SESSION_HANDOFF.md claims "Persona-based widget visibility" — in practice the widget-set is heuristic, not declarative. The implementation detail is described in `PersonaContext.tsx` (default `EXECUTIVE`, persisted to localStorage). The `PersonaSwitcher` *does* toggle state, **but the forensic branch is not properly labeled or data-tailored** — pages currently render the same widgets regardless of persona selection in many areas.
- **Recommendation:** Extract the persona-based widget matrix into one declarative config (`personaWidgets[persona]`), and have it filter `kanban` cards, drawer content, etc. Audit each branch for "no client scoring math" and "no client narrative inside widgets" to ensure PRODUCT_MOAT holds when persona = FORENSIC.
- **Fix scope:** Task T-G01.

### F-009 · `BoardStory.tsx` performs plain-string navigation search (`searchParams.get('org')`) without escaping or org contract
- **Severity:** LOW
- **File:** `frontend/src/pages/BoardStory.tsx`, `DecisionEngine.tsx`, `BusinessUnits.tsx`
- **Cited contracts:** Strict typing / API consistency.
- **Problem:** `useSearchParams().get('org') || ''` silently swallows invalid org ids. If a user crafts `/board-story?org=foo`, the page renders "no organization selected" — but the API call still goes out and 404s server-side. A small UX win.
- **Recommendation:** Pre-validate with an `isValidOrgId` check (UUID v4) before firing the API. Surface a clean "missing or invalid org" state.
- **Fix scope:** Task T-H01.

### F-010 · `EvidenceNetwork.tsx` (970 lines) — single file mixing tab UI, modal dialogs, and direct vendor operations
- **Severity:** MEDIUM
- **File:** `frontend/src/pages/EvidenceNetwork.tsx`
- **Cited contracts:** Implementation Spec §1 "Technical Debt #1 — `Dashboard.tsx` has grown to ~1,400 lines…"; SESSION_HANDOFF.md calls this out — must be applied consistently.
- **Problem:** EvidenceNetwork itself is 970 lines and contains 4 sections (network / wazuh / splunk / webhooks) plus all of the wiring (state, API call handlers for each adapter + 6 mock/seed flows). This is structurally similar to the bloat flagged in the spec. The fix recommended in the spec for `Dashboard.tsx` should also apply here per the consistency principle.
- **Recommendation:** Extract each tab into `frontend/src/components/evidence/{Network,Wazuh,Splunk,Webhooks}Tab.tsx`. Keep `EvidenceNetwork.tsx` as a router + heading + tab-state container only.
- **Fix scope:** Task T-I01.

### F-011 · `EvidenceNetwork.tsx` renders hardcoded fallback score 84
- **Severity:** MEDIUM
- **File:** `frontend/src/pages/EvidenceNetwork.tsx` L483
- **Cited contracts:** ADR-010 (Evidence Confidence deterministic). PRODUCT_MOAT (deterministic scoring only — no fallback fabricating numbers).
- **Problem:** `ConfidenceGauge score={confidenceData?.aggregate_score || 84}`. If the real confidence call fails or returns falsy, the UI displays **84** as the verification confidence — a deterministic, plausible number. This breaks ADR-010's invariant: never fabricate a number. Use `null` and render a "Confidence unavailable" indicator instead.
- **Recommendation:** Use the `isLoading`/`error` states of the existing call to gate rendering. Display `—` or "Confidence unavailable" character when `confidenceData == null`.
- **Fix scope:** Task T-J01.

### F-012 · Mock/seed Splunk call retained in production UX
- **Severity:** HIGH
- **File:** `frontend/src/pages/EvidenceNetwork.tsx` L304 (`handleSeedFindings`), L287 (`handleConnectSplunk`).
- **Cited contracts:** Implementation Spec §1 "Technical Debt #4 — `cve_enrichment.py` currently relies on mock NVD/KEV data for staging." / §2 "Telemetry beats Questionnaire / Pulling data from Splunk/Wazuh is superior to asking humans." Mock seeds short-circuit that contract in production UX.
- **Problem:** Buttons "Seed Mock Findings" and "Connect Splunk" call `seedMockSplunkFindings`. This is acceptable in the connector card, but `Connect Splunk` `handleConnectSplunk` (L287) is exposed as a primary action in the Wazuh/Splunk tab UX, accepting that the developer is seeding synthetic findings. For the staging-only mandate in the spec this is okay; for production the button label is misleading.
- **Recommendation:** Label guard. Use `import.meta.env.VITE_APP_ENV === 'staging'` to render a `Demo Only` small text on the buttons when not in production. Tag the seed call site clearly. (Spec demands staging-first; ensure production loses the demo buttons entirely.)

### F-013 · `EvidenceNetwork.tsx` org select panel duplicates the existing `DashboardLayout` header org selector
- **Severity:** LOW
- **File:** `frontend/src/pages/EvidenceNetwork.tsx` L428–L437
- **Cited contracts:** UI consistency, S2-B6 persona-based widget visibility.
- **Problem:** EvidenceNetwork renders a local `<select>` for `Organization` even though the surrounding `DashboardLayout` chrome already has a global org selector. This is inconsistent.
- **Recommendation:** Lift org selection into `DashboardLayout` context, consume via `useContext` (the existing pattern used by `useDemoMode`). Avoid duplicate knobs.
- **Fix scope:** Task T-K01.

### F-014 · Frontend hardcodes fallback strings that look like scoring inputs
- **Severity:** MEDIUM
- **File:** `frontend/src/pages/DecisionEngine.tsx` (`projection ? Math.round(projection.assessment_score) : 84`)
- **Cited contracts:** ADR-007; Product_MOAT "Deterministic scoring only".
- **Problem:** When `projection == null` the page renders `84%` as a "Baseline Posture". A UI-ascribed number presented to a CISO looks identical to a verified scoring snapshot. The "POSTURE" here is the readiness score baseline shown in a UI panel — at PRODUCT_MOAT, a number the user sees must come from the server (or be explicitly "No data").
- **Recommendation:** Replace `84%` with `—` (em dash) or `<span>Pending</span>` UI placeholder that conveys "no calculation yet".
- **Fix scope:** Task T-L01.

### F-015 · `UsePersona` and `UseDemoMode` dual-toggle data sources conflict
- **Severity:** MEDIUM
- **File:** `frontend/src/pages/Dashboard.tsx` L678–L710 (Data Source Toggle) and L661–L996 (EXECUTIVE branch)
- **Cited contracts:** S2-B6 "Persona context filters visible widgets; default = 'Executive' (all)."
- **Problem:** There's an independent `dataSource` toggle (`'live' | 'static'`) layered on top of the persona context. This is two control surfaces where one is sufficient. Persona should encapsulate data-source choice (Executive = live; Forensic = live; only MaintenanceMode = static).
- **Recommendation:** Component-test-match. Drop `dataSource` in favor of computing it from persona.
- **Fix scope:** Task T-M01.

### F-016 · Duplicate lossless client-side hardcoded numbers throughout
- **Severity:** MEDIUM
- **File:** `frontend/src/pages/Dashboard.tsx` L412–L459 `getExecutiveExplanation()`
- **Cited contracts:** PRODUCT_MOAT (deterministic scoring only), ADR-007 (LLM never scores), ADR-011 (Board Story narrative-only).
- **Problem:** `getExecutiveExplanation()` returns hardcoded `risk: '$120,000 (Minimal…)'`, `risk: '$4,200,000 (Critical…)'`, `hoursSaved: '320 hours saved this quarter…'`, `mttr: '1.4 hours average response time'`. **None of these numbers traces back to a deterministic server-supplied field**; they are placeholders inside a `getReadinessLevel`-branched string. This **directly produces the failure mode PRODUCT_MOAT warns against** (numbers in narrative without sourcing).
- **Recommendation:** Convert these strings to require sourced fields: take `risk_estimate_usd`, `hours_saved`, `mttr` from the readiness payload and never fallback hardcoded. If missing, render "Estimate unavailable" — same pattern as F-011.
- **Fix scope:** Task T-N01.

### F-017 · Frontend uses `verifyControl` extension keys via concatenated strings (`verify_control`, `remediate_exposure`, `remediate_lifecycle`)
- **Severity:** LOW
- **File:** `frontend/src/pages/DecisionEngine.tsx` L101–L111
- **Cited contracts:** Strict typing / API consistency.
- **Problem:** TypeScript maps `DecisionAction.type` is `string` instead of a union literal of valid types. The frontend falls back to a `HelpCircle` for unknown types — silent degradation.
- **Recommendation:** Tighten the `DecisionAction` interface to use `type: 'verify_control' | 'remediate_exposure' | 'remediate_lifecycle' | ...` and TS will reveal server-side drift.
- **Fix scope:** Task T-O01.

### F-018 · Deprecated routes — backup file contains stale info that straddles past and present
- **Severity:** MEDIUM
- **File:** `frontend/.deprecated_routes.txt`
- **Cited contracts:** S2-C3 Acceptance ("Removed routes 404; remaining routes unaffected. Backups of route configs preserved.").
- **Problem:** The backup file says `/sentinel` was removed but `SentinelDashboard.tsx` was never actually imported in the *visible* App.tsx — only the older `app/api/routes/sentinel_test.py` (a Python module) was deleted. The route document is not authoritative. Plus, the file `SentinelDashboard.tsx` doesn't exist on disk (verified via `Test-Path = False`). The backup is a historical note rather than a rollback-ready inventory.
- **Recommendation:** Refresh `.deprecated_routes.txt` with the definitive list of routes audited at the audit time (paths, components, mount-points). Mark clearly which were truly deleted vs conditionally retired. Provide restoration snippets (require only the prior `.tsx` snapshot being re-added).

### F-019 · Strict-typing map drift between Pydantic `BoardStorySection` and frontend `BoardStorySection`
- **Severity:** LOW
- **File:** `frontend/src/api.ts` L1395–L1403
- **Cited contracts:** Implementation directive #3: "Ensure TypeScript interfaces perfectly map to Pydantic schemas".
- **Problem:** Both sides define `section_id`, `title`, `content` — but the backend schema (referenced by the spec) should include the canonical 10-section ID set as a Pydantic Literal, validated against it. Frontend has only the move-typed string. Mismatches will not be caught at compile time.
- **Recommendation:** Both backend and frontend should align on a single source of truth for the 10 section IDs (`'sec-1'..'sec-10'`) and the canonical section titles. Optionally extract into a shared JSON. (Backend is out of scope for this audit; the spec directs the frontend to align.)

### F-020 · `EvidenceNetwork.tsx` has a hardcoded fallback score of 84 — appearing twice (Conf + scoreboard)
- **Severity:** MEDIUM
- **File:** `frontend/src/pages/EvidenceNetwork.tsx` L483 (ConfidenceGauge), `DecisionEngine.tsx` L251 (Baseline Posture), Dashboard.tsx L770 (Evidence Verification).
- **Problem:** Three different UI panels each independently fall back to `84%` when their respective API hasn't completed. This pattern, repeated, indicates a code-smell that risks ADR-010 compliance. Centralize the "unavailable state" rendering.
- **Recommendation:** Extract a single `<ScoreUnavailableState />` component used in all three call-sites.

### F-021 · `EvidenceNetwork.tsx` confidence score boot static `84`
- **Severity:** MEDIUM (related to F-011 / F-014 / F-020)
- **Note:** Consolidates F-011 with sibling sites; F-020 references the same code smell.

---

## 4. Performance / Dead-code / Type safety observations (severity LOW unless flagged)

- **F-022 (LOW):** `EvidenceNetwork.tsx` L3 imports `motion, AnimatePresence` from `framer-motion` — used mostly for cover animations; some pages don't actually use AnimatePresence. Keep.
- **F-023 (LOW):** `EvidenceNetwork.tsx` L529 `"bg-slate-50/50 dark:bg-slate-955/20"` — `slate-955` is not a valid Tailwind token (Tailwind 3 has 50/100/.../950). Either `slate-950/20` or `slate-900/65`. Visual bug.

---

## 5. Enterprise readiness / regression observations

- **F-024 (MEDIUM):** The `.deprecated_routes.txt` references `PilotDashboard` as a "Route Config" but the config it shows is the original arbitrary path `/pilot-program` rather than a documented App.tsx mount. The file cannot be used for a faithful rollback. Make the file a snippet-of-code style — paste in the exact JSX <Route> statement.
- **F-025 (HIGH):** Despite SESSION_HANDOFF.md claiming "All Sprint 1.8 & 2 frontend milestones have been fully accomplished and verified", **the spec's acceptance criteria (#3 Strict Typing) are not demonstrably met** — `DecisionAction.type: string`, `DecisionAction.control: Record<string, any>`, `ProjectReadinessResponse.modifiers: Record<string, any>`. These need to be replaced with Pydantic-mirrored interfaces (`type: Literal[...]`, `modifiers: Modifiers`).
- **F-026 (HIGH):** DecisionEngine.tsx uses fixed dropdown `SLA_TEMPLATE` for typings — actions are matched by `act.type-act.software_name` string concat; if backend returns a single action with `control: { control_id, name }` the equality tuple differs from backend logic. The projection is data-dependent on a brittle equality key.

---

## 6. Recommended Implementation Tasks (for the next sprint)

Each task below is small (1–3h) and self-contained. Names match TASK_QUEUE.md conventions.

### T-A01 — Server-rendered Board Story PDF (replaces client-build in F-001, F-002) · HIGH
- **Title:** Move PDF generation server-side under `/api/v1/reports/board-story.pdf` (and equivalent for executive-risk dashboard).
- **Severity Fix:** CRITICAL ← F-001 + F-002.
- **Files:** `app/api/v1/reports.py` (new endpoint), `frontend/src/pages/BoardStory.tsx`, `frontend/src/components/ExecutiveRiskMatrix.tsx`, `frontend/src/pages/Dashboard.tsx`.
- **Acceptance:**
  - Frontend buttons issue a single GET to a server endpoint and download the response.
  - All numbers in PDF body are sourced from scoring snapshot fields (verified by `tests/test_narrative_anti_hallucination.py`).
  - 422 on missing org_id; 503 on Gemini rate-limit fallback.
- **Unit tests:** `tests/test_board_story_pdf_endpoint.py` — verifies deterministic rendering, source traceability.
- **Integration tests:** Hit staging; assert response is PDF bytes, contains the 10 section IDs.

### T-B01 — Explicit redirect from `/integrations` → `/dashboard/evidence-network` · MEDIUM
- **Severity Fix:** MEDIUM ← F-003.
- **Files:** `frontend/src/pages/Integrations.tsx` → replace `export default EvidenceNetwork` with `<Navigate replace to="/dashboard/evidence-network" />`.
- **Acceptance:** Both `/integrations` and `/dashboard/integrations` resolve to the same canonical page; query-string `?` flows through.

### T-C01 — Remove dead `/dashboard/pilot-program` links · HIGH
- **Severity Fix:** HIGH ← F-004.
- **Files:** `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/GovernanceProfile.tsx`.
- **Acceptance:** No `<Link>` in `frontend/src/pages/*` points at `/sentinel` or `/pilot-program`. Linter unit test enforces.
- **Coverage:** `tests/frontend/test_link_integrity.py` (new) scans rendered TSX for these substrings via a regex AST walker.

### T-D01 — Single-prefix routing audit on top-level duplicates · MEDIUM
- **Severity Fix:** MEDIUM ← F-005.
- **Files:** `frontend/src/App.tsx`.
- **Acceptance:** Only one canonical mount per page. Legacy top-levels replaced with `<Navigate replace />`.
- **Lint unit test:** `tests/frontend/test_route_uniqueness.py`.

### T-E01 — Rename `PersonaSwitcher` file · LOW
- **Severity Fix:** LOW ← F-006.
- **Files:** Rename `frontend/src/components/dashboard/PersonaContext.tsx` → `PersonaSwitcher.tsx` + update import in `Dashboard.tsx`.

### T-F01 — Pass `org_id` to `getEvidenceConfidence()` · MEDIUM
- **Severity Fix:** MEDIUM ← F-007.
- **Files:** `frontend/src/api.ts`, `EvidenceNetwork.tsx`, `Dashboard.tsx`.
- **Acceptance:** All three callers pass `orgId`, OR server default is documented. Tenant isolation covered by existing backend tests.

### T-G01 — Persona-driven widget matrix · HIGH
- **Severity Fix:** HIGH ← F-008.
- **Files:** `frontend/src/pages/Dashboard.tsx`.
- **Acceptance:** `persona=EXECUTIVE` shows executive-cited widgets only; `persona=FORENSIC` shows technical-cited widgets only; no widget set overlap.
- **Unit test:** `tests/frontend/test_persona_widget_filter.py` — verifies DISJOINT widget sets per persona (per spec acceptance).

### T-H01 — Validate `?org` UUID on board-story / decision / business-unit pages · LOW
- **Severity Fix:** LOW ← F-009.
- **Files:** `frontend/src/pages/BoardStory.tsx`, `DecisionEngine.tsx`, `BusinessUnits.tsx`.

### T-I01 — Extract EvidenceNetwork tabs into separate components · MEDIUM
- **Severity Fix:** MEDIUM ← F-010.
- **Files:** `frontend/src/components/evidence/{Wazuh,Splunk,Webhooks,Network}Tab.tsx`. Keep `EvidenceNetwork.tsx` ≤ 200 lines.

### T-J01 — Confidence gauge: render `—` instead of `84` fallback · MEDIUM
- **Severity Fix:** MEDIUM ← F-011.
- **Files:** `frontend/src/pages/EvidenceNetwork.tsx`, `frontend/src/components/evidence/ConfidenceGauge.tsx`.

### T-L01 — DecisionEngine baseline score: render unavailable state · MEDIUM
- **Severity Fix:** MEDIUM ← F-014.
- **Files:** `frontend/src/pages/DecisionEngine.tsx`.

### T-M01 — Unify `dataSource` and `persona` toggles · MEDIUM
- **Severity Fix:** MEDIUM ← F-015.
- **Files:** `frontend/src/pages/Dashboard.tsx`, `frontend/src/contexts/PersonaContext.tsx`.

### T-N01 — Sourced numbers in `getExecutiveExplanation()` · MEDIUM
- **Severity Fix:** MEDIUM ← F-016.
- **Files:** `frontend/src/pages/Dashboard.tsx`. **Hard constraint: no hardcoded fallback.** Replace `'$120,000 (Minimal drift exposure)'` etc. with a sourced field from the readiness payload.

### T-O01 — Tighten `DecisionAction` types · LOW
- **Severity Fix:** LOW ← F-017.
- **Files:** `frontend/src/api.ts`.

### T-P01 — Score unavailable state component · MEDIUM
- **Severity Fix:** MEDIUM ← F-020 (centralizes F-011 + F-014 + F-015).
- **Files:** `frontend/src/components/ui/ScoreUnavailableState.tsx`.

### T-Q01 — Refresh `.deprecated_routes.txt` to be authoritative · MEDIUM
- **Severity Fix:** MEDIUM ← F-018.
- **Files:** `frontend/.deprecated_routes.txt`. Replace prose with the actual historic `<Route>` snippets.

### T-R01 — Tailwind invalid token fix · LOW
- **Severity Fix:** LOW ← F-023.
- **Files:** `frontend/src/pages/EvidenceNetwork.tsx` (the `slate-955` class).

### T-S01 — Strict typing against Pydantic schemas · HIGH
- **Severity Fix:** HIGH ← F-025, F-026.
- **Files:** `frontend/src/api.ts` — replace `Record<string, any>` in `DecisionAction`, `ProjectReadinessResponse`, `BoardStorySection`, `OrgConfidenceResponse`. Pin down Literal types for `DecisionAction.type`.

### T-T01 — Apply lint rule against hardcoded numeric fallbacks in JSX · LOW
- **Severity Fix:** LOW (prophylactic) ← F-011, F-014, F-016.
- **Files:** introduced `tests/frontend/test_no_fallback_numbers.py` (AST scan of `frontend/src/pages/**` for `\|\| <number>` patterns).

---

## 7. Architecture / Security / PRODUCT_MOAT compliance verdict

- **PRODUCT_MOAT #1 (LLMs never score):** **VIOLATED** in frontend (F-001, F-002, F-016) — client-side fabricated numerics appear in user-visible output. The spec scope is "...AI does not calculate readiness scores" but the client-side rendering of stale placeholder numbers breaches the spirit of this invariant. **MUST FIX** before merge.
- **PRODUCT_MOAT #2 (Telemetry beats questionnaires):** Evidence Network largely aligned; F-012 is acceptable in staging but needs prod gate.
- **PRODUCT_MOAT #3 (Evidence beats self-attestation):** Aligned; no notable violation.
- **PRODUCT_MOAT #4 (Deterministic scoring only):** F-011, F-014, F-016, F-020 are direct violations of the "deterministic only — no fabrication" spirit.

---

## 8. Regression risk assessment

| Risk | Severity for next sprint |
|---|---|
| Misleading score in Board Story PDF | CRITICAL — fix T-A01 first. |
| Persona widget set leakage | HIGH — fix T-G01. |
| Dead-link 404s in production | HIGH — fix T-C01. |
| Hardcoded fallback scores being read as authoritative | MEDIUM — fix T-J01, T-L01, T-N01, T-P01 in combination. |

## 9. PASSELIGIBILITY determination

THIS IMPLEMENTATION DOES **NOT** PASS PRODUCT_MOAT COMPLIANCE as of audit time.

The blockers are CRITICAL findings F-001, F-002, and HIGH findings F-004, F-008, F-012, F-025. **Re-audit is required** after the builder executes T-A01, T-C01, T-G01, T-S01, plus F-011 / F-014 / F-016 centralized (T-J01, T-L01, T-N01, T-P01) remediation.

### Per-milestone decisions

- **S1.8-C5** (EvidenceNetwork): **NOT PASS** — fails F-011, F-012, F-013, F-020, F-023. Required: T-J01, T-I01, T-P01, T-R01.
- **S2-A4** (BoardStory): **NOT PASS** — fails F-001 + F-002 (CRITICAL). Required: T-A01.
- **S2-B5** (DecisionEngine): **PASS with caveats** — fails F-014, F-017. Required: T-L01, T-O01.
- **S2-B6** (BusinessUnits + PersonaSwitcher): **NOT PASS** — fails F-008 (HIGH). Required: T-G01, T-E01.
- **S2-C3** (route cleanup): **NOT PASS** — fails F-004 (HIGH), F-018 (MEDIUM), F-023 (LOW for tailwind illicit), F-005 (MEDIUM). Required: T-C01, T-D01, T-Q01.
