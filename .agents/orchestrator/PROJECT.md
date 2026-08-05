# Project: ResilAI Frontend Refactoring

## Architecture
- **Dual Workspace Architecture**: Single React application (`P:\projects\AIRS\frontend`) structured into two primary progressive layers:
  1. **Business Workspace**: Executive-level view for C-Suite and clinic managers. Focuses on high-level readiness, plain-English AI explanations, 30-second time-to-insight, and business continuity.
  2. **Operations Workspace**: Technical depth view for SecOps, SRE, and compliance officers. Preserves full evidence graph, compliance drift, tech stack lifecycle, reliability, and remediation ledger.
  3. **Administration Workspace**: Organization management, auditor access, system settings, and threshold configurations.
- **Unified Navigation & Progressive Disclosure**: Unified sidebar connecting all workspaces. Business cards support 5-tier drill-down into operational details (Clinic Ready → Business Continuity → Verification → Connector → Evidence Network) without modal application switches or losing context.
- **Design Tokens & Theme System**: Standardized Tailwind v4 theme CSS variables (`index.css`), 4px/8px grid spacing scale, typography scale, semantic status colors with proper `dark:` utility support, shadows, and elevation tokens.
- **Backend Contract Compliance (R13)**: Frontend strictly consumes backend-supplied `DailyReadinessReport` objects (`src/types/readiness.ts`) without performing client-side readiness score derivations or mock calculations.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Product & UI Audit | Comprehensive audit of every page, persona, business question, and component classification (Keep, Improve, Merge, Retire). | M1 | R0, R1 |
| 2 | Documentation Suite | Produce `UI_INVENTORY.md`, `DESIGN_SYSTEM.md`, `FEATURE_MAP.md`, `ROUTE_MAP.md`, `COMPONENT_MAP.md`, and `FRONTEND_ARCHITECTURE.md`. | M1 | R14 |
| 3 | Design Token System | Standardize Tailwind v4 theme tokens in `index.css`: 4px/8px spacing, typography scale, semantic status colors, dark mode support, and elevation. | M2 | R5, R8 |
| 4 | Component Variant Strategy | Refactor core shared components (`StatusCard`, `NorthStarHero`, `StoryActionCard`, `TrustBadge`, `Badge`) for `compact`, `expanded`, and `technical` variants. | M2 | R3 |
| 5 | Dual Workspace Layout | Unified shell layout with responsive `UnifiedSidebar` covering Dashboard, Operations, and Administration; seamless workspace zoom toggles. | M3 | R2, R6 |
| 6 | Navigation & Route Migration | Route inventory migration in `App.tsx` matching `ROUTE_MAP.md`; remove hardcoded `IS_READINESS_PRODUCT` flag redirect; preserve all routes. | M3 | R6, R10 |
| 7 | Progressive Disclosure Mechanics | 5-tier drill-down from executive summary cards into operational checks, connector details, and evidence graphs via inline expanders / slide-overs. | M4 | R7 |
| 8 | AI Translator Panel | Interactive AI Assistant UI panel consuming deterministic `DailyReadinessReport` to present natural language readiness explanations and recommended actions. | M4 | R4, R13 |
| 9 | Operations Workspace Integration | Remap legacy technical tools (`EvidenceNetwork`, `ComplianceDrift`, `TechnologyIntelligence`, `ReliabilityDashboard`, `RemediationLedger`, `AIAttackSimulationLab`). | M5 | R3, R9 |
| 10 | Administration Workspace & Auditor Access | Remap organization settings, audit calendar, auditor view, and system settings into Admin workspace menu. | M5 | R0, R10 |
| 11 | State & API Compliance Remediation | Fix legacy components violating R13 (remove client-side score math in `ResultsTabs`, `CompetitorParityChart`, `Analytics`, `useMockTrustData`). | M5 | R11, R13 |
| 12 | Accessibility, Theme & Offline Hardening | Implement ARIA roles, focus rings, keyboard nav, full dark mode compatibility, offline state detection (`navigator.onLine`), loading skeletons. | M6 | R12, R15 |
| 13 | Final Build & Forensic Audit Gate | Ensure `npm run build` completes with exit code 0; pass Reviewer, Challenger, and Forensic Auditor verification gates. | M6 | Acceptance Criteria |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Documentation Suite | Draft `UI_INVENTORY.md`, `DESIGN_SYSTEM.md`, `FEATURE_MAP.md`, `ROUTE_MAP.md`, `COMPONENT_MAP.md`, `FRONTEND_ARCHITECTURE.md`. | none | DONE |
| M2 | Design System & Component Primitives | Implement token CSS in `index.css` and variant-enabled UI primitives (`StatusCard`, `StoryActionCard`, `NorthStarHero`, `TrustBadge`, `Badge`). | M1 | IN_PROGRESS |
| M3 | Dual Workspace Layout & Navigation | Implement `DualWorkspaceLayout`, `UnifiedSidebar`, and update `App.tsx` routing according to `ROUTE_MAP.md`. | M2 | PLANNED |
| M4 | Business Workspace & AI Translator Panel | Implement executive views (`TodayPage`, `NeedsAttentionPage`, `RecoveryReadinessPage`, `ActivityPage`) with AI Translator Panel and progressive disclosure. | M3 | PLANNED |
| M5 | Operations Workspace & Legacy Integration | Remap legacy components (`EvidenceNetwork`, `ComplianceDrift`, `TechnologyIntelligence`, etc.) into Operations/Admin, fix R13 contract violations. | M4 | PLANNED |
| M6 | Accessibility, Build & Forensic Verification | Verify a11y, theme support, offline states, run `npm run build`, and complete Forensic Integrity Audit. | M5 | PLANNED |

