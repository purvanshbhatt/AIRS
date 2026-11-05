# ResilAI Design System Audit

**Status:** Awaiting implementation of unified design system.

## 1. Top 10 Technical/UI Inconsistencies

1. **Inconsistent Radius/Border:** The application mixes sharp corners (`rounded-none`), medium curves (`rounded-md`), and extreme pills (`rounded-full`) on similar container types.
2. **Color Palette Bleed:** Use of generic Tailwind colors (e.g., standard `blue-500` or `red-500`) instead of semantic ResilAI tokens (`ready-emerald`, `drift-amber`).
3. **Typography Disconnect:** The UI mixes Inter, Roboto, and system sans-serif fonts without a clear typographic scale. 
4. **Card Elevation:** Some cards use flat borders (`border-surface-bright`), while others use heavy drop shadows, breaking the "depth" model.
5. **Button Consistency:** CTAs range from large block buttons to tiny inline text links.
6. **Form Inputs:** Disparate padding and focus ring colors across different forms.
7. **Animation Sprawl:** Excessive and inconsistent animations. Some pages use heavy `framer-motion` springs, while others snap instantaneously.
8. **Responsive Breakpoints:** The grid collapses at different pixel widths depending on the page (`md` vs `lg` used arbitrarily).
9. **Empty States:** Ranging from a blank white page to an overly complex "No Data" illustration.
10. **State Management:** Loading states are sometimes full-page spinners, sometimes skeletal loaders, and sometimes missing entirely.

## 2. Design System Directives (For Refactor)

Based on the `design-taste-frontend` skill, the following directives will govern the frontend redesign:

- **Dials:** `DESIGN_VARIANCE: 7`, `MOTION_INTENSITY: 6`, `VISUAL_DENSITY: 4` (Premium B2B / SaaS Landing).
- **Typography:** Sans-serif primary (e.g., Geist or Inter strictly controlled). No serif fonts as default.
- **Color:** Neutral dark base (`slate-900`) with high-contrast semantic accents (`ready-emerald`, `drift-amber`, `critical-rose`). No "AI Purple/Lila" default glow.
- **Materiality:** 1px borders, subtle inset shadows for depth, controlled corner radius (e.g., standard `rounded-xl` for cards, `rounded-md` for internal items).
- **Interactive UI:** Skeletal loaders, tactile feedback (`scale-[0.98]` on active), clear empty/error states.
- **Buttons:** Single primary intent per page. Strict WCAG AA contrast on all CTAs.

## 3. Implementation Sequence

The frontend refactor will proceed in the following order:

1. **Design System Standardization:** Centralize tokens in `tailwind.config.js` and CSS variables. Build primitive components (Buttons, Cards, Inputs).
2. **Product Narrative & Onboarding:** Fix the core storytelling and initial user experience.
3. **L1 Morning Brief (Business Workspace):** Implement the `TodayPage` with progressive disclosure.
4. **L2 Needs Attention:** Build the action-oriented workflow for executives.
5. **L3 IT Workspace (Operations Workspace):** Build the deep technical drill-downs for IT Ops.
6. **Documentation Architecture:** Separate product docs from customer evidence.
7. **Connectors & Evidence:** Refine the technical graph and connector health UI.
8. **Regional Profiles & Billing:** Finalize administrative views.
