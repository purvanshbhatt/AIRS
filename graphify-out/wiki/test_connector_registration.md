# test_connector_registration

> 6 nodes · cohesion 0.33

## Key Concepts

- **test_connector_registration()** (6 connections) — `tests/test_microsoft_connector.py`
- **.get_connector_class()** (5 connections) — `app/connectors/registry.py`
- **.list_available_connectors()** (4 connections) — `app/connectors/registry.py`
- **Look up a connector class by type string. Raises ``KeyError`` if the type is…** (1 connections) — `app/connectors/registry.py`
- **Return sorted list of registered connector type identifiers.** (1 connections) — `app/connectors/registry.py`
- **Verify that MicrosoftConnector is registered with ConnectorRegistry.** (1 connections) — `tests/test_microsoft_connector.py`

## Relationships

- [ConnectorHealth](ConnectorHealth.md) (4 shared connections)
- [Connector](Connector.md) (2 shared connections)
- [test_microsoft_connector.py](test_microsoft_connector.py.md) (1 shared connections)
- [NormalizedEvent](NormalizedEvent.md) (1 shared connections)

## Source Files

- `app/connectors/registry.py`
- `tests/test_microsoft_connector.py`

## Audit Trail

- EXTRACTED: 11 (85%)
- INFERRED: 2 (15%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*