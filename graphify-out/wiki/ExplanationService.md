# ExplanationService

> 24 nodes · cohesion 0.12

## Key Concepts

- **ExplanationService** (25 connections) — `app/services/explanation.py`
- **._extract_source_facts()** (8 connections) — `app/services/explanation.py`
- **.generate_explanation()** (7 connections) — `app/services/explanation.py`
- **._extract_readiness_facts()** (4 connections) — `app/services/explanation.py`
- **._extract_recovery_facts()** (4 connections) — `app/services/explanation.py`
- **._generate_with_gemini()** (4 connections) — `app/services/explanation.py`
- **._extract_connector_facts()** (3 connections) — `app/services/explanation.py`
- **._extract_evidence_facts()** (3 connections) — `app/services/explanation.py`
- **._extract_finding_facts()** (3 connections) — `app/services/explanation.py`
- **._generate_deterministic_fallback()** (3 connections) — `app/services/explanation.py`
- **._get_model_name()** (3 connections) — `app/services/explanation.py`
- **.__init__()** (2 connections) — `app/services/explanation.py`
- **Any** (1 connections)
- **Session** (1 connections)
- **Extract facts from a deterministic finding.** (1 connections) — `app/services/explanation.py`
- **Extract facts from the readiness/clinic engine.** (1 connections) — `app/services/explanation.py`
- **Extract facts about a connector (no secrets).** (1 connections) — `app/services/explanation.py`
- **Extract recovery/backup readiness facts.** (1 connections) — `app/services/explanation.py`
- **Extract facts about a specific evidence record.** (1 connections) — `app/services/explanation.py`
- **Use Gemini to transform source facts into a narrative. Returns None if Gemini…** (1 connections) — `app/services/explanation.py`
- **Generates business-language explanations from deterministic facts. Gemini is…** (1 connections) — `app/services/explanation.py`
- **Generate a structured explanation without LLM assistance.** (1 connections) — `app/services/explanation.py`
- **Generate a business-language explanation for a deterministic subject. Steps: 1.…** (1 connections) — `app/services/explanation.py`
- **Extract deterministic facts from the database for the given subject.** (1 connections) — `app/services/explanation.py`

## Relationships

- [app/db/database.py](app-db-database.py.md) (3 shared connections)
- [contracts.py](contracts.py.md) (3 shared connections)
- [TestExplanationServiceInit](TestExplanationServiceInit.md) (2 shared connections)
- [create_explanation](create_explanation.md) (1 shared connections)
- [TestExplanationTenantIsolation](TestExplanationTenantIsolation.md) (1 shared connections)
- [test_explanation_service.py](test_explanation_service.py.md) (1 shared connections)
- [main.py](main.py.md) (1 shared connections)
- [Organization](Organization.md) (1 shared connections)
- [Connector](Connector.md) (1 shared connections)
- [TelemetryEvent](TelemetryEvent.md) (1 shared connections)

## Source Files

- `app/services/explanation.py`

## Audit Trail

- EXTRACTED: 44 (92%)
- INFERRED: 4 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*