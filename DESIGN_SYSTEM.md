# ResilAI Design System Specification

**Document Version:** 1.0.0  
**Target Application:** ResilAI Frontend (`P:\projects\AIRS\frontend`)  
**Design Tokens Standard:** Tailwind CSS v4 Theme Variables & Utility Classes (R5, R8)  
**Author:** Milestone 1 Documentation Suite Worker  

---

## 1. Executive Summary & Design System Architecture

The ResilAI Design System provides a unified, enterprise-grade aesthetic for healthcare executive and technical IT operations users. Satisfying **R5 (Design System Standardization)** and **R8 (Build a Real Design System)**, this specification extracts all spacing scales, typography hierarchies, semantic colors, status badge variants, elevation levels, border radiuses, icon conventions, and grid breakpoints into explicit design tokens.

The design system enforces a **Dual-Theme Architecture** supporting seamless light and dark mode operations through CSS custom variables in `src/index.css` and dark variant Tailwind classes (`dark:` utilities).

---

## 2. CSS Variables & Tailwind v4 Tokens Setup (`src/index.css`)

```css
@import "tailwindcss";

@layer base {
  :root {
    /* Color Palette - Primary Brand (Emerald Green) */
    --color-primary-50: #e5faf0;
    --color-primary-100: #c2f5dc;
    --color-primary-500: #00c853;
    --color-primary-600: #00b047;
    --color-primary-700: #008a37;
    --color-primary-950: #00290e;

    /* Color Palette - Secondary Accent (Titanium Blue) */
    --color-blue-50: #ecf3ff;
    --color-blue-100: #d4e3ff;
    --color-blue-500: #2979ff;
    --color-blue-600: #1c64e6;
    --color-blue-700: #124cb8;
    --color-blue-950: #071940;

    /* Status Colors - Light Theme Default */
    --status-safe-bg: #f0fdf4;
    --status-safe-text: #15803d;
    --status-safe-border: #bbf7d0;

    --status-warning-bg: #fffbeb;
    --status-warning-text: #b45309;
    --status-warning-border: #fef08a;

    --status-danger-bg: #fef2f2;
    --status-danger-text: #b91c1c;
    --status-danger-border: #fecaca;

    --status-unknown-bg: #f8fafc;
    --status-unknown-text: #475569;
    --status-unknown-border: #e2e8f0;

    /* Neutral Light Surfaces */
    --color-surface-bg: #f8fafc;
    --color-surface-card: #ffffff;
    --color-surface-canvas: #f1f5f9;
    --color-border-subtle: #e2e8f0;
    --color-border-strong: #cbd5e1;
    --color-text-primary: #0f172a;
    --color-text-secondary: #475569;
    --color-text-muted: #94a3b8;

    /* Elevation & Shadows */
    --shadow-card: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    --shadow-soft: 0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04);
    --shadow-medium: 0 4px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    --shadow-focus: 0 0 0 3px rgba(41, 121, 255, 0.35);

    /* Border Radius Scale */
    --radius-sm: 4px;
    --radius-md: 6px;
    --radius-lg: 8px;
    --radius-xl: 12px;
    --radius-2xl: 16px;
    --radius-full: 9999px;
  }

  .dark {
    /* Status Colors - Dark Theme Overrides */
    --status-safe-bg: rgba(6, 78, 59, 0.4);
    --status-safe-text: #4ade80;
    --status-safe-border: #065f46;

    --status-warning-bg: rgba(120, 53, 15, 0.4);
    --status-warning-text: #fbbf24;
    --status-warning-border: #92400e;

    --status-danger-bg: rgba(127, 29, 29, 0.4);
    --status-danger-text: #f87171;
    --status-danger-border: #991b1b;

    --status-unknown-bg: rgba(30, 41, 59, 0.6);
    --status-unknown-text: #94a3b8;
    --status-unknown-border: #334155;

    /* Neutral Dark Surfaces */
    --color-surface-bg: #121212;
    --color-surface-card: #1e1e1e;
    --color-surface-canvas: #181818;
    --color-border-subtle: #2d2d2d;
    --color-border-strong: #404040;
    --color-text-primary: #f8fafc;
    --color-text-secondary: #cbd5e1;
    --color-text-muted: #64748b;

    /* Elevation & Shadows - Dark Theme */
    --shadow-card: 0 1px 3px 0 rgba(0, 0, 0, 0.5), 0 1px 2px 0 rgba(0, 0, 0, 0.3);
    --shadow-soft: 0 4px 20px 0 rgba(0, 0, 0, 0.4);
    --shadow-medium: 0 8px 30px 0 rgba(0, 0, 0, 0.6);
  }
}
```

