# get_onboarding_status

> 15 nodes · cohesion 0.16

## Key Concepts

- **get_onboarding_status()** (13 connections) — `app/api/onboarding.py`
- **schemas/onboarding.py** (6 connections) — `app/schemas/onboarding.py`
- **EvidenceStatus** (5 connections) — `app/schemas/onboarding.py`
- **OnboardingResponse** (5 connections) — `app/schemas/onboarding.py`
- **OnboardingStatus** (5 connections) — `app/schemas/onboarding.py`
- **OnboardingStep** (5 connections) — `app/schemas/onboarding.py`
- **get** (1 connections)
- **Session** (1 connections)
- **User** (1 connections)
- **Get the onboarding status for an organization.** (1 connections) — `app/api/onboarding.py`
- **Pydantic schemas for the Onboarding Status API. Provides a stable contract for…** (1 connections) — `app/schemas/onboarding.py`
- **A single step in the onboarding flow.** (1 connections) — `app/schemas/onboarding.py`
- **Current evidence/connector status for the organization.** (1 connections) — `app/schemas/onboarding.py`
- **Overall onboarding progress.** (1 connections) — `app/schemas/onboarding.py`
- **Full onboarding response for GET /api/orgs/{org_id}/onboarding.** (1 connections) — `app/schemas/onboarding.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (7 shared connections)
- [BaseModel](BaseModel.md) (4 shared connections)
- [User](User.md) (1 shared connections)
- [Organization](Organization.md) (1 shared connections)
- [Connector](Connector.md) (1 shared connections)

## Source Files

- `app/api/onboarding.py`
- `app/schemas/onboarding.py`

## Audit Trail

- EXTRACTED: 23 (74%)
- INFERRED: 8 (26%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*