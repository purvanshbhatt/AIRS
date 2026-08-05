# Original User Request

## Initial Request — 2026-08-03T20:11:20Z

<USER_REQUEST>
# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Multi-agent teamwork system is executing the prompt.

Refactor the ResilAI frontend into a Dual Workspace Architecture (Business and Operations) using progressive disclosure. Maximize reuse of existing UI components and extract standard design tokens, avoiding a complete rewrite.

Working directory: P:\projects\AIRS\frontend

Integrity mode: development

## Requirements

### R0. Product Audit
Before generating the UI Inventory, perform a full product audit. For every page, determine its target persona, business question, appropriate workspace (Business, Operations, Admin), duplication status, and alignment with the ResilAI vision. Do not classify by technical implementation alone.

### R1. UI Component Audit
Generate a comprehensive `UI_INVENTORY.md` document prior to making any code changes, categorizing every existing page and component as Keep, Improve, Merge, or Retire with a short justification.

### R2. Dual Workspace Layout
Implement a single application with two progressive layers: a Business Workspace (executive summary) and an Operations Workspace (technical depth). Implement a unified sidebar covering Dashboard, Operations, and Administration.

### R3. Component Preservation & Variant Strategy
Do not duplicate components for different workspaces. Instead, refactor existing components (e.g., StatusCard) to support `compact`, `expanded`, and `technical` variants. Preserve valuable legacy components like EvidenceNetwork, ComplianceDrift, and TechnologyIntelligence by remapping them into the Operations workspace.

### R4. AI Translator Panel
Implement a UI panel for an AI Assistant that translates the deterministic `DailyReadinessReport` into natural language explanations (Why readiness dropped, what changed, recommended actions). Use realistic mock responses, not hardcoded fake intelligence logic.

### R5. Design System Standardization
Extract spacing, colors, radius, icons, shadows, animations, and typography into reusable design tokens before creating new UI to ensure a cohesive, premium aesthetic. Document these in `DESIGN_SYSTEM.md`.

### R6. Preserve Navigation Flow
Do not create two disconnected workspaces. Business and Operations must feel like different zoom levels of the same application. Avoid modal application switches; users should naturally drill into technical detail from business views.

### R7. Progressive Disclosure
Every business card should support expansion into operational detail (e.g. Clinic Ready → Business Continuity → Verification → Connector → Evidence). The user should never feel they left the product.

### R8. Build a Real Design System
Create a reusable design system extracting the spacing scale, typography scale, semantic colors, shadows, border radius, transitions, icons, status colors, badges, elevation, and grid system.

### R9. Feature Mapping
Create `FEATURE_MAP.md` tracking Old Component → New Component → Reason → Status → Location to prevent lost functionality.

### R10. Route Inventory
Generate `ROUTE_MAP.md` containing Current Route → Future Route → Redirect → Deprecated → Owner. No routes should disappear accidentally.

### R11. State Management Audit
Audit React Context, TanStack Query, Redux, Local State, API Cache, and Loading State before adding new state to avoid duplication.

### R12. Accessibility Review
Every page must pass keyboard navigation, ARIA, focus, contrast, responsive layout, empty state, loading state, unknown state, and offline state reviews.

### R13. Backend Contract Compliance
The frontend must consume only the frozen backend contract. No business calculations, derived readiness, score computation, or connector inference on the frontend. Display exactly what the backend provides.

### R14. Documentation Suite
Produce `UI_INVENTORY.md`, `DESIGN_SYSTEM.md`, `FEATURE_MAP.md`, `ROUTE_MAP.md`, `COMPONENT_MAP.md`, and `FRONTEND_ARCHITECTURE.md`. These become the frontend constitution.

### R15. Final Deliverable
The result must look like a premium SaaS product designed for executives and IT teams, featuring a cohesive visual language, progressive disclosure, and reusable components. It should not look like a refactored cybersecurity dashboard.

## Acceptance Criteria

### Programmatic Verification
- [ ] `npm run build` executes in the `frontend` directory and completes with exit code 0 (no TypeScript or Vite build errors).

### Independent Agent Review (UX Validation)
- [ ] An independent evaluator agent confirms that `UI_INVENTORY.md`, `FEATURE_MAP.md`, `ROUTE_MAP.md`, and `DESIGN_SYSTEM.md` were generated and contain exhaustive audits.
- [ ] An independent evaluator agent confirms that legacy components (e.g., EvidenceNetwork, TechnologyIntelligence) were reused and mapped into Operations rather than rewritten.
- [ ] **UX Validation**: Independent verification confirms no duplicated components were introduced, existing high-quality UI was preserved, every page has a clear target persona, and navigation follows progressive disclosure.
- [ ] **UX Validation**: Independent verification confirms Business users can determine clinic readiness within 30 seconds, and IT users can drill into technical details without leaving the application (feels like a single cohesive experience).
</USER_REQUEST>

