## Task Assignment for teamwork_preview_explorer_m1_1

**Mission**: Survey the `frontend/` directory and root `AIRS` repository to identify all legacy components, unused routes, duplicate providers/layouts, theme setup, and build configuration.

**Instructions**:
1. Read `P:\projects\AIRS\.agents\ORIGINAL_REQUEST.md` completely.
2. Inspect `P:\projects\AIRS\frontend\src` (components, pages, routes, hooks, contexts, providers, styles).
3. Identify legacy or retired components that are candidate for safe pruning.
4. Check references to ensure no active routes or components import these candidates before marking them for removal.
5. Check current TypeScript configuration, Vite/ESLint setup, and run build check (`npm run build` in `frontend/`) to record current build baseline.
6. Write a comprehensive investigation report in your working directory (`P:\projects\AIRS\.agents\teamwork_preview_explorer_m1_1\handoff.md`).
