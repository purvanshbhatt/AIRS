# get_firestore_client

> 65 nodes · cohesion 0.05

## Key Concepts

- **get_firestore_client()** (23 connections) — `app/db/firestore.py`
- **is_firestore_available()** (20 connections) — `app/db/firestore.py`
- **FirestoreUnavailableError** (16 connections) — `app/db/firestore.py`
- **Any** (16 connections)
- **sync_orgs_from_firestore()** (14 connections) — `app/db/firestore.py`
- **require_firestore()** (13 connections) — `app/db/firestore.py`
- **firestore_get_all_orgs()** (9 connections) — `app/db/firestore.py`
- **firestore_save_finding_tracking()** (9 connections) — `app/db/firestore.py`
- **.get()** (9 connections) — `app/services/organization.py`
- **firestore_get_finding_tracking_map()** (8 connections) — `app/db/firestore.py`
- **firestore_get_org()** (8 connections) — `app/db/firestore.py`
- **firestore_set_assessment_lifecycle()** (8 connections) — `app/db/firestore.py`
- **firestore_upsert_remediation_ledger()** (8 connections) — `app/db/firestore.py`
- **firestore_delete_org()** (7 connections) — `app/db/firestore.py`
- **firestore_get_all_assessments()** (7 connections) — `app/db/firestore.py`
- **firestore_get_all_wazuh_configs()** (7 connections) — `app/db/firestore.py`
- **.get_all()** (7 connections) — `app/services/organization.py`
- **.update()** (7 connections) — `app/services/organization.py`
- **_decrypt_org_doc()** (6 connections) — `app/db/firestore.py`
- **.create()** (6 connections) — `app/services/organization.py`
- **determine_regulatory_profile()** (5 connections) — `app/core/regulatory.py`
- **firestore_delete_wazuh_config()** (5 connections) — `app/db/firestore.py`
- **_org_to_doc()** (5 connections) — `app/db/firestore.py`
- **sync_wazuh_configs_from_firestore()** (5 connections) — `app/db/firestore.py`
- **_sync_firestore_on_startup()** (5 connections) — `app/main.py`
- *... and 40 more nodes in this community*

## Relationships

- [Organization](Organization.md) (35 shared connections)
- [app/db/database.py](app-db-database.py.md) (23 shared connections)
- [User](User.md) (10 shared connections)
- [WazuhConfig](WazuhConfig.md) (9 shared connections)
- [EncryptionService](EncryptionService.md) (7 shared connections)
- [test_production_org_lifecycle.py](test_production_org_lifecycle.py.md) (5 shared connections)
- [_make_org](_make_org.md) (4 shared connections)
- [api/integrations.py](api-integrations.py.md) (3 shared connections)
- [ingest_intelligence_packet](ingest_intelligence_packet.md) (2 shared connections)
- [main.py](main.py.md) (2 shared connections)
- [SessionLocal](SessionLocal.md) (1 shared connections)

## Source Files

- `app/core/regulatory.py`
- `app/db/firestore.py`
- `app/main.py`
- `app/services/organization.py`
- `tests/test_production_org_lifecycle.py`

## Audit Trail

- EXTRACTED: 197 (99%)
- INFERRED: 2 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*