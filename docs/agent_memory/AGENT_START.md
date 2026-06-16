Before making changes:

Step 1
Read: PROJECT_STATE.md and PRODUCT_MOAT.md

Step 2
Read: ARCHITECTURE_DECISIONS.md

Step 3
Read: CURRENT_SPRINT.md and NEXT_TASKS.md

Step 4
Read: DEPENDENCY_MAP.md and OWNERSHIP_MAP.md

Step 5
Read: CODE_INDEX.md to find exactly which files to edit.
ONLY inspect files directly related to your task.
Do not scan the entire repository.

Step 6
After changes:
Update BACKEND_STATE.md, FRONTEND_STATE.md, or DEVOPS_STATE.md.
Update CURRENT_SPRINT.md.
Update PROJECT_STATE.md.

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