## Interface Contracts
### DailyReadinessReport Contract (Frozen - `src/types/readiness.ts`)
```typescript
export interface DailyReadinessReport {
  status: 'safe_to_open' | 'action_needed' | 'critical_risk' | 'unknown';
  clinic_health_pct: number;
  connector_health_pct: number;
  greeting: string;
  summary: string;
  timeline: TimelineEvent[];
  business_continuity: BusinessContinuity;
  passed_checks: ReadinessCheck[];
  failed_checks: ReadinessCheck[];
  warnings: ReadinessCheck[];
  unknowns: UnknownItem[];
  immediate_actions: ActionCard[];
  coverage: CoverageReport;
  connectors: ConnectorReadiness[];
  verification: VerificationContext;
  trend: ReadinessTrend;
  value: ValueSummary;
  generated_at: string;
}
```

### Component Variant Contract
```typescript
export type ComponentVariant = 'compact' | 'expanded' | 'technical';

export interface VariantProps {
  variant?: ComponentVariant;
}
```

## Code Layout
- `P:\projects\AIRS\frontend\`
  - `src/`
    - `index.css` (Tailwind v4 tokens, CSS variables, typography, animations, dark mode)
    - `App.tsx` (Unified router, Dual Workspace routes, providers)
    - `types/` (Backend contracts & readiness data models)
    - `components/`
      - `ui/` (Reusable primitive components: Badge, Button, Modal, Skeleton, Toast, Tooltip)
      - `layout/` (DualWorkspaceLayout, UnifiedSidebar, Header, WorkspaceToggle)
      - `readiness/` (NorthStarHero, StoryActionCard, AITranslatorPanel, StatusCard)
    - `features/`
      - `readiness/` (Business Workspace pages: TodayPage, NeedsAttentionPage, RecoveryReadinessPage, ActivityPage)
      - `operations/` (Operations Workspace views: EvidenceNetwork, ComplianceDrift, TechStack, Reliability, Remediation, Simulation)
      - `admin/` (Admin Workspace views: Organizations, AuditCalendar, Settings)
  - `UI_INVENTORY.md`
  - `DESIGN_SYSTEM.md`
  - `FEATURE_MAP.md`
  - `ROUTE_MAP.md`
  - `COMPONENT_MAP.md`
  - `FRONTEND_ARCHITECTURE.md`
