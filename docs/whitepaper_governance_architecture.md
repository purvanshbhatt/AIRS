# Deterministic Governance Inference & Validation Architecture for Continuous Compliance Intelligence

**AIRS Platform — Technical White Paper**
**Version 1.0 | February 2026**

---

## Abstract

Enterprise adoption of AI-assisted security tooling has exposed a fundamental tension: large language models excel at synthesizing human-readable narratives, but they cannot serve as the system of record for governance, risk, and compliance (GRC) decisions. This paper presents the architecture behind the AIRS platform's dual-engine design — an **AI Narrative Engine** for consultant-grade text and a **Deterministic Governance Engine** for auditable, reproducible compliance inference. We formalize the Governance Health Index (GHI), a weighted composite metric, and describe the Internal Governance Validation Framework (IGVF) that provides continuous regression assurance over governance logic without LLM dependency.

---

## 1. The "Black Box" Problem

Modern AI security platforms increasingly rely on LLMs to generate risk assessments, maturity scores, and compliance recommendations. While the natural-language output appears authoritative, this approach introduces three structural failures that disqualify it from enterprise audit standards:

**Non-determinism.** Given identical inputs, an LLM may produce different severity classifications, score justifications, or framework mappings across successive invocations. Auditors require that the same organizational profile, finding set, and technology stack produce the *exact same* governance score every time. Stochastic outputs cannot satisfy SOC 2 Type II evidence requirements or ISO 27001 Annex A control traceability.

**Opacity of inference.** When an LLM determines that an organization is "HIPAA-applicable," the reasoning chain is embedded in transformer attention weights — not in an auditable rule set. An external assessor cannot inspect, version-control, or unit-test the decision boundary. This makes the compliance determination itself an unverifiable artifact, which is antithetical to the evidentiary standards demanded by frameworks like FedRAMP, CMMC, and PCI-DSS.

**Score contamination risk.** If the same model that generates narrative text also computes numeric scores, there is no architectural guarantee that a prompt injection, model update, or hallucination will not silently alter a maturity rating from "Developing" to "Advanced." The blast radius of a single model failure extends across the entire assessment output.

These are not hypothetical concerns. They represent the gap between "AI-assisted" and "audit-ready" — a gap that the AIRS architecture is specifically designed to close.

---

## 2. Architecture: Dual-Engine Separation

AIRS enforces a strict separation of concerns between two independent processing paths:

