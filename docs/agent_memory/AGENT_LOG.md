# AGENT_LOG.md

2026-06-16

Agent: Antigravity

Added:
- Agent Memory System (`docs/agent_memory/`)
- Async tech stack discovery (`app/api/tech_stack.py`)
- Archive assessment functionality (`app/services/assessment.py`, frontend)

Reason:
- Improve agent collaboration context caching.
- Prevent CORS timeouts in production.
- Provide compliance-friendly deletion UX.

Impacts:
- All future agents must read `AGENT_START.md` before executing.

---

2026-06-18

Agent: Antigravity

Added:
- CORSErrorSafetyMiddleware (`app/core/middleware.py`)
- Complete CORS origin list in `gcp/env.prod.yaml`

Reason:
- Production CORS error observed at AWS Summit caused by Cloud Run stripping headers on 5xx.

Files Modified:
- `app/core/middleware.py`
- `app/main.py`
- `gcp/env.prod.yaml`

Dependencies Created:
- CORSErrorSafetyMiddleware must always be the LAST middleware added (runs first in the stack).

Business Impact:
- Eliminates CORS errors for live demos and investor presentations.

Next Recommended Task:
- Verify CORS headers present on production after deployment.

Affected Teams:
- Backend
- DevOps
