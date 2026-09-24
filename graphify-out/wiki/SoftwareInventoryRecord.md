# SoftwareInventoryRecord

> 21 nodes · cohesion 0.14

## Key Concepts

- **SoftwareInventoryRecord** (10 connections) — `app/services/discovery/direct_connectors.py`
- **DirectDiscoveryPoller** (9 connections) — `app/services/discovery/direct_connectors.py`
- **aws_ssm_poller.py** (6 connections) — `app/services/discovery/aws_ssm_poller.py`
- **direct_connectors.py** (6 connections) — `app/services/discovery/direct_connectors.py`
- **AWSConfigPoller** (4 connections) — `app/services/discovery/direct_connectors.py`
- **KubernetesInventoryPoller** (4 connections) — `app/services/discovery/direct_connectors.py`
- **MicrosoftGraphPoller** (4 connections) — `app/services/discovery/direct_connectors.py`
- **.__init__()** (3 connections) — `app/services/discovery/direct_connectors.py`
- **.poll()** (3 connections) — `app/services/discovery/direct_connectors.py`
- **.poll()** (2 connections) — `app/services/discovery/aws_ssm_poller.py`
- **.poll()** (2 connections) — `app/services/discovery/direct_connectors.py`
- **.poll()** (2 connections) — `app/services/discovery/direct_connectors.py`
- **.poll()** (2 connections) — `app/services/discovery/direct_connectors.py`
- **Any** (1 connections)
- **Abstract base class for direct technology discovery pollers.** (1 connections) — `app/services/discovery/direct_connectors.py`
- **Initialize the poller. Args: credentials: A dictionary containing secrets/keys.…** (1 connections) — `app/services/discovery/direct_connectors.py`
- **Poll the data source and return a list of discovered software inventory…** (1 connections) — `app/services/discovery/direct_connectors.py`
- **Poller for Microsoft Graph API device inventory.** (1 connections) — `app/services/discovery/direct_connectors.py`
- **Poller for AWS Config resource inventory.** (1 connections) — `app/services/discovery/direct_connectors.py`
- **Normalized software inventory record returned by pollers.** (1 connections) — `app/services/discovery/direct_connectors.py`
- **Poller for Kubernetes cluster workloads and images.** (1 connections) — `app/services/discovery/direct_connectors.py`

## Relationships

- [validate_delta.py](validate_delta.py.md) (5 shared connections)
- [app/db/database.py](app-db-database.py.md) (1 shared connections)
- [BaseModel](BaseModel.md) (1 shared connections)

## Source Files

- `app/services/discovery/aws_ssm_poller.py`
- `app/services/discovery/direct_connectors.py`

## Audit Trail

- EXTRACTED: 35 (97%)
- INFERRED: 1 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*