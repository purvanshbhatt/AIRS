# EvidenceKind

> 62 nodes · cohesion 0.06

## Key Concepts

- **EvidenceKind** (43 connections) — `app/services/clinic_engine/v2/schema.py`
- **RawEvent** (27 connections) — `app/services/clinic_engine/v2/schema.py`
- **EvidenceProvider** (15 connections) — `app/services/clinic_engine/v2/providers/base.py`
- **MicrosoftProvider** (14 connections) — `app/services/clinic_engine/v2/providers/microsoft_provider.py`
- **.extract()** (13 connections) — `app/services/clinic_engine/v2/providers/microsoft_provider.py`
- **WazuhProvider** (12 connections) — `app/services/clinic_engine/v2/providers/wazuh_provider.py`
- **providers/base.py** (11 connections) — `app/services/clinic_engine/v2/providers/base.py`
- **ProviderRegistry** (11 connections) — `app/services/clinic_engine/v2/providers/base.py`
- **providers/__init__.py** (9 connections) — `app/services/clinic_engine/v2/providers/__init__.py`
- **microsoft_provider.py** (9 connections) — `app/services/clinic_engine/v2/providers/microsoft_provider.py`
- **veeam_provider.py** (9 connections) — `app/services/clinic_engine/v2/providers/veeam_provider.py`
- **VeeamProvider** (9 connections) — `app/services/clinic_engine/v2/providers/veeam_provider.py`
- **wazuh_provider.py** (9 connections) — `app/services/clinic_engine/v2/providers/wazuh_provider.py`
- **.extract()** (9 connections) — `app/services/clinic_engine/v2/providers/wazuh_provider.py`
- **TestMicrosoftProvider** (9 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **TestWazuhProvider** (8 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **TestCertificationMatrix** (7 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- **.get_providers_for_evidence()** (5 connections) — `app/services/clinic_engine/v2/providers/base.py`
- **.extract()** (4 connections) — `app/services/clinic_engine/v2/providers/veeam_provider.py`
- **.required_evidence()** (3 connections) — `app/services/clinic_engine/v2/capability.py`
- **.extract()** (3 connections) — `app/services/clinic_engine/v2/providers/base.py`
- **.provides()** (3 connections) — `app/services/clinic_engine/v2/providers/microsoft_provider.py`
- **.provides()** (3 connections) — `app/services/clinic_engine/v2/providers/wazuh_provider.py`
- **str** (3 connections)
- **.test_providers_for_q1_unauthorized_access()** (3 connections) — `tests/services/clinic_engine/test_v2_engine.py`
- *... and 37 more nodes in this community*

## Relationships

- [schema.py](schema.py.md) (30 shared connections)
- [Evidence](Evidence.md) (19 shared connections)
- [NormalizedEvent](NormalizedEvent.md) (18 shared connections)
- [router.py](router.py.md) (5 shared connections)
- [MetricsEngine](MetricsEngine.md) (3 shared connections)
- [ConnectorHealth](ConnectorHealth.md) (2 shared connections)
- [TestProviderRegistry](TestProviderRegistry.md) (1 shared connections)
- [BaseModel](BaseModel.md) (1 shared connections)

## Source Files

- `app/services/clinic_engine/v2/capabilities/device_compromise.py`
- `app/services/clinic_engine/v2/capabilities/recovery_readiness.py`
- `app/services/clinic_engine/v2/capabilities/unauthorized_access.py`
- `app/services/clinic_engine/v2/capability.py`
- `app/services/clinic_engine/v2/providers/__init__.py`
- `app/services/clinic_engine/v2/providers/base.py`
- `app/services/clinic_engine/v2/providers/microsoft_provider.py`
- `app/services/clinic_engine/v2/providers/veeam_provider.py`
- `app/services/clinic_engine/v2/providers/wazuh_provider.py`
- `app/services/clinic_engine/v2/schema.py`
- `tests/services/clinic_engine/test_v2_engine.py`

## Audit Trail

- EXTRACTED: 165 (83%)
- INFERRED: 34 (17%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*