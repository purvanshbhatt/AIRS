---
name: Ethereal Resilience
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
  secondary: '#7bd0ff'
  on-secondary: '#00354a'
  secondary-container: '#00a6e0'
  on-secondary-container: '#00374d'
  tertiary: '#ffb3af'
  on-tertiary: '#650911'
  tertiary-container: '#fc7c78'
  on-tertiary-container: '#711419'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#6ffbbe'
  primary-fixed-dim: '#4edea3'
  on-primary-fixed: '#002113'
  on-primary-fixed-variant: '#005236'
  secondary-fixed: '#c4e7ff'
  secondary-fixed-dim: '#7bd0ff'
  on-secondary-fixed: '#001e2c'
  on-secondary-fixed-variant: '#004c69'
  tertiary-fixed: '#ffdad7'
  tertiary-fixed-dim: '#ffb3af'
  on-tertiary-fixed: '#410005'
  on-tertiary-fixed-variant: '#842225'
  background: '#0b1326'
  on-background: '#dae2fd'
  surface-variant: '#2d3449'
  deep-navy: '#020617'
  slate-surface: '#1e293b'
  readiness-high: '#10b981'
  readiness-med: '#f59e0b'
  readiness-low: '#ef4444'
  glass-stroke: rgba(255, 255, 255, 0.1)
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
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
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  mono-code:
    fontFamily: ui-monospace
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  container-max: 1280px
  gutter: 24px
  section-padding: 120px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style

This design system embodies a "Precision Healthcare for Fintech" aesthetic, merging the empathetic, data-rich clarity of Apple Health with the rigorous, high-end professional utility of Mercury. The brand personality is authoritative yet approachable—an executive partner in a complex regulatory landscape.

The visual style is **Corporate / Modern** with strong **Glassmorphism** influences. It prioritizes "breathability" through expansive whitespace (or "dark space") and utilizes translucent layers to signify the clarity that the product brings to opaque compliance data. The goal is to evoke a sense of calm reliability and unshakeable security.

## Colors

The palette is anchored in a sophisticated Dark Mode. The primary background is not black, but a rich `deep-navy` (#020617) to provide a more premium, "infinite" depth. 

- **Primary Emerald (#10b981):** Represents health, "go" status, and growth. It is used for primary actions and "Ready" indicators.
- **Secondary Sky (#38bdf8):** Used for informational accents and secondary data visualizations, providing a technical contrast to the organic green.
- **Readiness Tiers:** A strict semantic hierarchy is enforced: Emerald for high readiness, Amber for caution/moderate, and Crimson for critical gaps.
- **Glassmorphism:** Surfaces utilize `slate-surface` with varying opacities and a 1px `glass-stroke` to create the "Apple Health" layered effect.

## Typography

The design system relies exclusively on **Inter** to maintain a clean, systematic feel. Hierarchies are established through significant weight variance and tight letter-spacing on larger headings to create a bespoke, "executive" editorial look.

- **Display Text:** Used for hero sections, using a heavy weight and negative letter-spacing.
- **Body Text:** Optimized for readability with a generous 1.5x line height.
- **Labels:** Small caps are used for category headers and status indicators to differentiate them from actionable body text.
- **Monospace:** Reserved strictly for API telemetry, hashes, and technical data logs.

## Layout & Spacing

This design system uses a **Fixed Grid** model for desktop to maintain a controlled, high-end editorial feel. 

- **Breathing Room:** Section vertical padding is set to a generous 120px to prevent visual clutter and signal premium positioning.
- **Grid:** A 12-column grid with 24px gutters. Elements typically span 6 columns for balanced "Split" views (Content vs. Data Visualization).
- **Mobile Reflow:** Margins shrink to 16px. Section padding reduces to 64px. Stacked elements transition from horizontal to vertical with `stack-lg` spacing between logical groups.

## Elevation & Depth

Depth is communicated through **Glassmorphism** and **Tonal Layering** rather than traditional drop shadows.

- **The Z-Axis:**
    - **Level 0 (Base):** Deep Navy background.
    - **Level 1 (Cards):** Translucent Slate (#1e293b at 60% opacity) with a `backdrop-filter: blur(12px)`.
    - **Level 2 (Modals/Popovers):** Higher opacity Slate (80%) with a subtle 1px white border at 10% opacity to define the edge.
- **Gradients:** Subtle, large-radius background blurs (radial gradients) in Primary Emerald and Secondary Sky sit *behind* the glass layers to provide a soft, bioluminescent glow, mimicking modern fintech dashboards.

## Shapes

The shape language is consistently **Rounded** (0.5rem base), creating a soft, approachable feel that balances the technical nature of AI and compliance. 

- **Standard Elements:** Buttons, inputs, and small cards use the 0.5rem (8px) radius.
- **Container Elements:** Large dashboard cards or feature containers use `rounded-xl` (1.5rem / 24px) to create a "containerized" look reminiscent of iOS widgets.
- **Readiness Gauges:** Circular or semi-circular strokes are used for scores to feel more organic and "human."

## Components

### Buttons
- **Primary:** Solid Emerald fill with white text. High contrast, slightly wider horizontal padding for an "Executive" feel.
- **Secondary (Glass):** Translucent background with a 1px border. Used for "Sandbox" or "Demo" actions.

### Readiness Status Indicators
- **Score Gauges:** A thick, rounded-cap stroke (Emerald/Amber/Red) surrounding a central percentage.
- **Status Chips:** Small, pill-shaped indicators with low-opacity background tints and high-contrast text for immediate glanceability.

### Input Fields
- Dark backgrounds (slightly lighter than the base navy) with 1px borders that glow Emerald on focus. Placeholder text uses a muted slate to reduce visual noise.

### Cards
- Utilizes the glassmorphism effect. Content inside cards should have increased internal padding (32px) to support the "breathable" narrative. Header text within cards should be `label-caps`.

### Lists
- Borderless. Items are separated by subtle 1px horizontal lines (`glass-stroke`). Hover states use a slight increase in background opacity.