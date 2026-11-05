# RESILAI AGENT GOVERNANCE PROTOCOL (MANDATORY)

You are an engineering contributor working on the ResilAI codebase.

Before performing ANY analysis, coding, architecture review, implementation, deployment, refactor, documentation update, or recommendation, you MUST follow this protocol.

---

## PHASE 1: LOAD PROJECT MEMORY

Before opening source code files, read the following files in this exact order:

1. docs/agent_memory/AGENT_START.md
2. docs/agent_memory/PROJECT_STATE.md
3. docs/agent_memory/PRODUCT_MOAT.md
4. docs/agent_memory/CURRENT_SPRINT.md
5. docs/agent_memory/NEXT_TASKS.md
6. docs/agent_memory/CODE_INDEX.md
7. docs/agent_memory/OWNERSHIP_MAP.md
8. docs/agent_memory/DEPENDENCY_MAP.md

These files are the authoritative source of truth.

Do NOT assume architecture, versions, roadmap, ownership, priorities, or product positioning without first reading these files.

---

## PHASE 2: DETERMINE SCOPE

Identify:

* Current sprint objective
* Current task priority
* Architectural dependencies
* Ownership boundaries
* Product constraints

Determine which team you belong to:

* Backend Core
* Backend Security
* Backend Intelligence
* Frontend UX
* DevOps
* Research
* Product Strategy

Only work within your assigned domain unless explicitly instructed otherwise.

---

## PHASE 3: TARGETED FILE DISCOVERY

Do NOT scan the entire repository.

Use CODE_INDEX.md and OWNERSHIP_MAP.md to locate the relevant files.

Open only:

* files directly related to your task
* direct dependencies
* interfaces you must integrate with

Avoid repository-wide searches unless absolutely required.

Minimize token consumption.

---

## PHASE 4: VALIDATE AGAINST PRODUCT MOAT

Every proposed change must be checked against PRODUCT_MOAT.md.

Reject any implementation that violates:

* deterministic scoring
* evidence-first philosophy
* telemetry verification
* trust-first architecture
* executive-focused reporting

Never introduce functionality that turns ResilAI into generic GRC software.

---

## PHASE 5: EXECUTE TASK

Implement only the requested scope.

Respect:

* existing architecture
* ownership boundaries
* dependency graph
* sprint priorities

Do not redesign unrelated systems.

Do not introduce new frameworks without justification.

Do not move architecture away from FastAPI, React, Cloud Run, PostgreSQL, Firebase Auth, and Gemini.

---

## PHASE 6: UPDATE MEMORY

After completing work, update ALL applicable memory files.

Required:

ACTIVE_CONTEXT.md

Update:
* short-term memory of this run
* task status changes

Only update the following larger files if something materially changes:
* CURRENT_SPRINT.md
* NEXT_TASKS.md
* BACKEND_STATE.md
* FRONTEND_STATE.md
* DEVOPS_STATE.md

---

## PHASE 7: AGENT HANDOFF

Append a new entry to AGENT_LOG.md.

Format:

Date:
Agent:
Task:

Changes Made:
* item
* item

Files Modified:
* file
* file

Dependencies Created/Updated:
* dependency

Business Impact:
* impact

Next Recommended Task:
* task

Blocked By:
* blocker

Affected Teams:
* backend
* frontend
* devops

---

## PHASE 8: FINAL REPORT

At completion provide:

1. Summary
2. Files changed
3. Memory files updated
4. Architectural impact
5. Risks
6. Recommended next task

---

## TOKEN EFFICIENCY RULE

Reading order:

1. Memory files
2. Indexed files
3. Direct dependencies

NEVER start by scanning the repository.

Repository-wide searches require justification.

The memory layer exists specifically to avoid unnecessary token consumption.

---

## RESILAI NON-NEGOTIABLE RULES

1. LLMs NEVER calculate readiness scores.
2. LLMs NEVER modify findings.
3. LLMs NEVER determine framework mappings.
4. Gemini is narrative-only.
5. Scoring remains deterministic.
6. Telemetry is preferred over questionnaires.
7. Evidence is preferred over self-attestation.
8. Trust and auditability are product priorities.
9. Executive reporting must remain board-ready.
10. All changes must strengthen the ResilAI moat.

Failure to follow this protocol is considered a process violation.
