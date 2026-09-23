# create_explanation

> 8 nodes · cohesion 0.32

## Key Concepts

- **create_explanation()** (9 connections) — `app/api/explanations.py`
- **_verify_org_access()** (8 connections) — `app/api/explanations.py`
- **Session** (2 connections)
- **User** (2 connections)
- **Organization** (1 connections)
- **post** (1 connections)
- **Verify that the authenticated user owns the organization. Returns the…** (1 connections) — `app/api/explanations.py`
- **Generate a business-language explanation for a deterministic subject.** (1 connections) — `app/api/explanations.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (2 shared connections)
- [User](User.md) (2 shared connections)
- [ExplanationService](ExplanationService.md) (1 shared connections)
- [test_explanation_service.py](test_explanation_service.py.md) (1 shared connections)
- [Organization](Organization.md) (1 shared connections)

## Source Files

- `app/api/explanations.py`

## Audit Trail

- EXTRACTED: 12 (75%)
- INFERRED: 4 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*