---

## 3. Spacing Scale (4px / 8px Base Grid)

The grid layout adheres to a strict 4px / 8px base spacing scale. All component paddings, margins, flex gaps, and grid layouts must use standard spacing tokens.

| Token | Pixel Value | Rem Equivalent | Primary Design System Application |
|---|---|---|---|
| `--spacing-1` | `4px` | `0.25rem` | Micro-gaps between inline badges, pill tags, and indicator dots. |
| `--spacing-2` | `8px` | `0.5rem` | Standard gap between button icons and text labels; compact list item padding. |
| `--spacing-3` | `12px` | `0.75rem` | Internal padding for compact buttons, input controls, and table cells. |
| `--spacing-4` | `16px` | `1.0rem` | **Default Grid Gap**: Standard padding inside cards, modals, and list items. |
| `--spacing-6` | `24px` | `1.5rem` | **Section Gap**: Vertical spacing between dashboard card rows and section containers. |
| `--spacing-8` | `32px` | `2.0rem` | Page container padding for desktop viewports; hero banner inner padding. |
| `--spacing-12` | `48px` | `3.0rem` | Major vertical section separation in executive landing and report views. |
| `--spacing-16` | `64px` | `4.0rem` | Top-level layout container margins and hero header spacing. |

---

## 4. Typography Scale & Hierarchy

The font family is set to **Inter** (`ui-sans-serif, system-ui, sans-serif`). The typography hierarchy defines clear typographic levels for executive readability and technical density.

| Level | Size (px / rem) | Line Height | Weight | Letter Spacing | Utility Class Name & Example Use |
|---|---|---|---|---|---|
| **Display** | `36px` (`2.25rem`) | `40px` (`2.5rem`) | Bold (`700`) | `-0.025em` | `.text-display` — Executive Hero readiness percentages ("98%"). |
| **Headline** | `24px` (`1.5rem`) | `32px` (`2.0rem`) | Bold (`700`) | `-0.015em` | `.text-headline` — Page titles ("Today's Operational Readiness"). |
| **Title** | `18px` (`1.125rem`) | `28px` (`1.75rem`) | SemiBold (`600`) | `0.0em` | `.text-title` — Card headers, modal titles, and section headers. |
| **Body** | `14px` (`0.875rem`) | `20px` (`1.25rem`) | Regular (`400`) | `0.0em` | `.text-body` — Standard body narrative text and descriptions. |
| **Caption** | `12px` (`0.75rem`) | `16px` (`1.0rem`) | Medium (`500`) | `+0.02em` | `.text-caption` — Table cell subtext, timestamps, and metadata. |
| **Overline** | `10px` (`0.625rem`) | `12px` (`0.75rem`) | SemiBold (`600`) | `+0.08em` | `.text-overline` — Uppercase field labels and category badges. |

---

## 5. Color Palette & Semantic Status Mapping

### 5.1 Palette Overview
- **Primary Brand (Emerald Green)**: Symbolizes operational safety, system health, and clinical readiness (`#00C853`).
- **Secondary Accent (Titanium Blue)**: Symbolizes technical precision, analytics, and infrastructure controls (`#2979FF`).
- **Neutrals**:
  - **Light Theme**: Canvas `#F1F5F9`, Card `#FFFFFF`, Border `#E2E8F0`, Text `#0F172A`.
  - **Dark Theme**: Canvas `#121212`, Card `#1E1E1E`, Border `#2D2D2D`, Text `#F8FAFC`.

### 5.2 Status Token Classes (Dual Theme Compliance)

All status indicators must use dual-theme compliant utility tokens:

| Status Key | Business Meaning | Light Mode Utility Classes | Dark Mode Utility Classes |
|---|---|---|---|
| `safe_to_open` | All controls verified; clinic safe to operate. | `bg-emerald-50 text-emerald-700 border-emerald-200` | `dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-800` |
| `action_needed` | Operational issue requires intervention; clinic open. | `bg-amber-50 text-amber-700 border-amber-200` | `dark:bg-amber-950/40 dark:text-amber-400 dark:border-amber-800` |
| `critical_risk` | Severe blocker; immediate executive action required. | `bg-red-50 text-red-700 border-red-200` | `dark:bg-red-950/40 dark:text-red-400 dark:border-red-800` |
| `unknown` | Telemetry pending or connector sync offline. | `bg-slate-50 text-slate-700 border-slate-200` | `dark:bg-slate-900 dark:text-slate-400 dark:border-slate-800` |

