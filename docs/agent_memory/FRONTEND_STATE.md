# Frontend State

Core Layer: React (18.3.1), Vite (6.4.1), TypeScript (5.5.3), TailwindCSS (4.1.18)
Client Router: React Router
API Client: `frontend/src/api.ts`

Recent Changes:
- 2026-08-31 ResilAI Authenticated Product Experience & Identity Refactoring:
  - Overhauled authenticated dashboard into a 5-stage narrative hierarchy (*Readiness Hero → Why → Needs Attention → Recommended Actions → Evidence Provenance*).
  - Built 4-tier progressive disclosure model in `ExecutiveExplanation.tsx` and `AIDrawer.tsx`.
  - Implemented 6-step guided Getting Started workflow (`Onboarding.tsx`) with per-org persistence and top-bar launch trigger.
  - Added Contextual Demo Mode guidance banner and dismissible section explanations.
  - Added "Explain for Leadership" drawer calling backend narrative endpoint.
  - Modernized Documents and Governance pages, removing legacy 5-domain questionnaire framing.
  - Passed 124/124 Vitest tests; built and deployed production bundle cleanly.
- Production Productization & Executive UX Recovery:
  - High-taste Executive Zero-Evidence State: When an organization is live but has no connectors, renders the polished "Not Yet Verified" posture ("Your readiness journey starts here", "Status: Not Yet Verified", "What we know: No security systems connected / No telemetry received / No verified evidence available", "Next step: Connect a security system").
  - Organization Onboarding Guard: When a user has 0 organizations, `TodayPage.tsx` directly renders the "Set up your readiness workspace" card with a `[Create Organization]` button linking to `/onboarding`.
  - Unmistakable Environment Distinction: Amber badge for `DEMO WORKSPACE (SIMULATED DATA)` vs emerald badge for `LIVE WORKSPACE` in `ReadinessHeader.tsx`.
  - Methodology & Operating Model Overhaul: Completely updated `/docs/methodology` to feature the 5-Stage Verification Operating Model (1. Connect → 2. Verify → 3. Measure → 4. Explain → 5. Improve) with interactive persona switching.
  - Contextual Error Formatting: Fixed `api.ts` error prefixing to prevent duplicate "Not found: Not Found" strings.
  - Pure SVG Icons: Sidebar and headers standardized on Lucide React SVG components with zero font ligature dependencies.
  - Production Homepage Acquisition Optimization (`Landing.tsx`): Primary conversion CTA set to "Get Started" linking directly to Google Login / unified auth (`/login`); removed redundant "Request Pilot" CTAs.
  - Bounded build checks confirmed 100% green TypeScript compilation and production packaging (`npm run build`, `npm run build:staging`, `npm run build:production`, and live Firebase deployments to all 4 targets).

Next Tasks:
- Monitor live self-serve Google Login conversion and organization onboarding.
- Track design-partner qualification conversion triggers post-remediation.

