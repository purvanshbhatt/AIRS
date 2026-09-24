# FindingsEngine

> 36 nodes · cohesion 0.07

## Key Concepts

- **FindingsEngine** (26 connections) — `app/services/findings.py`
- **Finding** (8 connections) — `app/services/findings.py`
- **.evaluate()** (8 connections) — `app/services/findings.py`
- **TestFindingsEngine** (8 connections) — `tests/test_findings.py`
- **FindingRule** (7 connections) — `app/services/findings.py`
- **FrameworkRefs** (5 connections) — `app/services/findings.py`
- **TestFindingsEngine** (5 connections) — `tests/test_frameworks.py`
- **.test_full_assessment_flow_with_frameworks()** (5 connections) — `tests/test_frameworks.py`
- **.get_summary()** (4 connections) — `app/services/findings.py`
- **.test_engine_custom_rules()** (4 connections) — `tests/test_findings.py`
- **.test_engine_handles_errors_gracefully()** (4 connections) — `tests/test_findings.py`
- **TestIntegration** (4 connections) — `tests/test_frameworks.py`
- **._get_domain_name()** (3 connections) — `app/services/findings.py`
- **._get_related_questions()** (3 connections) — `app/services/findings.py`
- **.__init__()** (3 connections) — `app/services/findings.py`
- **.test_engine_initialization()** (3 connections) — `tests/test_findings.py`
- **.test_finding_includes_framework_refs()** (3 connections) — `tests/test_frameworks.py`
- **.test_iv001_finding_has_mfa_techniques()** (3 connections) — `tests/test_frameworks.py`
- **.to_dict()** (1 connections) — `app/services/findings.py`
- **Framework references for a finding.** (1 connections) — `app/services/findings.py`
- **Definition of a finding rule.** (1 connections) — `app/services/findings.py`
- **Generated finding from a rule.** (1 connections) — `app/services/findings.py`
- **Deterministic rule-based findings engine. Evaluates assessment answers and…** (1 connections) — `app/services/findings.py`
- **Get domain display name from rubric.** (1 connections) — `app/services/findings.py`
- **Evaluate all rules against answers and scores. Args: answers: Dict mapping…** (1 connections) — `app/services/findings.py`
- *... and 11 more nodes in this community*

## Relationships

- [test_frameworks.py](test_frameworks.py.md) (7 shared connections)
- [test_findings.py](test_findings.py.md) (6 shared connections)
- [findings.py](findings.py.md) (6 shared connections)
- [api/verification.py](api-verification.py.md) (6 shared connections)
- [generate_findings](generate_findings.md) (3 shared connections)
- [get_rubric](get_rubric.md) (1 shared connections)
- [generate_detailed_roadmap](generate_detailed_roadmap.md) (1 shared connections)

## Source Files

- `app/services/findings.py`
- `tests/test_findings.py`
- `tests/test_frameworks.py`

## Audit Trail

- EXTRACTED: 67 (87%)
- INFERRED: 10 (13%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*