```
┌──────────────────────────────────────────────────────────────────┐
│                        AIRS Platform                             │
│                                                                  │
│  ┌─────────────────────┐      ┌─────────────────────────────┐   │
│  │  AI Narrative Engine │      │  Deterministic Governance   │   │
│  │  (Google Gemini)     │      │  Engine (Pure Python)       │   │
│  │                      │      │                             │   │
│  │  ✓ Executive summary │      │  ✓ Compliance inference     │   │
│  │  ✓ 30/60/90 roadmap  │      │  ✓ Audit readiness score    │   │
│  │  ✗ No score compute  │      │  ✓ SLA gap analysis         │   │
│  │  ✗ No framework map  │      │  ✓ Lifecycle risk scoring   │   │
│  │  ✗ No findings data  │      │  ✓ GHI composite index      │   │
│  └─────────────────────┘      └─────────────────────────────┘   │
│          │                                │                      │
│          │ Narrative text only            │ Structured scores    │
│          ▼                                ▼                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Assessment Output                      │   │
│  │   Deterministic scores + AI-generated narrative text     │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### 2.1 AI Narrative Engine

The Narrative Engine wraps Google Gemini (via the `google-genai` SDK) and is scoped exclusively to text generation. It receives *pre-computed* assessment data — scores, findings, maturity levels — as a read-only input payload and produces two outputs: an executive summary paragraph and a 30/60/90-day remediation roadmap narrative. Critically, the LLM **cannot modify** numeric scores, maturity tiers, finding counts, severity classifications, or any structured data. If the LLM is unavailable or fails, the system falls back to deterministic template-based text with zero impact on governance scores.

### 2.2 Deterministic Governance Engine

The Governance Engine is implemented as a pure Python package (`app.services.governance`) with no LLM dependency. It contains four sub-engines:

| Sub-Engine | Module | Function |
|---|---|---|
| **Compliance Engine** | `compliance_engine.py` | Rule-based framework applicability mapping (HIPAA, PCI-DSS, CMMC, GDPR, SOC 2, NIST AI RMF, FedRAMP, FFIEC) |
| **Audit Calendar** | `audit_calendar.py` | Audit scheduling, enrichment, and deadline forecasting |
| **Lifecycle Engine** | `lifecycle_engine.py` | Static version lifecycle intelligence from versioned JSON configuration — EOL dates, LTS status, deprecation windows |
| **Tech Stack Service** | `tech_stack.py` | Technology stack risk classification and major-version-behind detection |

Every function in this package is deterministic: same inputs → same outputs → same audit trail. The entire decision surface is unit-testable, version-controlled, and diff-auditable.

---

## 3. The Governance Health Index (GHI)

The GHI is a composite governance posture metric that collapses four independent dimensions into a single 0–100 score with a letter grade:

$$\text{GHI} = (\text{Audit} \times 0.4) + (\text{Lifecycle} \times 0.3) + (\text{SLA} \times 0.2) + (\text{Compliance} \times 0.1)$$

### 3.1 Dimension Definitions

**Audit Readiness (weight: 0.4).** Measures the severity burden of open findings. Starting from a perfect score of 100, deductions are applied per finding severity:

$$\text{Audit Score} = \max\!\Big(0,\; 100 - (\text{Critical} \times 15) - (\text{High} \times 8) - (\text{Medium} \times 3)\Big)$$

Low-severity findings carry zero deduction weight but are still counted for reporting. Only findings with status `open` or `in_progress` are evaluated; `resolved` and `accepted` findings are excluded. This dimension receives the highest weight (0.4) because unresolved critical findings represent the most immediate governance risk.

**Lifecycle Risk (weight: 0.3).** Aggregates technology stack health across all registered components:

$$\text{Lifecycle Score} = \max\!\Big(0,\; 100 - (\text{EOL} \times 25) - (\text{Deprecated} \times 15) - (\text{Outdated} \times 5)\Big)$$

A component is classified as *outdated* when it is two or more major versions behind the current release. Lifecycle status is resolved from a static, versioned `lifecycle_config.json` — no live API calls, no scraping — ensuring reproducibility in air-gapped environments.

**SLA Gap (weight: 0.2).** Evaluates whether an organization's stated SLA target is achievable given its declared application tier:

| Condition | Status | Score |
|---|---|---|
| Target meets or exceeds tier requirement | `on_track` | 100 |
| Gap ≤ 0.5% | `at_risk` | 60 |
| Gap > 0.5% | `unrealistic` | 20 |
| Tier or target not configured | `not_configured` | 0 |

Tier SLA requirements follow industry convention: Tier 1 = 99.99%, Tier 2 = 99.9%, Tier 3 = 99.5%, Tier 4 = 99.0%.

**Compliance (weight: 0.1).** Measures governance profile completeness and framework applicability awareness. If the organization's profile attributes trigger at least one applicable framework (e.g., `processes_phi → HIPAA`), the score is 100. If the profile is configured but triggers no frameworks, the score is 50. An unconfigured profile scores 0. This dimension has the lowest weight because the current implementation measures *awareness*, not *control implementation depth* — a distinction reserved for future SIEM-integrated verification.

### 3.2 Grade Mapping

| GHI Range | Grade | Interpretation |
|---|---|---|
| 90–100 | **A** | Governance posture exceeds requirements |
| 80–89 | **B** | Strong posture with minor gaps |
| 60–79 | **C** | Acceptable with identified improvements needed |
| 40–59 | **D** | Significant governance gaps requiring remediation |
| 0–39 | **F** | Critical governance deficiencies |

An organization **passes** IGVF validation only when it has zero critical issues *and* a GHI ≥ 60.

---

## 4. Assurance: The Internal Governance Validation Framework (IGVF)

Deterministic logic is only trustworthy if it is continuously verified. The IGVF is the platform's internal assurance layer — a staging-only subsystem that prevents governance logic regression.

### 4.1 Architecture

The IGVF operates through three interfaces:

1. **Validation Engine** (`validation_engine.py`) — The core computation module. It orchestrates all four dimension engines, computes the GHI, determines pass/fail status, and emits structured JSON log events (`audit_readiness_inputs`, `compliance_inference_result`, `sla_gap_calculation`) traceable by `organization_id` with no PII exposure.

2. **Internal API Endpoint** (`/internal/governance/validate/{organization_id}`) — A protected REST endpoint gated by two dependencies:
   - **Environment gate:** Returns HTTP 404 (not 403) when `ENV ≠ staging`, making the endpoint *invisible* — not merely forbidden — in production and demo environments.
   - **Admin token authentication:** Requires an `X-Admin-Token` header validated against a server-side environment variable, bypassing the standard Firebase authentication path to avoid coupling internal assurance to user identity.

3. **CLI Tool** (`scripts/validate_governance.py`) — A command-line interface that invokes the Validation Engine directly (no HTTP round-trip) with `--org`, `--json`, and `--brief` flags. Returns exit code 1 on any validation failure, enabling CI/CD pipeline integration.

### 4.2 CI/CD Integration

The platform's GitHub Actions CI pipeline includes a dedicated `governance-validation` job that executes after the main test suite:

```yaml
governance-validation:
  needs: backend-tests
  steps:
    - run: pytest tests/test_igvf.py -v --tb=short   # 79 unit tests
    - run: python scripts/validate_governance.py --brief  # CLI exit-code check
