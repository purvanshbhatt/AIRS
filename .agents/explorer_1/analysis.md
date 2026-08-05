# ResilAI Frontend Operations Workspace Investigation & Architecture Analysis

**Document Version:** 1.0.0  
**Target Directory:** `P:\projects\AIRS\frontend`  
**Working Directory:** `P:\projects\AIRS\.agents\explorer_1`  
**Author:** Explorer Agent  

---

## 1. Executive Summary

This report delivers a thorough architectural analysis of the ResilAI frontend codebase (`P:\projects\AIRS\frontend`) for requirements R1 through R4 specified in the prompt follow-up. 

The investigation covers four key areas:
1. **Sidebar Navigation (`src/components/layout/AppSidebar.tsx`)**: Removing legacy grouping and establishing a workspace-toggle-free, strictly grouped navigation model covering Morning Operations, Technology Operations, and Platform.
2. **Evidence Drawer (`src/components/readiness/AIDrawer.tsx`)**: Refactoring the AI drawer to display "How do we know?" as the primary title/header, placing deterministic evidence at the top, operational AI summary in the middle, and domain-specific navigation at the bottom.
3. **Technology Operations Domain Pages & Summary Cards**: Designing a reusable `DomainSummaryCard` ("So what?" business summary answer) and mini-product structure (`Overview`, `Events`, `Issues`, `Inventory`) for technology domains, focusing on `Backups` and `Identity` as primary implementations while reusing existing widgets (`ScoreTrendChart`, `EvidenceTimeline`, `StatusCard`, `TrustBadge`).
4. **App Routing (`src/App.tsx`)**: Remapping application routes to support domain mini-products and clean navigation endpoints with seamless backward-compatible redirects.

---

## 2. Component Inspection Findings

### 2.1 Navigation & Layout (`src/components/layout/AppSidebar.tsx`)

#### Current State Analysis
- File path: `P:\projects\AIRS\frontend\src\components\layout\AppSidebar.tsx`
- Currently imports icons from `lucide-react` and defines three navigation groups: `TODAY`, `EXPLORE`, and `ADMINISTRATION`.
- There is **no workspace toggle** currently present in `AppSidebar.tsx`.
- Current route paths bound in sidebar:
  - `TODAY`: Morning Brief (`/dashboard/today`), Needs Attention (`/dashboard/attention`), Recovery (`/dashboard/recovery`), Activity (`/dashboard/activity`).
  - `EXPLORE`: Verification (`/explore/verification`), Evidence (`/explore/evidence`), Systems (`/explore/systems`), Integrations (`/explore/integrations`), History (`/explore/history`).
  - `ADMINISTRATION`: Team (`/admin/team`), Integrations (`/admin/integrations`), Audit (`/admin/audit`), Settings (`/admin/settings`).

#### Requirements Mapping (R1)
Group sidebar items strictly into three explicit sections without any workspace toggle dropdown or switch:

```typescript
export const NAV_GROUPS = [
  {
    label: 'Morning Operations',
    items: [
      { label: 'Morning Brief', icon: LayoutDashboard, path: '/morning-brief' },
      { label: 'Needs Attention', icon: Zap, path: '/needs-attention' },
      { label: 'Recovery', icon: ShieldAlert, path: '/recovery' },
      { label: 'Yesterday', icon: History, path: '/yesterday' },
    ]
  },
  {
    label: 'Technology Operations',
    items: [
      { label: 'Identity', icon: Users, path: '/identity' },
      { label: 'Devices', icon: Laptop, path: '/devices' },
      { label: 'Backups', icon: Database, path: '/backups' },
      { label: 'Email', icon: Mail, path: '/email' },
      { label: 'Network', icon: Network, path: '/network' },
      { label: 'Cloud', icon: Cloud, path: '/cloud' },
      { label: 'AI', icon: Cpu, path: '/ai' },
    ]
  },
  {
    label: 'Platform',
    items: [
      { label: 'Connectors', icon: Cable, path: '/connectors' },
      { label: 'Activity', icon: Activity, path: '/activity' },
      { label: 'Audit', icon: ShieldCheck, path: '/audit' },
      { label: 'Settings', icon: Settings, path: '/settings' },
    ]
  }
];
```

