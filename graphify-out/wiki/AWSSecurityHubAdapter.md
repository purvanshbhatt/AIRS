# AWSSecurityHubAdapter

> 15 nodes · cohesion 0.13

## Key Concepts

- **AWSSecurityHubAdapter** (14 connections) — `app/services/evidence/adapters/aws_security_hub.py`
- **.fetch_evidence()** (4 connections) — `app/services/evidence/adapters/aws_security_hub.py`
- **.normalize()** (4 connections) — `app/services/evidence/adapters/aws_security_hub.py`
- **.health()** (3 connections) — `app/services/evidence/adapters/aws_security_hub.py`
- **.bind_connector()** (2 connections) — `app/services/evidence/adapters/aws_security_hub.py`
- **datetime** (2 connections)
- **.connector_name()** (1 connections) — `app/services/evidence/adapters/aws_security_hub.py`
- **.__init__()** (1 connections) — `app/services/evidence/adapters/aws_security_hub.py`
- **Any** (1 connections)
- **EvidenceAdapter** (1 connections)
- **EvidenceAdapter implementation for AWS Security Hub. The adapter delegates to a…** (1 connections) — `app/services/evidence/adapters/aws_security_hub.py`
- **Bind the AWSSecurityHubConnector that owns this adapter's telemetry.** (1 connections) — `app/services/evidence/adapters/aws_security_hub.py`
- **Fetch all evidence checks from AWS Security Hub. This is a thin shim —…** (1 connections) — `app/services/evidence/adapters/aws_security_hub.py`
- **AWS Security Hub payloads have already been normalised by the…** (1 connections) — `app/services/evidence/adapters/aws_security_hub.py`
- **Report live adapter health via the bound AWSSecurityHubConnector. Returns a…** (1 connections) — `app/services/evidence/adapters/aws_security_hub.py`

## Relationships

- [EvidenceAdapter](EvidenceAdapter.md) (3 shared connections)
- [EvidenceRecord](EvidenceRecord.md) (3 shared connections)
- [AdapterHealth](AdapterHealth.md) (2 shared connections)
- [ConnectorManager](ConnectorManager.md) (1 shared connections)
- [Connector](Connector.md) (1 shared connections)

## Source Files

- `app/services/evidence/adapters/aws_security_hub.py`

## Audit Trail

- EXTRACTED: 21 (88%)
- INFERRED: 3 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*