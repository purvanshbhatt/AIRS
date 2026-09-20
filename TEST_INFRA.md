# Test Infrastructure: ResilAI Multi-Vertical Positioning Experiment (Staging Only)

## 1. Test Philosophy
- **Opaque-Box & Requirement-Driven**: Tests are designed against explicit contractual requirements in `PROJECT.md` and `ORIGINAL_REQUEST.md`. They verify observable user outcomes, DOM semantics, network boundaries, and state transitions without coupling to private internal variables.
- **Zero Facade Testing**: Every test exercises genuine components, routing logic, API contracts, or storage state. Facade assertions and tautological assertions (e.g. `expect(true).toBe(true)`) are strictly forbidden.
- **Deterministic Derivation**: Expected outputs (headlines, questions, persona names, system telemetry, and invariant guarantees) are derived directly from the authoritative specifications in `ORIGINAL_REQUEST.md` and `PROJECT.md`.
- **Architectural Invariant Enforcement**: Tests independently verify that the core mathematical scoring engine (`app/services/scoring.py` / `calculate_readiness_delta`) remains shared and untainted by LLMs, with zero duplicate scoring implementations across verticals.

---

## 2. Test Architecture

The E2E test suite spans two dedicated test suites:

### 2.1 Frontend Browser & DOM Test Suite (`frontend/src/test/e2e-vertical-positioning.test.tsx`)
- **Test Runner**: Vitest 4.x with `@testing-library/react`, `@testing-library/user-event`, and `jsdom`.
- **Scope**:
  - Subdomain parsing and hostname simulation (`window.location.hostname`).
  - Path prefix parsing and history routing (`/healthcare`, `/legal`, `/`).
  - Query parameter detection and priority resolution (`?vertical=healthcare`).
  - Landing page DOM rendering (headlines, core questions, focus areas, CTAs).
  - Multi-tenant demo persona initialization (Acme Technologies, Northstar Family Health, Northstar & Cole LLP).
  - Global sticky amber demo banner rendering across demo routes (`bg-amber-500/10 border-b border-amber-500/20 text-amber-900 dark:text-amber-200`).
  - Client-side mutation guard (`api.ts` blocking `POST`, `PUT`, `DELETE`, `PATCH` during active demo sessions).
  - Rapid tenant switching and session persistence in `localStorage`.

### 2.2 Backend Public Config & Engine Invariant Test Suite (`tests/test_e2e_vertical_config.py`)
- **Test Runner**: Pytest 9.x inside `.venv_linux`.
- **Scope**:
  - Public API contract verification (`GET /api/public/product-config`).
  - Query parameter filtering (`?vertical=healthcare`, `?vertical=legal`, `?vertical=general`).
  - Header resolution (`X-ResilAI-Vertical`).
  - Unknown vertical handling and fallback responses.
  - JSON schema adherence (keys, types, non-empty focus areas).
  - Shared scoring engine invariant verification (ensuring identical scoring logic is executed regardless of vertical).

---

## 3. Feature Inventory Mapping (Tiers 1–4)

| Feature ID | Feature Name | Description | Tier 1 (Count) | Tier 2 (Count) | Tier 3 (Cross) | Tier 4 (Real-World) |
|---|---|---|:---:|:---:|:---:|:---:|
| **F1** | Subdomain Vertical Detection | Parse hostname (`healthcare.staging.resilai.org`, `legal.staging.resilai.org`, `staging.resilai.org`, `healthcare.localhost`) | 5 | 5 | ✓ | ✓ |
| **F2** | Path Fallback | Route path prefix (`/healthcare`, `/legal`, `/`) | 5 | 5 | ✓ | ✓ |
| **F3** | Query Parameter Fallback | Route query param (`?vertical=healthcare`, `?vertical=legal`, `?vertical=general`) | 5 | 5 | ✓ | ✓ |
| **F4** | Public Config API | `GET /api/public/product-config` contract and static fallback | 5 | 5 | ✓ | ✓ |
| **F5** | General Landing Experience | Universal positioning headline, question, focus areas (Cloud, SaaS, Identity) | 5 | 5 | ✓ | ✓ |
| **F6** | Healthcare Landing Experience | Healthcare headline, ransomware question, focus areas (EHR, Veeam, M365) | 5 | 5 | ✓ | ✓ |
| **F7** | Legal Landing Experience | Law firm headline, client data question, focus areas (DMS, partner access, ABA) | 5 | 5 | ✓ | ✓ |
| **F8** | Demo Persona Launch | Acme Technologies, Northstar Family Health, Northstar & Cole LLP | 5 | 5 | ✓ | ✓ |
| **F9** | Global Amber Demo Banner | Unmistakable sticky amber banner rendered across all demo pages | 5 | 5 | ✓ | ✓ |
| **F10** | Read-Only Demo Mutation Guard | Mutation interception (`POST`, `PUT`, `DELETE`, `PATCH`) under active demo session | 5 | 5 | ✓ | ✓ |

