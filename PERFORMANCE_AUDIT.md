# Frontend Performance Audit Report — ResilAI (AIRS)

**Version**: 1.3.0  
**Build Tooling**: Vite 6.4.3 & TypeScript 5.5.3  

---

## 1. Bundle Size & Chunk Splitting

Vendor dependencies are split into dedicated chunks in `vite.config.ts` via `manualChunks`:

| Chunk Name | Modules Included | Gzip Size | Purpose |
|---|---|---|---|
| `vendor-react` | `react`, `react-dom`, `react-router-dom` | 61.40 kB | Core application framework |
| `vendor-firebase` | `firebase/app`, `firebase/auth` | 34.27 kB | Authentication & persistence |
| `vendor-charts` | `recharts` | 105.32 kB | Posture & trend visualizations |
| `vendor-icons` | `lucide-react` | 8.68 kB | UI Iconography |
| `index` | App business logic & routes | 123.48 kB | Application codebase |

---

## 2. Lighthouse & Load Metrics (Staging Environment)

- **First Contentful Paint (FCP)**: 181.63 ms
- **Speed Index**: < 0.8 s
- **Time to Interactive (TTI)**: < 1.1 s
- **Total Blocking Time (TBT)**: 0 ms
- **Cumulative Layout Shift (CLS)**: 0.00
- **Lighthouse Performance Score**: **98 / 100**
- **Lighthouse Accessibility Score**: **100 / 100**
