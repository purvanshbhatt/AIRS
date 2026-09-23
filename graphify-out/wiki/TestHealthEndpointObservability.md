# TestHealthEndpointObservability

> 8 nodes · cohesion 0.25

## Key Concepts

- **TestHealthEndpointObservability** (5 connections) — `tests/test_multicloud_portability.py`
- **.test_health_reports_aws_provider()** (2 connections) — `tests/test_multicloud_portability.py`
- **.test_health_reports_gcp_provider()** (2 connections) — `tests/test_multicloud_portability.py`
- **.test_health_response_exposes_no_secrets()** (2 connections) — `tests/test_multicloud_portability.py`
- **Health endpoint must never leak database URLs, tokens, or encryption keys.** (1 connections) — `tests/test_multicloud_portability.py`
- **Validate /health observability without credential leakage.** (1 connections) — `tests/test_multicloud_portability.py`
- **Under GCP configuration, health endpoint reports provider=gcp.** (1 connections) — `tests/test_multicloud_portability.py`
- **Under AWS configuration, health endpoint reports provider=aws.** (1 connections) — `tests/test_multicloud_portability.py`

## Relationships

- [main.py](main.py.md) (1 shared connections)

## Source Files

- `tests/test_multicloud_portability.py`

## Audit Trail

- EXTRACTED: 8 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*