---

## 4. Test Tiers Breakdown

### Tier 1: Feature Coverage (≥5 Tests per Feature, Minimum 50 Tests)
- **F1 (Subdomain Detection)**:
  1. `healthcare.staging.resilai.org` resolves to healthcare vertical.
  2. `legal.staging.resilai.org` resolves to legal vertical.
  3. `staging.resilai.org` resolves to general platform.
  4. Localhost subdomains (`healthcare.localhost:5173`) resolve correctly.
  5. Unrecognized subdomains (`unknown.staging.resilai.org`) default to general platform.
- **F2 (Path Fallback)**:
  1. `/healthcare` activates healthcare vertical.
  2. `/legal` activates legal vertical.
  3. Root path `/` activates general platform.
  4. Path takes precedence over root hostname when on general host.
  5. Deep paths under vertical preserve vertical context.
- **F3 (Query Param Fallback)**:
  1. `?vertical=healthcare` resolves to healthcare vertical.
  2. `?vertical=legal` resolves to legal vertical.
  3. `?vertical=general` forces general platform.
  4. Query param overrides path prefix when conflicting.
  5. Query param overrides subdomain when conflicting.
- **F4 (Public Config API)**:
  1. `GET /api/public/product-config` returns default general config.
  2. `GET /api/public/product-config?vertical=healthcare` returns healthcare schema.
  3. `GET /api/public/product-config?vertical=legal` returns legal schema.
  4. Header `X-ResilAI-Vertical: healthcare` returns healthcare config.
  5. Offline fallback uses synchronous static registry in `verticals.ts`.
- **F5 (General Landing Experience)**:
  1. Renders headline: "ResilAI — AI Incident Readiness Platform".
  2. Renders core question: "If a security or AI incident happens tomorrow, are you actually ready?".
  3. Renders universal focus areas (Cloud, SaaS, Identity).
  4. CTA links lead to general demo sandbox (`Acme Technologies`).
  5. Navigation links preserve general context.
- **F6 (Healthcare Landing Experience)**:
  1. Renders headline: "Incident readiness for healthcare organizations".
  2. Renders core question: "If ransomware hits your clinic tomorrow morning, can you keep operating and prove you're ready?".
  3. Renders healthcare focus areas (Ransomware, EHR clinical operations, Veeam, M365).
  4. CTA links lead to healthcare demo sandbox (`Northstar Family Health`).
  5. Navigation links preserve healthcare context.
- **F7 (Legal Landing Experience)**:
  1. Renders headline: "Incident readiness for law firms".
  2. Renders core question: "If ransomware hits your firm tomorrow morning, can you keep operating and protect client data?".
  3. Renders legal focus areas (Client data protection, privileged access, document vault security, ABA compliance).
  4. CTA links lead to legal demo sandbox (`Northstar & Cole LLP`).
  5. Navigation links preserve legal context.
- **F8 (Demo Persona Launch)**:
  1. Launching demo from general landing seeds `demo-acme-technologies` (Alex Chen).
  2. Launching demo from healthcare landing seeds `demo-northstar-health` (Dr. Evelyn Reed).
  3. Launching demo from legal landing seeds `demo-northstar-cole` (Marcus Cole).
  4. Active organization hook populates all 3 demo tenants for switching.
  5. Demo session initializes authenticated state with mock user profile.
