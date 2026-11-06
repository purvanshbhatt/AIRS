# ResilAI Official Brand Asset Suite & Implementation Guide

> [!NOTE]
> All brand assets preserve the authentic **6-fold hexagonal node network / cyber snowflake** emblem and typography from the company's design standards. Every variant is rendered in ultra-high resolution (up to 3120px, 300 DPI ready) with edge-preserving anti-aliased transparency, eliminating low-resolution pixelation and legacy black-and-white limitations.

---

## 1. Brand Color Standards

| Element | Color Name | Hex Code | RGB | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Navy** | Corporate Navy | `#182939` | `rgb(24, 41, 57)` | Light mode text, outer brackets, center hexagon |
| **Accent Green** | Vibrant Emerald | `#6ED975` | `rgb(110, 217, 117)` | Network nodes, radial circuit spokes, dumbbell links |
| **Dark Mode Text** | Crisp White | `#FFFFFF` | `rgb(255, 255, 255)` | Dark mode text and outer brackets |
| **Dark Canvas** | Cyber Navy | `#0B1326` | `rgb(11, 19, 38)` | Solid dark background canvas |
| **Light Canvas** | Pure White | `#FFFFFF` | `rgb(255, 255, 255)` | Solid light background canvas |

---

## 2. Brand Asset Matrix & Locations

All assets are organized and available in two primary locations in the repository:
1. `frontend/public/brand/` (Web-accessible, public CDN path: `/brand/...`)
2. `docs/assets/brand/` (Offline documentation, report generators, and design handoff)

### A. Horizontal Lockups (`brand/horizontal/`)
*Emblem on left + "ResilAI" wordmark on right (3120 × 1122 px, 300 DPI)*
Best for: **Navbar headers, footers, website banners, letterheads, email signatures, GitHub README.**

| Variant | Filename | Background | Color Scheme |
| :--- | :--- | :--- | :--- |
| **Light Transparent** | `resilai_horizontal_light_trans.png` | Transparent (Alpha) | Navy (`#182939`) + Emerald (`#6ED975`) |
| **Dark Transparent** | `resilai_horizontal_dark_trans.png` | Transparent (Alpha) | White (`#FFFFFF`) + Emerald (`#6ED975`) |
| **Solid White** | `resilai_horizontal_light_solid.png` | Pure White (`#FFFFFF`) | Navy (`#182939`) + Emerald (`#6ED975`) |
| **Solid Cyber Dark** | `resilai_horizontal_dark_solid.png` | Cyber Navy (`#0B1326`) | White (`#FFFFFF`) + Emerald (`#6ED975`) |
| **White Monochrome** | `resilai_horizontal_white_mono.png` | Transparent (Alpha) | Pure White (`#FFFFFF`) |
| **Black Monochrome** | `resilai_horizontal_black_mono.png` | Transparent (Alpha) | Dark Navy (`#182939`) |
| **Adaptive SVG** | `resilai_horizontal_adaptive.svg` | Transparent (Auto) | Auto-switches via `(prefers-color-scheme)` |
| **Light SVG** | `resilai_horizontal_light.svg` | Transparent | Light mode vector |
| **Dark SVG** | `resilai_horizontal_dark.svg` | Transparent | Dark mode vector |

---

### B. Stacked / Vertical Lockups (`brand/stacked/`)
*Emblem centered on top + "RESILAI" wordmark below (1695 × 2445 px, 300 DPI)*
Best for: **Report title pages, book covers, full-page pitch decks, splash screens, login dialogs, posters.**

| Variant | Filename | Background | Color Scheme |
| :--- | :--- | :--- | :--- |
| **Light Transparent** | `resilai_stacked_light_trans.png` | Transparent (Alpha) | Navy (`#182939`) + Emerald (`#6ED975`) |
| **Dark Transparent** | `resilai_stacked_dark_trans.png` | Transparent (Alpha) | White (`#FFFFFF`) + Emerald (`#6ED975`) |
| **Solid White** | `resilai_stacked_light_solid.png` | Pure White (`#FFFFFF`) | Navy (`#182939`) + Emerald (`#6ED975`) |
| **Solid Cyber Dark** | `resilai_stacked_dark_solid.png` | Cyber Navy (`#0B1326`) | White (`#FFFFFF`) + Emerald (`#6ED975`) |
| **White Monochrome** | `resilai_stacked_white_mono.png` | Transparent (Alpha) | Pure White (`#FFFFFF`) |
| **Black Monochrome** | `resilai_stacked_black_mono.png` | Transparent (Alpha) | Dark Navy (`#182939`) |
| **Adaptive SVG** | `resilai_stacked_adaptive.svg` | Transparent (Auto) | Auto-switches via `(prefers-color-scheme)` |
| **Light SVG** | `resilai_stacked_light.svg` | Transparent | Light mode vector |
| **Dark SVG** | `resilai_stacked_dark.svg` | Transparent | Dark mode vector |