---

## 6. Component Badge Tokens & Variants (R3)

Badges and status indicators must support three standardized variants:

### 6.1 `compact` Variant
- **Target Use**: Compact header status pills, table inline rows, and mobile summary headers.
- **Specification**: Height `24px` (`h-6`), padding `px-2 py-0.5`, font size `11px`, border `1px solid`, rounded `full`. Include a `6px` colored status dot (`animate-pulse` if critical).

### 6.2 `expanded` Variant
- **Target Use**: Executive card headers (`StatusCard`, `NorthStarHero`), action items.
- **Specification**: Height `32px` (`h-8`), padding `px-3 py-1`, font size `13px` SemiBold, border `1px solid`, rounded `lg`. Includes icon, status label, and optional action chevron.

### 6.3 `technical` Variant
- **Target Use**: Operations views (`EvidenceNetwork`, `ComplianceDrift`, `RemediationLedger`).
- **Specification**: Height `36px` (`h-9`), padding `px-3.5 py-1.5`, font size `12px` Monospace/Sans, rounded `md`. Displays status label, verification timestamp ("12m ago"), and inspector hash link.

---

## 7. Elevation, Shadows, & Border Radiuses

### 7.1 Border Radius Tokens
- `rounded-sm`: `4px` — Table inline code blocks, micro badges.
- `rounded-md`: `6px` — Form inputs, select dropdowns, technical table cards.
- `rounded-lg`: `8px` — Standard executive dashboard cards and action buttons.
- `rounded-xl`: `12px` — Hero banners, AI Assistant panel, modal containers.
- `rounded-2xl`: `16px` — Top-level landing hero wrappers.
- `rounded-full`: `9999px` — Status pills, avatar circles, toggle switches.

### 7.2 Elevation & Shadow Layers
- **Card Shadow (`shadow-card`)**: `0 1px 3px 0 rgba(0,0,0,0.1)` — Standard resting elevation for dashboard cards.
- **Soft Hover Shadow (`shadow-soft`)**: `0 2px 15px -3px rgba(0,0,0,0.07)` — Hover elevation for interactive action cards.
- **Floating Shadow (`shadow-medium`)**: `0 4px 25px -5px rgba(0,0,0,0.1)` — Slide-over drawers, dropdown menus, and popovers.
- **Modal Overlay (`z-50`)**: Dark backdrop backdrop-blur overlay for system dialogs.

---

## 8. 12-Column Grid System & Breakpoints

The responsive layout uses standard 12-column CSS grid containers with defined breakpoint thresholds:

| Breakpoint Prefix | Min Width | Column Count | Gutter Width | Typical Device |
|---|---|---|---|---|
| `sm` | `640px` | 4 columns | `16px` | Large smartphones / mini tablets |
| `md` | `768px` | 8 columns | `20px` | Tablets / iPad portrait |
| `lg` | `1024px` | 12 columns | `24px` | Laptops / iPad landscape |
| `xl` | `1280px` | 12 columns | `24px` | Standard Desktop Monitors |
| `2xl` | `1536px` | 12 columns | `32px` | Large Desktop / Ultra-Wide Displays |

---

## 9. Iconography & Animation Guidelines

### 9.1 Iconography (Lucide React)
- **Library**: `lucide-react`
- **Icon Sizing**:
  - Micro / Inline: `14px` (`w-3.5 h-3.5`)
  - Standard Button / Badge: `16px` (`w-4 h-4`)
  - Section Header: `20px` (`w-5 h-5`)
  - Hero Card Icon: `24px` (`w-6 h-6`)
- **Stroke Width**: Standard `2px` stroke width for technical icons; `1.75px` for hero banners.

### 9.2 Animation & Transition Tokens
- **Transition Duration**: `duration-150` (micro interactions), `duration-200` (card expanders/drawers), `duration-300` (workspace zoom toggles).
- **Easing**: `ease-in-out` for all disclosure transitions.
- **Pulse Indicators**: `animate-pulse` applied to critical risk status dots and live connector sync badges.
- **Loading Spinners**: `animate-spin` on `Loader2` icons during active data revalidation.