- **F9 (Global Amber Demo Banner)**:
  1. Amber banner displays "DEMO / SIMULATED DATA" across `/morning-brief`.
  2. Amber banner persists on `/needs-attention`.
  3. Amber banner persists on `/recovery`.
  4. Amber banner persists on non-briefing routes (`/reports`, `/settings`, `/connectors`).
  5. Amber banner styling contains distinctive amber background and border classes.
- **F10 (Read-Only Demo Sandbox Mutation Guard)**:
  1. Blocks `POST` requests when `resilai_demo_user` is true.
  2. Blocks `PUT` requests when `resilai_demo_user` is true.
  3. Blocks `DELETE` requests when `resilai_demo_user` is true.
  4. Blocks `PATCH` requests when `resilai_demo_user` is true.
  5. Dispatches `resilai-readonly-action` event to notify the UI without throwing unhandled exceptions.

### Tier 2: Boundary, Extreme & Corner Cases (≥5 Tests per Group, Minimum 35 Tests)
- **Unknown & Malformed Queries**:
  1. `?vertical=finance` defaults cleanly to general without crash.
  2. `?vertical=12345` defaults cleanly to general.
  3. Empty query `?vertical=` defaults cleanly to general.
  4. Special character query `?vertical=<script>` safely defaults to general without XSS.
  5. Query with trailing spaces `?vertical=%20healthcare%20` is trimmed and resolved.
- **Case Sensitivity & Normalization**:
  1. `?vertical=HEALTHCARE` resolves to healthcare.
  2. `?vertical=Legal` resolves to legal.
  3. `?vertical=GeNeRaL` resolves to general.
  4. Subdomain `HEALTHCARE.staging.resilai.org` is case-normalized.
  5. Path `/HEALTHCARE` is case-normalized.
- **Precedence & Conflicts**:
  1. Subdomain `healthcare.staging.resilai.org` + Path `/legal` -> Path wins.
  2. Subdomain `healthcare.staging.resilai.org` + Query `?vertical=legal` -> Query wins.
  3. Path `/healthcare` + Query `?vertical=legal` -> Query wins.
  4. Conflicting header and query param in API (`?vertical=legal` + `X-ResilAI-Vertical: healthcare`) -> Query wins.
  5. Multiple query params `?vertical=healthcare&vertical=legal` handles deterministically.
- **Trailing Slashes & URL Variations**:
  1. `/healthcare/` with trailing slash resolves identical to `/healthcare`.
  2. `/legal/` with trailing slash resolves identical to `/legal`.
  3. `//healthcare` with double slash resolves safely.
  4. `/healthcare?vertical=healthcare` redundancy handled smoothly.
  5. Subdomain with trailing dot `healthcare.staging.resilai.org.` handled.
- **Offline / API Resilience**:
  1. Network failure during `GET /api/public/product-config` falls back to static config.
  2. 500 Internal Server Error from config endpoint triggers graceful fallback.
  3. Slow/timeout response does not block initial landing render.
  4. Malformed JSON payload from backend triggers static fallback.
  5. Missing fields in backend response safely defaulted by TypeScript schema.
- **Multi-Tenant Demo Rapid Switching**:
  1. Switching Acme -> Northstar Family Health -> Northstar & Cole LLP in rapid sequence.
  2. Switching tenants immediately updates active org context and persona.
  3. Report resolution switches instantly to tenant-specific telemetry.
  4. Rapid switching does not leak state across tenants.
  5. Invalid org ID selection falls back to the default vertical demo org.
- **Edge Mutation Rejections**:
  1. Mutation with custom headers still intercepted.
  2. Bulk mutation payload blocked with 403 API error.
  3. Simulated network failure during mutation check returns safe client rejection.
  4. Mutation check verifies both localStorage flag and user state.
  5. Mutation attempt does not clear read-only state or invalidate session.

