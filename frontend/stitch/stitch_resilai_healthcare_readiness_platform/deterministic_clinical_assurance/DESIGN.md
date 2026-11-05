---
name: Deterministic Clinical Assurance
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394e'
  surface-container-lowest: '#060d20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3e'
  surface-container-highest: '#2d3449'
  on-surface: '#dbe2fd'
  on-surface-variant: '#bbcabf'
  inverse-surface: '#dbe2fd'
  inverse-on-surface: '#283044'
  outline: '#86948a'
  outline-variant: '#3c4a42'
  surface-tint: '#4edea3'
  primary: '#4edea3'
  on-primary: '#003824'
  primary-container: '#10b981'
  on-primary-container: '#00422b'
  inverse-primary: '#006c49'
  secondary: '#adc6ff'
  on-secondary: '#002e6a'
  secondary-container: '#0566d9'
  on-secondary-container: '#e6ecff'
  tertiary: '#ffb95f'
  on-tertiary: '#472a00'
  tertiary-container: '#e29100'
  on-tertiary-container: '#523200'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#6ffbbe'
  primary-fixed-dim: '#4edea3'
  on-primary-fixed: '#002113'
  on-primary-fixed-variant: '#005236'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc6ff'
  on-secondary-fixed: '#001a42'
  on-secondary-fixed-variant: '#004395'
  tertiary-fixed: '#ffddb8'
  tertiary-fixed-dim: '#ffb95f'
  on-tertiary-fixed: '#2a1700'
  on-tertiary-fixed-variant: '#653e00'
  background: '#0b1326'
  on-background: '#dbe2fd'
  surface-variant: '#2d3449'
  surface-dark: '#0b1326'
  surface-light: '#ffffff'
  status-ready: '#10b981'
  status-drift: '#f59e0b'
  status-critical: '#ef4444'
  slate-soft: '#f8fafc'
  slate-text: '#475569'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
  title-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.4'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.0'
    letterSpacing: 0.05em
  narrative-summary:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: -0.01em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  margin-mobile: 1rem
  margin-desktop: 2.5rem
  gutter: 1.5rem
  sidebar-width: 260px
  max-content-width: 1200px
---

## Brand & Style

The design system is engineered to evoke **authoritative calm**. It targets healthcare executives who require binary certainty ("Ready" or "Not Ready") in a high-stakes, high-anxiety environment. The visual language bridges the gap between the technical precision of a cybersecurity platform and the clean, approachable warmth of a premium health application.

The aesthetic is a hybrid of **Minimalism** and **Corporate Modern**, drawing inspiration from:
- **Apple Health:** For data storytelling and "glanceable" health summaries.
- **Stripe & Linear:** For pixel-perfect spacing, rigorous grid alignment, and "technical luxury" through typography.
- **Mercury:** For the sense of institutional trust and security.

The interface must avoid generic SaaS tropes, instead opting for a "Clinical Premium" feel—crisp, high-contrast, and intentionally spacious.

## Colors

The palette is bifurcated to support two distinct psychological modes. 

**Dark Mode (Default):** Uses a deep navy (`#0b1326`) as the foundation to create a "Command Center" feel. Primary emerald (`#10b981`) signifies health and verification. This mode is the standard for IT Workspace and deep-work sessions.

**Light Mode:** Transitions to "Clinical White." It uses high-contrast typography against soft slate backgrounds (`#f8fafc`) to mimic the cleanliness of a modern medical facility.

**Semantic Logic:**
- **Green (Ready):** Deterministic health.
- **Orange (Drift):** Actionable warnings before failure.
- **Red (Critical):** Immediate executive intervention required.

## Typography

This design system utilizes **Inter** for all primary interface elements to ensure maximum legibility and a neutral, professional tone. **JetBrains Mono** is introduced sparingly for technical labels, timestamps, and evidence hashes to signify the deterministic, "under-the-hood" data verification.

**Hierarchy Rules:**
- **Executive Summaries:** Use `narrative-summary` for "Morning Brief" content—slightly larger than standard body text with generous line height to reduce cognitive load.
- **Data Tables:** Use `label-sm` for technical metadata to differentiate it from executive-level insights.
- **Headlines:** Tight letter-spacing on larger sizes to create a "premium editorial" feel similar to Linear.

## Layout & Spacing

The layout employs a **fixed grid system** for executive views to ensure a curated, "dashboard-as-a-document" experience, while the IT Workspace uses a **fluid grid** to maximize data density.

- **Desktop:** 12-column grid with a fixed 260px sidebar. Central content area is capped at 1200px to maintain readability for narrative summaries.
- **Mobile:** Single column with 16px side margins. Cards are full-width to maximize the "Apple Health" summary feel.
- **IT Workspace:** Uses a "pane-based" layout. Sections can be collapsed or expanded, prioritizing utility over the executive narrative.
- **Rhythm:** An 8px linear scale is used for all internal component spacing (8, 16, 24, 32, 48, 64).

## Elevation & Depth

This design system rejects traditional heavy shadows in favor of **Tonal Layering** and **Subtle Outlines**.

- **Dark Mode:** Surfaces use a tint-stacking method. The base is `#0b1326`, secondary containers are `#161f32`, and active elements are `#1e293b`. Border strokes are low-opacity white (10%) to define edges without adding visual noise.
- **Light Mode:** Uses "Paper on Slate." White cards sit on top of `#f8fafc` backgrounds. Shadows are extremely soft (15% opacity, 20px blur) to create a gentle lifted effect.
- **Glassmorphism:** Reserved exclusively for the **Top App Bar** and **Side Navigation** backgrounds (15px blur) to maintain context of the underlying data as the user scrolls.

## Shapes

The shape language is **Refined & Consistent**. A standard 8px (`rounded-md`) radius is used for primary UI containers and input fields. 

- **Status Cards:** Use `rounded-lg` (16px) to feel more "consumer-premium" and approachable.
- **Action Buttons:** Use a standard `rounded-md` (8px). Avoid pill-shaped buttons except for "Ask ResilAI" floating action triggers.
- **Tables:** Containments should be sharp on the outer edges if full-bleed, but inner cell-selection states use 4px rounding.

## Components

### Side Navigation
A fixed-width sidebar containing 8 distinct tabs: **Today, Needs Attention, Recovery, Documents, Governance, Connectors, IT Workspace, Settings**.
- **Visuals:** Icons are 20px stroke-based. Active state uses a "ghost" background with a primary emerald left-accent bar.

### Top App Bar
Minimalist and translucent. 
- **Search:** A centered, "Command-K" style search bar.
- **Profile:** Executive name and clinic ID on the far right.

### Status Cards (Apple Health Style)
The primary vehicle for the "Morning Brief."
- **Structure:** Large semantic icon (Top Left), Big Numeric/Status Value (Top Right), Narrative Sentence (Bottom).
- **Behavior:** On hover, cards subtly scale (1.02x) and increase shadow/glow.

### Narrative Summary (Linear Style)
Used at the top of the "Today" page.
- **Styling:** Left-aligned text, high-contrast, using the `narrative-summary` typography. This block explains *why* the status is green or orange in plain English.

### Audit Evidence Tables
Found in the IT Workspace.
- **Styling:** Tight vertical padding, monospaced fonts for technical data, and "Badge" components for status.
- **Function:** Rows must include a "Copy Evidence Link" button that appears on hover.

### Buttons & Inputs
- **Primary Button:** Solid emerald in Dark Mode; Solid navy in Light Mode.
- **Secondary:** Ghost style with 1px border.
- **Inputs:** High-contrast borders; focus state uses a 2px emerald ring.