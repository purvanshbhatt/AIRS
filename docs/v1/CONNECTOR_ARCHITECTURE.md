# ResilAI Connector Architecture

## Multi-SIEM Future-Proofing

ResilAI Sentinel connects to external SIEM, EDR, and security tools using a unified abstraction layer. To ensure strict determinism in our scoring engine and to prevent AI hallucinations during ingestion, all external telemetry MUST flow through the `BaseTelemetryConnector`.

### The `BaseTelemetryConnector` Interface

Located in `app/integrations/base.py`, this interface requires all SIEM modules to implement three core methods:

1. `health_check()`: Verifies connectivity and credentials without pulling data.
2. `search()`: Executes native searches using the SIEM's specific query language (e.g., SPL for Splunk).
3. `ingest()`: Performs the search, maps raw vendor alerts into the unified `SentinelTelemetryEvent` schema, and writes them to the database.

### Adding Future Connectors

When building new connectors (e.g., **Wazuh**, **AWS Security Hub**, **Microsoft Sentinel**), you must:

1. Inherit from `BaseTelemetryConnector`.
2. Implement native API clients (e.g., Wazuh API, Boto3 for AWS, Azure SDK).
3. In `ingest()`, map the vendor's alert fields to the `evidence_type` required by Sentinel.

By forcing all connectors to resolve to `SentinelTelemetryEvent` with a strict `evidence_type` string, the downstream **Evidence Engine**, **Digital Twin**, and **Deterministic Scoring** logic remains completely untouched. The scoring engine does not need to know if an alert came from Splunk or Wazuh.

