# TestMultiCloudHealthCheck

> 12 nodes · cohesion 0.17

## Key Concepts

- **TestMultiCloudHealthCheck** (7 connections) — `tests/test_health_multi_cloud.py`
- **.test_invalid_provider_rejected()** (3 connections) — `tests/test_health_multi_cloud.py`
- **.test_health_aws_standby()** (2 connections) — `tests/test_health_multi_cloud.py`
- **.test_health_gcp_production()** (2 connections) — `tests/test_health_multi_cloud.py`
- **.test_health_local()** (2 connections) — `tests/test_health_multi_cloud.py`
- **.test_zero_credential_leakage()** (2 connections) — `tests/test_health_multi_cloud.py`
- **Test /health endpoint across multi-cloud configurations.** (1 connections) — `tests/test_health_multi_cloud.py`
- **Under GCP configuration, health check returns provider=gcp,…** (1 connections) — `tests/test_health_multi_cloud.py`
- **Under AWS Standby configuration, health check returns provider=aws,…** (1 connections) — `tests/test_health_multi_cloud.py`
- **Under local configuration, health check returns provider=local or gcp,…** (1 connections) — `tests/test_health_multi_cloud.py`
- **Settings validation rejects unsupported cloud providers.** (1 connections) — `tests/test_health_multi_cloud.py`
- **Ensure no secrets, passwords, or internal credentials appear in /health…** (1 connections) — `tests/test_health_multi_cloud.py`

## Relationships

- [main.py](main.py.md) (1 shared connections)
- [Settings](Settings.md) (1 shared connections)

## Source Files

- `tests/test_health_multi_cloud.py`

## Audit Trail

- EXTRACTED: 13 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*