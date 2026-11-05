# TestAssessmentIsolation

> 16 nodes · cohesion 0.12

## Key Concepts

- **TestAssessmentIsolation** (9 connections) — `tests/test_tenant_isolation.py`
- **.test_user_a_cannot_compute_score_for_user_b_assessment()** (3 connections) — `tests/test_tenant_isolation.py`
- **.test_user_a_cannot_create_assessment_for_user_b_org()** (3 connections) — `tests/test_tenant_isolation.py`
- **.test_user_a_cannot_download_user_b_report()** (3 connections) — `tests/test_tenant_isolation.py`
- **.test_user_a_cannot_get_user_b_assessment_by_id()** (3 connections) — `tests/test_tenant_isolation.py`
- **.test_user_a_cannot_get_user_b_assessment_summary()** (3 connections) — `tests/test_tenant_isolation.py`
- **.test_user_a_cannot_see_user_b_assessments()** (3 connections) — `tests/test_tenant_isolation.py`
- **.test_user_a_cannot_submit_answers_for_user_b_assessment()** (3 connections) — `tests/test_tenant_isolation.py`
- **Test that assessments are isolated per user.** (1 connections) — `tests/test_tenant_isolation.py`
- **User A should not see User B's assessments in list.** (1 connections) — `tests/test_tenant_isolation.py`
- **User A should get 404 when trying to access User B's assessment.** (1 connections) — `tests/test_tenant_isolation.py`
- **User A should get 400 when trying to create assessment for User B's org.** (1 connections) — `tests/test_tenant_isolation.py`
- **User A should get 404 when trying to access User B's assessment summary.** (1 connections) — `tests/test_tenant_isolation.py`
- **User A should get 404 when trying to download User B's report.** (1 connections) — `tests/test_tenant_isolation.py`
- **User A should get 404 when trying to submit answers for User B's assessment.** (1 connections) — `tests/test_tenant_isolation.py`
- **User A should get 404 when trying to compute score for User B's assessment.** (1 connections) — `tests/test_tenant_isolation.py`

## Relationships

- [make_auth_override](make_auth_override.md) (7 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)

## Source Files

- `tests/test_tenant_isolation.py`

## Audit Trail

- EXTRACTED: 23 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*