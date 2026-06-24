# Open Source Readiness Audit — AIRS

Date: 2026-06-24
Repository: `purvanshbhatt/AIRS`
Scope: Community readiness, documentation quality, and GitHub best practices.

## Executive Summary
The repository is close to public-facing readiness (license, security policy, changelog, roadmap, issue templates, and CI workflows are present), but it is missing key community health files and has several documentation hygiene issues that reduce contributor trust and onboarding speed.

---

## 1) Missing Community Files

### High-priority missing files
1. **`CONTRIBUTING.md` missing**
   - Impact: No formal contribution flow, local validation expectations, branch/commit conventions, or PR review guidance.
2. **`CODE_OF_CONDUCT.md` missing**
   - Impact: No explicit behavior standards or enforcement contact for community participation.
3. **`SUPPORT.md` missing**
   - Impact: Users and contributors lack a clear support channel matrix (questions vs bugs vs security disclosures).
4. **`GOVERNANCE.md` missing**
   - Impact: Maintainer model, decision process, and release authority are undocumented.
5. **`CODEOWNERS` missing**
   - Impact: No auto-review ownership routing for critical paths.
6. **`.github/dependabot.yml` missing**
   - Impact: Dependency updates rely on manual effort; increased risk of stale/vulnerable dependencies.

---

## 2) Broken Links / Link Hygiene

### Confirmed broken internal links
Found in `frontend/src/pages/## Chat Customization Diagnostics.md`:
- Multiple links point to local Windows filesystem paths such as:
  - `c%3A/Users/purva/.vscode/...`
  - `C%3A/Users/purva/AppData/...`
- These are non-portable and invalid in GitHub context.

### Additional link concerns
- `docs/README.md` contains a placeholder YouTube link: `https://www.youtube.com/watch?v=YOUR_DEMO_VIDEO_ID` (in `docs/README.md`, lines 34–35).
- External URL availability checks from sandbox returned several `ERR` responses (likely network-restricted environment), so external link liveness could not be fully verified from this run.

---

## 3) Contributor Onboarding Gaps

Existing onboarding material is partial (`README.md`, `docs/LOCAL_DEV.md`), but contributor-specific onboarding is incomplete.

### Gaps
1. No contributor workflow document (`CONTRIBUTING.md`) covering:
   - how to pick issues,
   - branch naming,
   - commit message format,
   - required checks before PR,
   - code review and merge expectations.
2. Setup instructions are primarily **Windows PowerShell-oriented** (`README.md`, `docs/LOCAL_DEV.md`) with no first-class Linux/macOS path.
3. No explicit “good first issue” onboarding process or maintainer response SLAs.
4. No documented architecture entrypoint for new contributors beyond high-level docs.

---

## 4) Documentation Gaps

1. **Public docs build system is unclear**
   - `README.md` links to hosted docs, but repository lacks obvious docs site config (`mkdocs.yml`, `docs/.vitepress`, etc.).
2. **No dedicated API quickstart for external developers**
   - Docs mention endpoints and integration guides, but there is no concise “first API call in 5 minutes” onboarding page at repo root.
3. **No explicit compatibility/support matrix for runtime/tooling**
   - Node/Python minimum versions appear in some docs but are not consolidated into a single compatibility reference.

---

## 5) Stale Screenshot Signals

Screenshots exist (`images/dashboard.png`, `images/architecture.png`) and are referenced in `README.md`, but:
1. No capture date/version stamp is provided.
2. No process is documented for screenshot refresh during releases.
3. README mixes “Actual launch visuals” with rapidly evolving feature/version language, creating risk of visual drift over time.

Recommendation: treat these as **at-risk for staleness** unless tied to release tags or last-updated metadata.

---

## 6) Inconsistent Version References

### Observed inconsistencies
1. `README.md` claims enterprise readiness as of **`v0.3-enterprise-beta`** (line 125).
2. `SECURITY.md` supported versions list is **`v0.2.x` / `v0.1.x`**.
3. `CHANGELOG.md` latest released entry is **`0.2.0-staging`**.
4. `frontend/package.json` version is **`0.0.0`**.
5. `docs/governance-expansion-v1.md` references **`v0.7` / `v0.7.1`** staging concepts.

These version narratives are not aligned and can confuse users about current stable release state and support commitments.

---

## 7) GitHub Repository Best-Practice Recommendations

### Immediate recommendations (P0/P1)
1. Add `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md`, `GOVERNANCE.md`, and `CODEOWNERS`.
2. Remove or quarantine `frontend/src/pages/## Chat Customization Diagnostics.md` from public-facing docs/content if not intended for release.
3. Normalize versioning language across `README.md`, `SECURITY.md`, `CHANGELOG.md`, docs, and package manifests.
4. Add `.github/dependabot.yml` for Python and npm ecosystems.

### Recommended hardening (P2)
5. Add funding/community metadata (`.github/FUNDING.yml`) if open-source sponsorship is desired.
6. Add repository badges in `README.md` (CI status, license, release).
7. Add issue/PR triage automation (labeling, stale policy) if maintainer bandwidth is constrained.
8. Ensure branch protection requires CI/security workflows and dismisses stale approvals on new commits.
9. Add docs link checker in CI to prevent regressions in Markdown links.
10. Add release checklist documenting docs/screenshot/version update requirements.

---

## 8) Positive Readiness Signals Already Present

- `LICENSE` exists (AGPL-3.0).
- `SECURITY.md`, `CHANGELOG.md`, `ROADMAP.md` exist.
- Issue templates and PR template are present.
- CI, deploy, release, and security workflows are present under `.github/workflows/`.

---

## Conclusion
AIRS has a strong technical base for open-source publication, but community health and documentation consistency are the primary blockers. Addressing missing community standards files, link hygiene, and version alignment will significantly improve contributor confidence and external adoption readiness.
