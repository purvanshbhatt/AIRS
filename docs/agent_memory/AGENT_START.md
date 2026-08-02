BEFORE IMPLEMENTING ANY FEATURE:

1. Read:
   - AGENT_START.md
   - PROJECT_STATE.md
   - PRODUCT_MOAT.md
   - CURRENT_SPRINT.md
   - NEXT_TASKS.md
   - CODE_INDEX.md
   - OWNERSHIP_MAP.md
   - DEPENDENCY_MAP.md

2. Validate against PRODUCT_MOAT.md.

3. Reject any implementation that turns ResilAI into:
   - SIEM
   - Vulnerability Scanner
   - Generic GRC Platform
   - Asset Management Platform

4. Every feature must directly improve:
   - Incident Readiness
   - Evidence Verification
   - Deterministic Scoring
   - Executive Decision Making

5. Do not delete models, tables, APIs, or services without:
   - migration path
   - rollback plan
   - staging validation
   - explicit approval

Step 6
After changes:
Update ACTIVE_CONTEXT.md and AGENT_LOG.md. These are the ONLY files you should update every run.
Only update the larger project state files (PROJECT_STATE.md, BACKEND_STATE.md, FRONTEND_STATE.md, CURRENT_SPRINT.md) when something materially changes.

Commit summary.

---

# Ownership

**Backend Agent**
Owns:
- `app/services/`
- `app/api/`
- `app/models/`
- `app/db/`

**Frontend Agent**
Owns:
- `frontend/src/pages/`
- `frontend/src/components/`
- `frontend/src/hooks/`
- `frontend/src/api.ts`

**DevOps Agent**
Owns:
- `scripts/`
- `gcp/`
- `firebase.json`
