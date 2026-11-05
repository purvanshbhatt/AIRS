# EncryptionService

> 68 nodes · cohesion 0.05

## Key Concepts

- **EncryptionService** (24 connections) — `app/core/security/encryption.py`
- **get_encryption_service()** (14 connections) — `app/core/security/encryption.py`
- **test_firestore_encryption.py** (13 connections) — `tests/test_firestore_encryption.py`
- **generate_encryption_key()** (12 connections) — `app/core/security/encryption.py`
- **encryption.py** (10 connections) — `app/core/security/encryption.py`
- **_assessment_to_doc()** (10 connections) — `app/db/firestore.py`
- **_encrypt_doc_fields()** (9 connections) — `app/db/firestore.py`
- **test_encryption_validation.py** (9 connections) — `tests/test_encryption_validation.py`
- **_make_key()** (9 connections) — `tests/test_encryption_validation.py`
- **connector_encryption.py** (7 connections) — `app/core/security/connector_encryption.py`
- **_decrypt_assessment_doc()** (7 connections) — `app/db/firestore.py`
- **TestEncryptionBasics** (7 connections) — `tests/test_encryption_validation.py`
- **_get_connector_encryption_service()** (6 connections) — `app/core/security/connector_encryption.py`
- **TestConnectorEncryptionIsolation** (5 connections) — `tests/test_encryption_validation.py`
- **test_assessment_firestore_payload_round_trips_after_decrypt()** (5 connections) — `tests/test_firestore_encryption.py`
- **.decrypt_fields()** (4 connections) — `app/core/security/encryption.py`
- **.encrypt_fields()** (4 connections) — `app/core/security/encryption.py`
- **security/__init__.py** (4 connections) — `app/core/security/__init__.py`
- **.test_narrative_layer_never_receives_secrets()** (4 connections) — `tests/test_encryption_validation.py`
- **test_assessment_firestore_payload_is_encrypted_when_secret_present()** (4 connections) — `tests/test_firestore_encryption.py`
- **test_finding_tracking_encryption_round_trip()** (4 connections) — `tests/test_firestore_encryption.py`
- **decrypt_value()** (3 connections) — `app/core/security/connector_encryption.py`
- **encrypt_value()** (3 connections) — `app/core/security/connector_encryption.py`
- **_load_key_from_secret_manager()** (3 connections) — `app/core/security/connector_encryption.py`
- **._decrypt_blob()** (3 connections) — `app/core/security/encryption.py`
- *... and 43 more nodes in this community*

## Relationships

- [WazuhConfig](WazuhConfig.md) (13 shared connections)
- [Organization](Organization.md) (8 shared connections)
- [get_firestore_client](get_firestore_client.md) (7 shared connections)
- [app/db/database.py](app-db-database.py.md) (2 shared connections)

## Source Files

- `app/core/security/__init__.py`
- `app/core/security/connector_encryption.py`
- `app/core/security/encryption.py`
- `app/db/firestore.py`
- `app/db/types.py`
- `tests/test_encryption_validation.py`
- `tests/test_firestore_encryption.py`

## Audit Trail

- EXTRACTED: 139 (97%)
- INFERRED: 5 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*