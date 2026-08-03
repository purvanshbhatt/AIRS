# DevOps State

Environments:
- Staging (URL: airs-staging-0384513977.web.app / airs-api-staging)
- Demo (URL: gen-lang-client-0384513977.web.app / airs-api-demo)
- Production (URL: resilai-marketing.web.app -> resilai.org / airs-api)

Deployment Scripts:
- `scripts/deploy_cloud_run.ps1`
- `scripts/deploy_frontend.ps1`

Recent Changes:
- 2026-08-03: Force-patched frontend dependency graph (resolved 48 Dependabot vulnerabilities across websocket-driver, vite, react-router, tmp, braces, micromatch, cross-spawn via package.json overrides; commit f071157).
- Corrected Gemini API key in all backends
- Unlocked Demo deployment in scripts
