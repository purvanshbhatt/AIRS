# E2E Test Infra: ResilAI Authenticated Experience

## Test Philosophy
- **Opaque-box, requirement-driven**: Verifies user workflows and visual/data commitments without binding to internal implementation details.
- **Methodology**: 4-Tier verification (Tier 1: Feature Coverage, Tier 2: Boundary & Corner Cases, Tier 3: Cross-Feature Navigation, Tier 4: Real-World Persona Journeys) + Tier 5 Adversarial Coverage Hardening.

---

## Feature Inventory Mapping
| # | Feature | Requirement | Tier 1 (Count) | Tier 2 (Count) | Tier 3 (Cross) | Tier 4 (Journeys) |
|---|---------|-------------|:--------------:|:--------------:|:--------------:|:-----------------:|
| 1 | TodayPage Narrative Hierarchy (5 stages) | R1 | 5 | 5 | ✓ | ✓ |
| 2 | Executive-First 4-Tier Progressive Disclosure | R2 | 5 | 5 | ✓ | ✓ |
| 3 | 6-Step Getting Started & Onboarding | R3 | 5 | 5 | ✓ | ✓ |
| 4 | Contextual Demo Mode Disclaimers & Guidance | R4 | 5 | 5 | ✓ | ✓ |
| 5 | Simplified Explanation / "Explain for Leadership" | R5 | 5 | 5 | ✓ | ✓ |
| 6 | Report Center & Generation History | R6 | 5 | 5 | ✓ | ✓ |
| 7 | Documents Vault & Governance Modernization | R7 | 5 | 5 | ✓ | ✓ |
| 8 | Design Consistency, A11y & Mobile (375px) | R8 | 5 | 5 | ✓ | ✓ |

---

## Test Architecture
- **Test Runner**: Vitest / Node.js test harness configured in `frontend/src/test/`
- **Verification Execution**: `npm run test` / `npx vitest run` or automated node runner.
- **Directory Layout**:
  - `src/test/tier1-feature-coverage.test.ts` (>=40 test cases covering F1-F8)
  - `src/test/tier2-boundary-corner.test.ts` (>=40 boundary test cases: 0-systems, 401 handling, demo mutation blockers, 375px mobile responsiveness)
  - `src/test/tier3-cross-feature.test.ts` (>=10 pairwise cross-workspace flows)
  - `src/test/tier4-real-world-scenarios.test.ts` (>=5 end-to-end persona journeys: Executive 30s brief, IT triage & fix, 6-step onboarding, demo vs live org)

---

## Coverage Thresholds
- Tier 1: ≥5 per feature (Total ≥ 40)
- Tier 2: ≥5 per feature (Total ≥ 40)
- Tier 3: ≥10 cross-feature combinatorial interactions
- Tier 4: ≥5 realistic executive & IT operator application journeys
- **Total Minimum Target**: ≥ 95 test cases
