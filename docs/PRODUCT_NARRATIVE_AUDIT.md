# ResilAI Product Narrative Audit

**Objective:** Audit the product narrative against the actual implementation, specifically distinguishing the Deterministic Verification Engine from the Gemini Business Impact Engine.

## 1. The Core Issue: Narrative Bleed

The frontend implementation currently conflates deterministic evidence with AI-generated narrative. The product claims to be an evidence-backed verification engine, but the frontend UI frequently uses hardcoded fallbacks (`|| 98`) to manufacture "green" status when deterministic data is missing. 

Furthermore, the frontend asks the AI to calculate or format scores in certain legacy views, which violates the architectural boundary. 

### The Required Boundary

**ResilAI Deterministic Governance/Verification Engine:**
- Consumes normalized evidence from connectors (Wazuh, Splunk).
- Applies deterministic rules (e.g., "MFA must be active on all admin accounts").
- Calculates readiness scores and compliance percentages using strict math.
- Determines findings based on boolean rule triggers.
- Performs framework applicability and mapping (e.g., mapping to NIST CSF).
- **Rule:** This engine *never* guesses. If data is missing, the score is penalized or marked as "Unknown".

**Gemini Business Impact Engine:**
- Explains verified findings in plain English.
- Translates technical conditions (e.g., "Port 22 exposed") into business impact ("Ransomware entry point left open").
- Generates executive narratives for the Morning Brief.
- Proposes remediation narratives and step-by-step fixes.
- **Rule:** Gemini must *never* calculate readiness, alter findings, determine framework mappings, or manufacture evidence.

## 2. Narrative vs Implementation Mismatches

1. **"100% Evidence-Backed" vs Hardcoded UI**
   - *Narrative:* ResilAI provides continuous, evidence-backed verification of your clinical systems.
   - *Implementation:* The `TodayPage` and `Connectors` page fallback to `98%` health and `14/14` verified systems if the API response is incomplete. This creates a false sense of security.

2. **"AI-Driven Insights" vs "AI-Driven Scoring"**
   - *Narrative:* AI translates technical risk into executive action.
   - *Implementation:* Some legacy components (like older `Analytics` tabs) implicitly rely on generative AI to summarize "how well we are doing", blending score calculation with narrative generation.

3. **Progressive Disclosure Failure**
   - *Narrative:* Executives get the summary; IT gets the evidence.
   - *Implementation:* Currently, the UI jumps erratically between high-level summaries and deep JSON telemetry without a smooth "drill-down" path. 

## 3. Recommended Terminology Changes

- **Avoid:** "AI Security Score", "Gemini calculated risk"
- **Use:** "Verified Readiness Score", "Evidence-backed Posture"
- **Avoid:** "The AI found a vulnerability"
- **Use:** "The Verification Engine detected a vulnerability; the AI Translator explains the impact."
- **Avoid:** "Self-Assessment"
- **Use:** "Baseline Verification"
