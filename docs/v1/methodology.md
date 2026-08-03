# ResilAI Methodology

## Scoring Principles

ResilAI uses deterministic scoring. The same answers and rubric version always produce the same outputs.

- LLM output is optional and narrative-only
- Numeric scores and severity decisions are rule-based
- Framework mappings are deterministic

## Assessment Domains

| Domain | ID | Weight | Focus |
| --- | --- | --- | --- |
| Telemetry and Logging | `tl` | 20% | Collection, retention, centralization |
| Detection Coverage | `dc` | 25% | Monitoring and detection controls |
| Identity Visibility | `id` | 20% | IAM, MFA, privileged access |
| Incident Response | `ir` | 20% | Playbooks and response maturity |
| Resilience | `rs` | 15% | Backup and recovery readiness |

## Question Types

- Boolean: full points for compliant answers
- Numeric: threshold-based scoring bands
- Percentage: percentage thresholds mapped to point bands

## Formula

### 1. Domain score (0-5)

`domain_score = (points_earned / max_points) * 5`

### 2. Weighted contribution

`contribution = (domain_score / 5) * domain_weight`

### 3. Overall score (0-100)

`overall_score = sum(all_domain_contributions)`

## Maturity Levels

| Score Range | Level | Label |
| --- | --- | --- |
| 0-39 | 1 | Initial |
| 40-59 | 2 | Developing |
| 60-79 | 3 | Defined |
| 80-100 | 4 | Optimized |

## Finding Generation

Findings are generated from scored control gaps:

- Gap >= 75%: High
- Gap >= 50%: Medium
- Gap < 50%: Low

## Remediation Roadmap

Roadmap phases follow operational urgency:

- Day 30: critical actions
- Day 60: high-priority closure
- Day 90: medium and optimization work

## AI Narrative Usage

When LLM is enabled, ResilAI may generate:

- Executive narrative
- Roadmap narrative context
- Business-facing interpretation text

LLM does not modify:

- Numeric score
- Maturity level
- Severity ranking
- Framework mappings

## Reproducibility Guarantee

Given identical answers and rubric version, ResilAI guarantees identical scoring, findings, and framework mapping outputs.