### Tier 3: Cross-Feature Combinations (Pairwise Coverage, Minimum 10 Tests)
1. **Subdomain + Direct Demo Login**: Visitor arrives via `healthcare.staging.resilai.org` and clicks "Demo" -> Lands in `Northstar Family Health` demo session with clinical telemetry.
2. **Subdomain + Direct Demo Login (Legal)**: Visitor arrives via `legal.staging.resilai.org` and clicks "Demo" -> Lands in `Northstar & Cole LLP` demo session with legal telemetry.
3. **Path Navigation + Org Switcher**: Visitor arrives via `/healthcare`, enters demo, then uses the top-bar org switcher to switch to `Northstar & Cole LLP` -> Persona, reports, and banners reflect legal domain.
4. **Query Param + Contextual Banner**: Arriving via `?vertical=healthcare` sets up contextual demo banner with healthcare-specific narrative.
5. **Demo Session Persistence Across Reload**: Setting demo mode in `localStorage` and reloading the page retains demo persona, active tenant, and amber banner.
6. **Cross-Vertical Demo Transition**: Switching from `Northstar Family Health` to `Acme Technologies` immediately adjusts critical systems from EHR to Cloud/SaaS.
7. **Read-Only Guard Across Domain Pages**: Navigating through `Identity`, `Backups`, `Devices`, `Email`, and attempting remediations consistently triggers the read-only warning across all pages.
8. **Public Navbar Links Preservation**: Navigating between `About`, `Pricing`, and `Security` while on `/healthcare` maintains vertical context across all public pages.
9. **Direct URL Hash Navigation with Vertical Context**: Navigating to `/healthcare#how-it-works` scrolls to section while maintaining healthcare positioning.
10. **Sign Out from Demo**: Logging out from a vertical demo session cleanly resets demo flags and returns to the originating vertical landing page.

### Tier 4: Real-World Application Scenarios (Minimum 5 Realistic Scenarios)
1. **Scenario 1 (Clinic Managing Lead / Healthcare)**:
   - Clinic executive arrives at `healthcare.staging.resilai.org`.
   - Reads: "Incident readiness for healthcare organizations" and ransomware core question.
   - Clicks "Explore Demo".
   - Arrives at Morning Brief: Verifies `Northstar Family Health` active organization, Dr. Evelyn Reed persona.
   - Observes verified clinical workstations, EHR continuity, Veeam immutable backups, and persistent sticky amber banner.
2. **Scenario 2 (Law Firm Managing Partner / Legal)**:
   - Managing Partner visits `staging.resilai.org/legal`.
   - Reads: "Incident readiness for law firms" and client data protection question.
   - Clicks "Explore Demo".
   - Arrives at Morning Brief: Verifies `Northstar & Cole LLP` active organization, Marcus Cole persona.
   - Observes verified NetDocuments vault, Elite 3E practice management, partner laptop encryption, and persistent sticky amber banner.
3. **Scenario 3 (Enterprise CISO / General Platform)**:
   - CISO visits default staging URL `staging.resilai.org`.
   - Reads: "ResilAI — AI Incident Readiness Platform" and universal readiness question.
   - Clicks "Explore Demo".
   - Arrives at Morning Brief: Verifies `Acme Technologies` active organization, Alex Chen persona.
   - Observes verified AWS/GCP cloud environments, Okta/Entra ID identity telemetry, and persistent sticky amber banner.
4. **Scenario 4 (Compliance Auditor Invariant Verification)**:
   - Auditor inspects readiness scoring across General, Healthcare, and Legal demo tenants.
   - Confirms scoring calculation is executed purely through the shared deterministic scoring engine (`calculate_readiness_delta`).
   - Confirms AST byte-level isolation: zero LLM imports in scoring module, zero vertical-specific scoring engines exist.
5. **Scenario 5 (Demo User Mutation Prevention & Integrity)**:
   - An evaluator in demo mode attempts to trigger a remediation action (e.g., re-running a connector or modifying readiness thresholds).
   - The request is intercepted by the read-only sandbox mutation guard.
   - A clear "Read-only demo environment" toast/event is emitted; no backend data is mutated; session remains stable and isolated.

---

## 5. Coverage Thresholds

| Test Suite | Minimum Target Tests | Target Pass Rate |
|---|:---:|:---:|
| Tier 1: Feature Coverage (F1–F10) | ≥ 50 | 100% |
| Tier 2: Boundary & Corner Cases | ≥ 35 | 100% |
| Tier 3: Cross-Feature Interactions | ≥ 10 | 100% |
| Tier 4: Real-World Journeys | ≥ 5 | 100% |
| Backend Invariant & API E2E | ≥ 10 | 100% |
| **TOTAL** | **≥ 110** | **100%** |