## Follow-up — 2026-08-04T00:52:00Z

<USER_REQUEST>
# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Teamwork Multi-Agent System is executing the prompt.

Refactor the ResilAI frontend to build out the Operations workspace using domain-specific "mini-products" (Identity, Devices, Backups, Email, Network, Cloud, AI) that adhere to a story-first flow and a strict business-first UI principle.

Working directory: P:\projects\AIRS\frontend
Integrity mode: development

## Requirements

### R1. Unified Sidebar Navigation
Modify `src/components/layout/AppSidebar.tsx` to group navigation without a workspace toggle (assume RBAC hides it for executives). Groups must be:
- **Morning Operations**: Morning Brief, Needs Attention, Recovery, Yesterday
- **Technology Operations**: Identity, Devices, Backups, Email, Network, Cloud, AI
- **Platform**: Connectors, Activity, Audit, Settings

### R2. Core Architectural Principle
Every Technology Operations domain page must begin with a Summary Card that provides a one-sentence business answer ("So what?") before presenting any technical evidence. Technical telemetry must always be subordinate to operational context. 

### R3. Evidence Drawer Refactor
Update `src/components/readiness/AIDrawer.tsx` (internally keep this name) to display "How do we know?" in the UI. 
- Top section: Deterministic evidence (Target, Timestamp, Confidence, Source, Raw metrics).
- Middle section: "Why this matters" (Operational AI summary).
- Bottom section: A link to view technical details in the specific domain page.

### R4. Domain Mini-Products
Implement a layout for Technology Operations where each domain (e.g., Backups) acts as its own mini-product. Reuse existing widgets (`ScoreTrendChart`, `Timeline`, etc.) underneath the new Summary Cards within these domain pages. Update `src/App.tsx` routes accordingly.

## Acceptance Criteria

### Execution & Architecture
- [ ] `AppSidebar.tsx` has no workspace toggle and strictly follows the new grouping.
- [ ] `AIDrawer.tsx` prioritizes deterministic evidence over AI summaries and includes a navigation link to a domain.
- [ ] At least one Domain page (e.g., Backups or Identity) is implemented to demonstrate the mini-product structure (Overview, Events, Issues, etc.) and starts with a business summary card.
- [ ] The app builds successfully (`npm run build`) with no TypeScript errors.
</USER_REQUEST>

## Follow-up — 2026-08-04T19:21:02Z

<USER_REQUEST>
# Teamwork Project Prompt — Draft

> Status: Ready for launch — awaiting user approval.
> Goal: Craft prompt → get user approval → delegate to teamwork_preview

Execute ResilAI Sprint 3: Platform Consolidation & Production Readiness. Consolidate the legacy frontend components, themes, and authentication into the new Domain Architecture and perform a mandatory End-to-End Staging Deployment validation.

Working directory: `P:\projects\AIRS\frontend`
Integrity mode: demo

Reference Document: See `implementation_plan.md` for exact sprint phases, rules (Zero Regression, Harvest First), and delivery constraints.

## Requirements

### R1. Platform Consolidation & Audit (Phases 1-8)
Execute the exact 8 phases of platform consolidation as detailed in `implementation_plan.md`. This includes auditing and safely pruning legacy code, reconnecting the Theme System and Firebase Auth, establishing the single source of truth, overhauling terminology (e.g., "Verification" -> "Health Check"), configuring the First-Class Sales Demo Mode, and measuring performance. You must never delete code without first removing references and passing the build.

### R2. Staging Deployment & Validation (Phase 9)
You must deploy the consolidated frontend to the existing Firebase Hosting staging environment and deploy the backend to the existing Cloud Run staging service. Do not create duplicate staging services. After deployment, you must perform end-to-end integration validation against the staging URLs to verify authentication, API endpoints (CORS), and the Demo Mode flow. Localhost validation alone is strictly prohibited as the Definition of Done.

### R3. Final Deliverables
Generate all 13 canonical deliverable reports (e.g., `PRODUCT_MAP.md`, `STAGING_TEST_REPORT.md`, etc.) outlining the consolidated architecture, deployment success, and regression/performance metrics.

## Acceptance Criteria

### Build & Audit
- [ ] `npm run build` succeeds with exit code 0.
- [ ] No TypeScript errors or ESLint warnings exist.
- [ ] No duplicate providers, layouts, or routing systems remain.

### Staging Validation
- [ ] The frontend staging URL is accessible and loads the application.
- [ ] Firebase authentication successfully logs in a user and maintains session persistence without 401 loops.
- [ ] API calls to the staging backend succeed without CORS errors.
- [ ] The Demo Mode (Acme Health Systems) fully populates without any blank states.

### Documentation
- [ ] All 13 mandatory markdown deliverables have been created or updated in the `.gemini/antigravity/brain/` artifact directory.
</USER_REQUEST>
