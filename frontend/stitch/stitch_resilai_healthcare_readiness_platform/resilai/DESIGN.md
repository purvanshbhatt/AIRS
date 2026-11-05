---
name: ResilAI
colors:
  surface: '#0b1326'
  surface-dim: '#0b1326'
  surface-bright: '#31394d'
  surface-container-lowest: '#060e20'
  surface-container-low: '#131b2e'
  surface-container: '#171f33'
  surface-container-high: '#222a3d'
  surface-container-highest: '#2d3449'
  on-surface: '#dae2fd'
  on-surface-variant: '#bbcabf'
  inverse-surface: '#dae2fd'
  inverse-on-surface: '#283044'
  outline: '#86948a'
  outline-variant: '#3c4a42'
  surface-tint: '#4edea3'
  primary: '#4edea3'
  on-primary: '#003824'
  primary-container: '#10b981'
  on-primary-container: '#00422b'
  inverse-primary: '#006c49'
  secondary: '#ffb95f'
  on-secondary: '#472a00'
  secondary-container: '#ee9800'
  on-secondary-container: '#5b3800'
  tertiary: '#c0c1ff'
  on-tertiary: '#1000a9'
  tertiary-container: '#9699ff'
  on-tertiary-container: '#1d17b2'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#6ffbbe'
  primary-fixed-dim: '#4edea3'
  on-primary-fixed: '#002113'
  on-primary-fixed-variant: '#005236'
  secondary-fixed: '#ffddb8'
  secondary-fixed-dim: '#ffb95f'
  on-secondary-fixed: '#2a1700'
  on-secondary-fixed-variant: '#653e00'
  tertiary-fixed: '#e1e0ff'
  tertiary-fixed-dim: '#c0c1ff'
  on-tertiary-fixed: '#07006c'
  on-tertiary-fixed-variant: '#2f2ebe'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
  ready-emerald: '#10B981'
  drift-amber: '#F59E0B'
  critical-red: '#EF4444'
  slate-900: '#0F172A'
  slate-800: '#1E293B'
  slate-50: '#F8FAFC'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  title-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  mono-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  page-margin: 2rem
  section-gap: 3rem
  gutter: 1.5rem
  stack-sm: 0.5rem
  stack-md: 1rem
  container-max: 1200px
---

## Brand & Style

The design system embodies **Executive Clarity**—a fusion of high-end financial trust (Mercury), modern engineering precision (Linear), and human-centric healthcare narrative (Apple Health). It moves away from the anxiety-inducing "cybersecurity" aesthetic of red-and-black dashboards toward a calm, authoritative, and clinical environment.

The visual language is defined as **Corporate / Modern** with a **Minimalist** focus. It prioritizes information density for technical users while maintaining a high-contrast, "Apple Health" style narrative summary for medical directors. The interface should feel expensive and robust, instilling confidence that the clinic’s digital infrastructure is being continuously verified.

Key attributes:
- **Calm Authority:** Softened surfaces and refined typography reduce the stress of compliance monitoring.
- **Storytelling Data:** Complex telemetry is translated into simple, definitive "Yes/No" readiness states.
- **Surgical Precision:** Every pixel and margin is intentional, reflecting the discipline of a medical environment.

## Colors

The system uses a **Dark Mode First** approach to signify modern, premium software. The primary brand palette is built on **Deep Navy/Slate (#0F172A)**, providing a sophisticated backdrop for semantic status colors.

- **Primary (Ready):** Vibrant Emerald Green (#10B981). This is the color of "safety." It should be used for successful verifications, readiness scores, and affirmative actions.
- **Secondary (Drift/Action):** Warm Amber (#F59E0B). Used for warnings and "Compliance Drift"—items that aren't critical failures but require attention to maintain readiness.
- **Named Colors:** 
    - `critical-red` (#EF4444) is reserved exclusively for blocking failures (e.g., "Backup Failed").
    - `slate-800` is used for surface containers to create a layered, "Linear-style" depth.

## Typography

**Inter** is the sole typeface, utilized for its neutrality and high legibility in data-dense environments.

- **Authoritative Headers:** Headlines use semi-bold and bold weights with tighter letter spacing to convey certainty. 
- **Narrative Body:** Body text uses generous line heights to ensure readability for busy executives.
- **Contextual Labels:** Smaller labels use a medium weight and slightly increased letter spacing for clarity in navigation and status badges.
- **Scale:** For the "Morning Brief" view, use `display-lg` for the primary readiness score to ensure it is the first thing a user sees.

## Layout & Spacing

The layout follows a **Fixed Grid** model for desktop to maintain executive-level polish, while transitioning to a highly fluid, stacked model for the mobile "Morning Brief."

- **Executive View:** Utilizes large whitespace and centered containers to focus attention on the core "Ready" status.
- **IT Operations Center:** Switches to a 12-column grid to maximize data visibility and sidebar navigation.
- **Rhythm:** A strictly 8px-based spacing system ensures visual harmony. Use `section-gap` between major narrative blocks and `stack-md` for internal card padding.
- **Breakpoints:**
    - Mobile (< 640px): Single column, full-bleed cards with 16px margins.
    - Tablet (640px - 1024px): 2-column layout for "Needs Attention" triage.
    - Desktop (> 1024px): Multi-pane interface with persistent navigation.

## Elevation & Depth

To achieve a "Mercury" and "Linear" feel, depth is conveyed through **Tonal Layers** and **Low-Contrast Outlines** rather than heavy shadows.

- **Base Layer:** The deepest slate background (`#0F172A`).
- **Surface Layer:** Cards and containers use a slightly lighter slate (`#1E293B`) with a subtle 1px border (`#334155`) to define boundaries.
- **Interaction Depth:** On hover, cards should subtly lift using a very soft, ambient shadow (10% opacity black) and a slightly brighter border.
- **Executive Elements:** Use subtle background blurs (12px) for navigation bars and overlays to maintain a sense of lightness and modern sophistication.

## Shapes

The design uses a **Rounded (Level 2)** shape language. This provides a approachable, "healthcare-safe" feel that is more friendly than sharp corners but more professional than pill-shaped bubbles.

- **Standard Elements:** Buttons, input fields, and small cards use 0.5rem (8px).
- **Large Containers:** Main dashboard cards and "Ready" status indicators use 1rem (16px) to emphasize their importance.
- **Chips/Badges:** Use a full pill shape (999px) to distinguish status indicators (e.g., "Verified") from interactive buttons.

## Components

- **Readiness Hero:** A massive, high-contrast indicator for the "Today" page. It uses a thick circular progress ring in `ready-emerald` or `drift-amber` with a large central label.
- **Status Cards:** Narrative-driven cards. Instead of "MFA: Success," the card should read "Your identity provider is secure. MFA is active for all 24 staff members."
- **Buttons:** 
    - *Primary:* Solid `ready-emerald` with white text for positive readiness actions.
    - *Secondary:* Ghost style with `slate-50` borders for navigation.
- **Triage Lists:** High-density lists in the IT Operations Center using `mono-sm` for technical logs, with clear vertical rhythm.
- **Inputs:** Clean, dark-field inputs with `slate-800` backgrounds and focus rings in `primary-color`.
- **Narrative Data Vis:** Avoid complex line charts for executives. Use simple bar charts or "Apple Health" style rings that show "Compliance Trend" over 7 days.
- **The "Ask ResilAI" Bar:** A persistent, premium search-style bar at the bottom of the screen with a subtle gradient glow, signaling its AI-powered capabilities.