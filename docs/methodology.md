# AIRS Methodology

## Scoring Philosophy

AIRS uses a **deterministic scoring model** where every score is reproducible given the same inputs. There is no randomness or AI-driven modification of scores.

> **Key Principle:** AI is used *only* for generating human-readable narratives. All scores, findings, and recommendations are computed algorithmically.

## Assessment Domains

AIRS evaluates security readiness across five core domains:

| Domain | ID | Weight | Focus Area |
|--------|-----|--------|------------|
| **Telemetry & Logging** | `tl` | 20% | Log collection, retention, centralization |
| **Detection Coverage** | `dc` | 25% | EDR, network monitoring, threat detection |
| **Identity Visibility** | `id` | 20% | IAM, MFA, privileged access |
| **Incident Response** | `ir` | 20% | Playbooks, tabletops, response capabilities |
| **Resilience** | `rs` | 15% | Backups, recovery, business continuity |

## Question Types

Each domain contains 5 questions using standardized formats:

### Boolean Questions
```
Example: "Do you have centralized logging?"
Scoring: Yes = Full points, No = 0 points
```

### Numeric Questions
```
Example: "What is your log retention period (days)?"
Scoring: Threshold-based (90+ days = Full, 30-89 = Partial, <30 = Low)
```

### Percentage Questions
```
Example: "What percentage of endpoints have EDR?"
Scoring: 90%+ = Full, 70-89% = High, 50-69% = Medium, <50% = Low
```

## Scoring Formula

### Step 1: Domain Score (0-5 scale)
```
Domain Score = (Points Earned / Max Points) × 5
```

### Step 2: Weighted Contribution
```
Contribution = (Domain Score / 5) × Domain Weight
```

### Step 3: Overall Score (0-100)
```
Overall Score = Σ (All Domain Contributions)
```

## Maturity Levels

Based on the overall score, organizations are assigned a maturity level:

| Score Range | Level | Name | Description |
|-------------|-------|------|-------------|
| 0-39 | 1 | **Initial** | Ad-hoc security, significant gaps |
| 40-59 | 2 | **Developing** | Some controls, inconsistent application |
| 60-79 | 3 | **Defined** | Established processes, room for improvement |
| 80-100 | 4 | **Optimized** | Strong posture, continuous improvement |

## Finding Generation

Findings are generated automatically based on scoring gaps:

1. **Gap Detection**: Questions where earned < possible points
2. **Severity Assignment**: Based on point gap magnitude
   - Gap ≥ 75% → HIGH
   - Gap ≥ 50% → MEDIUM
   - Gap < 50% → LOW
3. **Prioritization**: Sorted by severity and domain weight

## Roadmap Construction

The 30/60/90 day roadmap is built deterministically:

| Phase | Timeline | Finding Types | Rationale |
|-------|----------|---------------|-----------|
| Day 30 | Immediate | CRITICAL severity | Address existential risks |
| Day 60 | Short-term | HIGH severity | Close major gaps |
| Day 90 | Medium-term | MEDIUM/LOW | Optimization and hardening |

## AI Narrative Generation (Optional)

When LLM features are enabled:

### What AI Generates
- Executive summary paragraphs
- Roadmap narrative descriptions
- Business-friendly finding rewrites

### What AI Cannot Modify
- ❌ Numeric scores
- ❌ Maturity levels
- ❌ Finding severity
- ❌ Recommendations
- ❌ Framework mappings

### Transparency
The UI clearly indicates:
- `llm_enabled: true/false` in API responses
- "AI Generated" badges on narrative sections
- Model name displayed (e.g., "Gemini 2.0")

## Reproducibility Guarantee

Given identical:
- Assessment answers
- Rubric version
- Baseline profiles

AIRS will produce identical:
- Overall score
- Domain scores
- Findings
- Recommendations
- Framework mappings

This reproducibility is essential for audit trails and compliance documentation.
