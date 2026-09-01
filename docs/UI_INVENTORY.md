# ResilAI Frontend UI Inventory

**Scope**: Routes and components identified via `CODE_INDEX.md` (`app/main.py`, `frontend/src/pages/Dashboard.tsx`, etc.) and the core `App.tsx` router.

## 1. Routes & Pages Inventory

### `frontend/src/pages/Dashboard.tsx` (Legacy Dashboard)
- **Route:** `/dashboard` (currently redirected to `/morning-brief`)
- **Purpose:** Executive view of Audit Confidence and Verification Status.
- **Intended Persona:** C-Suite / IT Ops
- **Information Hierarchy:** High-level scores (GHI, RRI), upcoming audits, open actions, telemetry status.
- **Backend/API Source:** `getGovernanceHealthIndex()`, `getSystemStatus()`, `getAuditCalendar()`
- **Deterministic vs Narrative:** Mixed. Uses `getExecutiveExplanation()` for narrative, but attempts to display deterministic GHI scores.
- **Hardcoded/Mock Values:** 
  - `activeGhiData.ghi || 0`
  - `upcomingAudits[0]?.days_until_audit || 12`
  - `openActions + inProgressActions || 22`
- **Workspace:** Executive Briefing / Operations

### `frontend/src/features/readiness/TodayPage.tsx` (Morning Brief)
- **Route:** `/morning-brief`
- **Purpose:** Executive status of the clinic's readiness to operate.
- **Intended Persona:** Clinic Director / VP Ops
- **Information Hierarchy:** North Star status (Ready vs Action Required), Morning Brief narrative, Readiness Score gauge.
- **Backend/API Source:** `getDailyReadinessReport()`
- **Deterministic vs Narrative:** Narrative-heavy (morning brief summary) layered over deterministic scores.
- **Hardcoded/Mock Values:**
  - `report.clinic_health_pct || 98`
  - `report.verification?.verified_items_count || 14`/`14`
  - `report.verification?.total_items_count || 142`
- **Workspace:** Executive Briefing

### `frontend/src/components/ResultsTabs.tsx` (Assessment Results)
- **Route:** `/activity/compliance-drift` (and Assessment runs)
- **Purpose:** Display domain scores, framework mappings, and findings.
- **Intended Persona:** Compliance Officer / IT Auditor
- **Information Hierarchy:** Overall Risk, Domain Scores, Framework Coverage, Findings List.
- **Backend/API Source:** Assessment & Findings Engine
- **Deterministic vs Narrative:** Deterministic.
- **Hardcoded/Mock Values:**
  - `mitre_techniques_total || 40`
  - `cis_controls_total || 56`
  - `owasp_total || 10`
- **Workspace:** Operations / IT Security

### `frontend/src/pages/Connectors.tsx` (Integrations)
- **Route:** `/connectors`
- **Purpose:** Telemetry source management (Wazuh, Splunk, Azure).
- **Intended Persona:** Systems Administrator / SRE
- **Information Hierarchy:** Connector health, evidence confidence.
- **Backend/API Source:** `getEvidenceConfidence()`
- **Deterministic vs Narrative:** Deterministic evidence telemetry.
- **Hardcoded/Mock Values:** `overall_confidence_pct || 98`
- **Workspace:** IT / Security

### `frontend/src/pages/Governance.tsx` (Governance)
- **Route:** `/governance`
- **Purpose:** Multi-unit policy and risk thresholds.
- **Intended Persona:** CISO / Compliance Director
- **Information Hierarchy:** Organizational compliance posture.
- **Backend/API Source:** `getGovernanceHealthIndex()`
- **Deterministic vs Narrative:** Deterministic.
- **Hardcoded/Mock Values:** `overall_score || 98%`
- **Workspace:** Administration / Operations

## 2. Hardcoded Assertion Audit

The following UI components present compliance or health assertions that bypass backend verification or provide fake fallback data:

1. **Dashboard.tsx**: Hardcoded upcoming audit days (`|| 12`) and open action counts (`|| 22`). 
2. **TodayPage.tsx**: Hardcodes clinic health to `98` if missing. Fakes verified items as `14/14` and total clinical accounts as `142`.
3. **ResultsTabs.tsx**: Hardcodes framework coverage denominators (`40` for MITRE, `56` for CIS, `10` for OWASP).
4. **Connectors.tsx**: Fakes telemetry confidence at `98%` if the backend evidence API fails.
5. **Governance.tsx**: Fakes overall governance score at `98%`.

*Conclusion: The UI heavily masks backend failures by defaulting to "green" or "passing" states, which violates the core trust model of an evidence-backed verification engine.*
