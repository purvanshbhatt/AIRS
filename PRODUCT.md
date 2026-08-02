# ResilAI Readiness OS Product Specification

## Core Vision
**Can this clinic safely open today?**
This is the single most important question ResilAI answers for healthcare practices and small-to-medium businesses (SMBs). Instead of presenting security alerts, vulnerabilities, or complex dashboards, ResilAI synthesizes everything into a singular, immutable daily readiness contract. 

## Target User
The target user is the non-technical Clinic Owner or Practice Manager. They are busy treating patients and running a business. They do not have time to parse security logs. They need a simple, actionable summary of their clinic's readiness and clear steps for remediation.

## Design Philosophy

### 1. The DailyReadinessReport is the Product
Everything in the system (every connector, rule, action, and trust signal) exists solely to populate the `DailyReadinessReport`. If a feature doesn't directly enhance the report's accuracy, actionability, or trust, it does not belong in the product.

### 2. AI as an Explainer, Never a Decider
Decisions about risk and readiness must be deterministic, transparent, and auditable. AI is used strictly to translate complex technical jargon into natural, clear customer language (e.g., explaining *why* a missing backup matters) but never to decide *if* something is a risk.

### 3. "Unknown" is a First-Class Trust Signal
If a connector goes offline, we do not assume safety. We degrade to "Unknown" and explicitly reduce our confidence score. Telling a customer "We don't know if your backups ran because the appliance is offline" builds more trust than a false "Safe".

## Architecture

The system follows a pipeline architecture, completely decoupled from the frontend:

1. **Connectors (Data Ingestion)**: Pulls raw telemetry from Microsoft 365, Wazuh, Veeam, etc.
2. **Providers (Extraction)**: Extracts uniform `Evidence` from raw telemetry.
3. **Evaluation Engine**: Maps evidence to standardized `ClinicMoments` (e.g., "Former employee active", "Backup failed").
4. **Risk Engine**: Resolves the moment against the clinic's context (e.g., "Does this employee have EMR access?").
5. **Action Engine**: Generates safe, reversible `ActionCards` with one-click remediation instructions.
6. **Trust Engine**: Calculates confidence based on data age, connector health, and evidence source.
7. **Coverage Engine**: Determines what percentage of the clinic's attack surface is actively monitored.
8. **Metrics Engine**: Calculates automated ROI (problems prevented, accounts protected) to justify renewals.
9. **Readiness Engine (The Aggregator)**: Synthesizes all layers into the `DailyReadinessReport`.

## API Surface
The core API endpoint is `GET /readiness/{org_id}`, which returns the `DailyReadinessReport` in a frozen, schema-validated contract. The frontend consumes this payload exactly as-is to render the dashboard.

## Next Steps
Future iterations will focus on expanding the frontend product experience, building one-click fixes for complex remediations, and deepening the library of deterministic rules for new capabilities.