```

Any regression in audit score computation, compliance inference rules, SLA gap thresholds, lifecycle classification, or GHI aggregation will fail the pipeline before code reaches staging. The 79-test suite covers boundary conditions (e.g., exactly zero critical findings, GHI at grade boundaries, EOL-only stacks) and API-level behavior (environment gating, token rejection, multi-org scans).

### 4.3 Structured Logging for Audit Trail

Each dimension computation emits a structured JSON log entry containing the inputs, intermediate calculations, and output score — but never PII or secrets. Example:

```json
{
  "event": "audit_readiness_inputs",
  "organization_id": "org-12345",
  "total_open": 7,
  "critical_count": 1,
  "high_count": 2,
  "medium_count": 4,
  "low_count": 0,
  "deductions": {"critical": 15, "high": 16, "medium": 12},
  "score": 57.0
}
```

These logs enable post-hoc reconstruction of any governance score — a requirement for audit evidence packages under SOC 2, ISO 27001, and FedRAMP continuous monitoring.

---

## 5. Evidence-Based GRC: From Self-Reporting to Verified Posture

Traditional GRC workflows rely on self-reported questionnaires: an organization *claims* it encrypts data at rest, *claims* it patches within SLA, *claims* it has no end-of-life components. The AIRS architecture moves toward **evidence-based governance** through three progressively stronger verification tiers:

| Tier | Source | Verification Level | Current Status |
|---|---|---|---|
| **Tier 1: Profile-Declared** | Organization self-reports attributes (industry, data types, regions) | Compliance *awareness* — frameworks are inferred, not verified | ✅ Implemented |
| **Tier 2: Platform-Observed** | Findings from integrated scanners, tech stack from dependency manifests, uptime from monitoring webhooks | Compliance *evidence* — claims are checked against platform-ingested data | ✅ Partially implemented (integration endpoints, webhook delivery, external findings) |
| **Tier 3: SIEM-Verified** | Continuous telemetry from SIEM/SOAR platforms (Splunk, Sentinel, CrowdStrike) confirming control effectiveness | Compliance *assurance* — posture is independently verified by operational data | 🔜 Roadmap |

The GHI is architected to incorporate higher-fidelity evidence as integration depth increases. The compliance dimension weight (currently 0.1) is intentionally low because Tier 1 awareness provides limited assurance. As Tier 2 and Tier 3 data sources are connected, the weighting model can be recalibrated without altering the composite formula structure — only the per-dimension scoring functions evolve.

This progression mirrors the maturity model used by FedRAMP's continuous monitoring program: organizations begin with self-attestation, move to automated scanning evidence, and ultimately achieve continuous authorization through real-time telemetry. The AIRS platform provides the computational substrate for each stage.

---

## 6. Conclusion

The separation of AI narrative generation from deterministic governance computation is not an implementation detail — it is an architectural invariant that determines whether a platform's output can survive an external audit. By formalizing governance posture into the GHI, gating that logic with the IGVF's 79-test regression suite, and designing for progressive evidence integration, the AIRS platform delivers compliance intelligence that is reproducible, auditable, and extensible — properties that no LLM alone can guarantee.

---

**References**

- NIST SP 800-53 Rev. 5 — Security and Privacy Controls for Information Systems
- NIST AI RMF 1.0 — Artificial Intelligence Risk Management Framework
- ISO/IEC 27001:2022 — Information Security Management Systems
- FedRAMP Continuous Monitoring Strategy Guide
- SOC 2 Type II — Trust Services Criteria (AICPA)
- PCI DSS v4.0 — Payment Card Industry Data Security Standard

---

*AIRS — AI Incident Readiness & Security Platform*
*© 2026. All rights reserved.*