#### Proposed Code Snippet / Patch for `AppSidebar.tsx`
```tsx
// Updated lucide-react imports
import { 
  LayoutDashboard, Zap, ShieldAlert, History,
  Users, Laptop, Database, Mail, Network, Cloud, Cpu,
  Cable, Activity, ShieldCheck, Settings
} from 'lucide-react';
```

---

### 2.2 Evidence Drawer (`src/components/readiness/AIDrawer.tsx`)

#### Current State Analysis
- File path: `P:\projects\AIRS\frontend\src\components\readiness\AIDrawer.tsx`
- Referenced inside `src/components/readiness/StatusCard.tsx` when clicking the "Explain" button.
- Current UI layout:
  - Header: Displays `<Sparkles /> AI Explanation`.
  - Body: 
    1. Subject (`title`)
    2. What Changed (`explanation.whatChanged`)
    3. How Do We Know (`explanation.howWeKnow` & confidence percentage)
    4. Evidence Snippet (`explanation.rawEvidencePreview`)
  - Footer: Button labeled "View Full Technical Evidence".

#### Refactoring Specifications (R3)
The drawer must prioritize **deterministic evidence** over AI narrative and connect directly to domain technical pages.

1. **Header**: Change title from "AI Explanation" to **"How do we know?"** with `ShieldCheck` or `CheckCircle2` icon.
2. **Top Section: Deterministic Evidence**:
   - Target / Asset identifier (e.g. `target || action.title`)
   - Verification Timestamp (e.g. `timestamp || action.last_verified_at`)
   - Telemetry Confidence Level (e.g. `98% Deterministic Telemetry`)
   - Verification Source / Connector (e.g. `Veeam Backup API v12` / `Microsoft Graph API`)
   - Raw metrics / JSON evidence preview.
3. **Middle Section: Operational AI Summary ("Why this matters")**:
   - Plain-language narrative explaining operational risk, business continuity implications, and recommendation rationale.
4. **Bottom Section: Domain Technical Details Link**:
   - Navigation button/link pointing directly to the target Technology Operations domain mini-product page (e.g. `View Technical Details in Backups Domain →` linking to `/backups`).

#### Proposed Interface Enhancement for `AIDrawer.tsx`:
```typescript
export interface AIDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  target?: string;
  timestamp?: string;
  confidence?: number;
  source?: string;
  rawMetrics?: Record<string, string | number>;
  rawEvidencePreview?: string;
  whyItMatters?: string;
  domainPath?: string;
  domainLabel?: string;
  onViewDomainDetails?: () => void;
}
```

---

### 2.3 Technology Operations Domain Pages & Summary Cards (R2 & R4)

#### Current State Analysis
- Currently, technology intelligence is presented as a single page (`src/pages/TechnologyIntelligence.tsx`) with generic tabs: `inventory`, `lifecycle`, `exposure`, `dependencies`, `timeline`, `insights`.
- No domain-specific mini-products currently exist for `Backups`, `Identity`, `Devices`, `Email`, `Network`, `Cloud`, or `AI`.
- High-value existing reusable widgets available for composition:
  - `ScoreTrendChart` (`src/components/ScoreTrendChart.tsx`): Recharts-driven readiness score trend over time.
  - `EvidenceTimeline` (`src/components/dashboard/EvidenceTimeline.tsx`): Chronological evidence stream with cryptographic hash copying and verification drift links.
  - `StatusCard` (`src/components/readiness/StatusCard.tsx`): Multi-variant card supporting `hero`, `story`, `compact`, and `technical` variants with inline fix triggers.
  - `TrustBadge` (`src/components/readiness/TrustBadge.tsx`): Confidence badge indicating verified vs self-attested status.

#### Component Design: Domain Summary Card (`src/components/technology/DomainSummaryCard.tsx`)
In accordance with **R2**, every Technology Operations domain page MUST start with a Summary Card answering the business question ("So what?") in plain language before showing technical metrics.

```tsx
interface DomainSummaryCardProps {
  domainName: string; // e.g. "Backups & Disaster Recovery"
  status: 'ready' | 'warning' | 'error';
  readinessScore: number; // e.g. 98
  businessAnswer: string; // "100% of critical healthcare databases and user backups are verified recoverable with RPO < 15m."
  lastVerifiedText: string; // "Verified 12m ago via Veeam Connector"
  keyMetrics: Array<{
    label: string;
    value: string;
    status?: 'good' | 'warning' | 'error';
  }>;
}
```

