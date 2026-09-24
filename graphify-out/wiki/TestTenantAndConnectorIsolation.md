# TestTenantAndConnectorIsolation

> 6 nodes · cohesion 0.33

## Key Concepts

- **TestTenantAndConnectorIsolation** (5 connections) — `tests/test_multicloud_portability.py`
- **.test_aws_connector_is_registered()** (3 connections) — `tests/test_multicloud_portability.py`
- **.test_real_org_receives_no_demo_telemetry_under_aws()** (3 connections) — `tests/test_multicloud_portability.py`
- **Verify tenant isolation and connector scoping.** (1 connections) — `tests/test_multicloud_portability.py`
- **AWSSecurityHubConnector is registered in the connector registry.** (1 connections) — `tests/test_multicloud_portability.py`
- **Real organizations never receive synthetic demo telemetry, even in AWS mode.** (1 connections) — `tests/test_multicloud_portability.py`

## Relationships

- [Organization](Organization.md) (2 shared connections)
- [main.py](main.py.md) (1 shared connections)
- [Connector](Connector.md) (1 shared connections)

## Source Files

- `tests/test_multicloud_portability.py`

## Audit Trail

- EXTRACTED: 8 (89%)
- INFERRED: 1 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*