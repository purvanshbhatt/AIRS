# ResilAI — Deterministic Readiness Engine Core

## 📐 Product Invariant: Non-LLM Mathematical Math

The ResilAI Deterministic Engine guarantees that **no numerical score is ever generated or hallucinated by a Large Language Model**.

All scores are mathematically computed based on normalized telemetry evidence pulled directly from enterprise infrastructure.

---

## 🧮 Core Scoring Formulation

Readiness $R$ for an organization or clinic is calculated as a weighted combination of **Trust ($T$)**, **Coverage ($C$)**, and **Risk Mitigation ($M$)**:

$$R = \left( w_t \cdot T + w_c \cdot C + w_m \cdot M \right) \times (1 - D)$$

Where:
* $T \in [0, 100]$: **Trust Score** derived from authenticated telemetry freshness and adapter confidence.
* $C \in [0, 100]$: **Coverage Score** representing the ratio of monitored assets to total inventory.
* $M \in [0, 100]$: **Risk Mitigation** calculated from resolved security advisories and backup freshness.
* $D \in [0, 1]$: **Drift Penalty** incurred when critical assets miss telemetry heartbeats for >24 hours.

---

## 🔒 Verification & Anti-Hallucination Guardrails

1. **Fallback Null Handling**: Missing evidence returns an explicit em-dash (`—`) rather than fabricated numbers or zero fallbacks.
2. **Immutable Ledger Hooks**: Every score calculation creates an immutable `ReadinessLedgerEntry` in Firestore containing the underlying telemetry hashes.
3. **LLM Boundary Scoping**: Gemini 3 Flash is restricted purely to summarizing the pre-calculated mathematical output in executive plain text.