#### Mini-Product Structure for Domain Pages (R4)
Each Technology Operations domain (focusing on `Backups` and `Identity` as primary implementations) will act as a mini-product with a unified tabbed layout:

1. **Header & Summary Card**:
   - Domain Icon & Title (e.g., `Backups & Disaster Recovery` / `Identity & Access Management`)
   - Organization selector dropdown
   - **`DomainSummaryCard`** ("So what?" business summary)
2. **Mini-Product Tabs**:
   - `Overview`: Summary card, `ScoreTrendChart` (readiness trend), high-level domain health metrics, active safeguards.
   - `Events`: Telemetry logs and evidence verification using `EvidenceTimeline`.
   - `Issues`: Actionable domain risks rendering `StatusCard` components in `story` or `technical` variants.
   - `Inventory`: Infrastructure asset table (e.g. Backup Jobs list, MFA coverage list).

---

### 2.4 Application Routing (`src/App.tsx`)

#### Current State Analysis
- File path: `P:\projects\AIRS\frontend\src\App.tsx`
- Uses `react-router-dom` `Routes` and `Route` wrapped in `ProtectedRoute` and `AppLayout`.

#### Target Route Inventory & Mapping (R1, R4)

| Domain / Group | Route Path | Component | Alias / Legacy Redirect |
|---|---|---|---|
| **Morning Operations** | `/morning-brief` | `TodayPage` | `/dashboard/today` -> `/morning-brief` |
| | `/needs-attention` | `NeedsAttentionPage` | `/dashboard/attention` -> `/needs-attention` |
| | `/recovery` | `RecoveryReadinessPage` | `/dashboard/recovery` -> `/recovery` |
| | `/yesterday` | `ActivityPage` | `/dashboard/activity` -> `/yesterday` |
| **Technology Operations** | `/identity` | `IdentityPage` (New) | `/explore/systems` -> `/identity` |
| | `/devices` | `DevicesPage` (New) | - |
| | `/backups` | `BackupsPage` (New) | - |
| | `/email` | `EmailPage` (New) | - |
| | `/network` | `NetworkPage` (New) | - |
| | `/cloud` | `CloudPage` (New) | - |
| | `/ai` | `AIPage` (New) | `/explore/integrations` -> `/ai` |
| **Platform** | `/connectors` | `Integrations` | `/admin/integrations` -> `/connectors` |
| | `/activity` | `EvidenceNetwork` | `/explore/verification` -> `/activity` |
| | `/audit` | `AuditCalendar` | `/admin/audit` -> `/audit` |
| | `/settings` | `Settings` | `/admin/settings` -> `/settings` |

---

## 3. Recommended Implementation Roadmap

1. **Step 1: Navigation Refactor (`AppSidebar.tsx`)**
   - Update `navGroups` to match Morning Operations, Technology Operations, Platform.
   - Remove any workspace toggle logic or unnecessary headers.

2. **Step 2: Evidence Drawer Refactor (`AIDrawer.tsx`)**
   - Update header to "How do we know?".
   - Move deterministic evidence (target, timestamp, confidence, source, metrics) to the top section.
   - Position "Why this matters" AI summary in the middle section.
   - Add domain navigation link button at the bottom.

3. **Step 3: Domain Summary Card & Mini-Product Component Creation**
   - Create `src/components/technology/DomainSummaryCard.tsx`.
   - Create `src/pages/technology/BackupsPage.tsx` and `src/pages/technology/IdentityPage.tsx` using `DomainSummaryCard`, `ScoreTrendChart`, `EvidenceTimeline`, `StatusCard`.
   - Create stub mini-product pages for `DevicesPage`, `EmailPage`, `NetworkPage`, `CloudPage`, `AIPage`.

4. **Step 4: Router Registration (`App.tsx`)**
   - Import new domain pages and register canonical routes (`/morning-brief`, `/identity`, `/backups`, etc.).
   - Add backwards-compatible `<Navigate>` redirects for legacy `/dashboard/*` and `/explore/*` paths.

---

## 4. Verification Method

- Build Verification: Run `npm run build` in `P:\projects\AIRS\frontend` (must exit code 0 with no TypeScript errors).
- UI Verification: Check navigation items, drawer sections, and domain mini-product tab structure.