---

### C. Standalone Emblem (`brand/emblem/`)
*The 6-fold radial hexagonal network mark without wordmark (1632 × 2080 px, 300 DPI)*
Best for: **App icons, favicons, watermarks, social media avatars, Discord/Slack bots, badge stamps.**

| Variant | Filename | Background | Color Scheme |
| :--- | :--- | :--- | :--- |
| **Light Transparent** | `resilai_emblem_light_trans.png` | Transparent (Alpha) | Navy (`#182939`) + Emerald (`#6ED975`) |
| **Dark Transparent** | `resilai_emblem_dark_trans.png` | Transparent (Alpha) | White (`#FFFFFF`) + Emerald (`#6ED975`) |
| **Solid White** | `resilai_emblem_light_solid.png` | Pure White (`#FFFFFF`) | Navy (`#182939`) + Emerald (`#6ED975`) |
| **Solid Cyber Dark** | `resilai_emblem_dark_solid.png` | Cyber Navy (`#0B1326`) | White (`#FFFFFF`) + Emerald (`#6ED975`) |
| **White Monochrome** | `resilai_emblem_white_mono.png` | Transparent (Alpha) | Pure White (`#FFFFFF`) |
| **Black Monochrome** | `resilai_emblem_black_mono.png` | Transparent (Alpha) | Dark Navy (`#182939`) |
| **Adaptive SVG** | `resilai_emblem_adaptive.svg` | Transparent (Auto) | Auto-switches via `(prefers-color-scheme)` |
| **Light SVG** | `resilai_emblem_light.svg` | Transparent | Light mode vector |
| **Dark SVG** | `resilai_emblem_dark.svg` | Transparent | Dark mode vector |

---

### D. Favicons & App Icons Suite (`brand/favicons/` & `frontend/public/`)

| File | Specs / Format | Role |
| :--- | :--- | :--- |
| `favicon.ico` | Multi-resolution ICO (16x16, 32x32, 48x48) | Classic browser tab icon (IE/Edge/Chrome fallback) |
| `favicon.svg` | Responsive SVG with CSS `@media` switching | Modern browser SVG favicon (auto dark/light mode) |
| `favicon-16.png` | 16 × 16 PNG (transparent) | High-DPI browser tab 1x |
| `favicon-32.png` | 32 × 32 PNG (transparent) | High-DPI browser tab 2x retina |
| `favicon-48.png` | 48 × 48 PNG (transparent) | Desktop taskbar shortcut icon |
| `favicon-192.png` | 192 × 192 PNG (transparent) | Android Home Screen / Progressive Web App (PWA) |
| `favicon-512.png` | 512 × 512 PNG (transparent) | PWA splash icon, Google search result avatar |
| `apple-touch-icon.png` | 180 × 180 PNG (transparent) | iOS Safari bookmark & Home Screen icon |
| `favicon-light.png` | 512 × 512 PNG | Light mode dedicated icon |
| `favicon-dark.png` | 512 × 512 PNG | Dark mode dedicated icon |

---

## 3. How to Use in Different Files

### In HTML / Websites
```html
<!-- Adaptive SVG (matches OS/Browser theme automatically) -->
<img src="/brand/horizontal/resilai_horizontal_adaptive.svg" alt="ResilAI" width="220" />

<!-- Or using Tailwind CSS dark: variants -->
<img src="/brand/horizontal/resilai_horizontal_light_trans.png" alt="ResilAI" className="h-9 w-auto block dark:hidden" />
<img src="/brand/horizontal/resilai_horizontal_dark_trans.png" alt="ResilAI" className="h-9 w-auto hidden dark:block" />
```

### In GitHub README.md
```markdown
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/assets/logo_header_dark.png">
    <source media="(prefers-color-scheme: light)" srcset=".github/assets/logo_header_light.png">
    <img src=".github/assets/logo_header_dark.png" alt="ResilAI Logo" width="380" />
  </picture>
</p>
```

### In PDF Reports & Print Documents (ReportLab / Python / Word)
```python
# For white-paper PDF reports (ReportLab)
from reportlab.platypus import Image
logo = Image("frontend/public/brand/horizontal/resilai_horizontal_light_trans.png", width=2.5 * inch, height=0.9 * inch)
```

### In Google Slides / PowerPoint / Keynote
- For **Dark Pitch Decks**: Insert `brand/horizontal/resilai_horizontal_dark_trans.png` or `brand/stacked/resilai_stacked_dark_trans.png`.
- For **White Presentations**: Insert `brand/horizontal/resilai_horizontal_light_trans.png` or `brand/stacked/resilai_stacked_light_trans.png`.
- For **Printed Handouts**: Insert `brand/horizontal/resilai_horizontal_black_mono.png`.
