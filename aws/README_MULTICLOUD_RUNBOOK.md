# ResilAI Multi-Cloud Architecture & Disaster Recovery Runbook
## GCP Primary + AWS Standby / Telemetry Infrastructure

---

## 1. Executive Summary & Core Rules

ResilAI employs a **GCP-Primary / AWS-Standby** multi-cloud resilience architecture:

- **Primary**: Google Cloud Run (`airs-api`), Firebase Hosting, Firestore persistence, and Gemini narrative intelligence.
- **Standby & Telemetry Infrastructure**: AWS App Runner (`resilai-backend`), Amazon ECR, Amazon S3 for DR snapshots, and AWS Security Hub for posture telemetry.
- **Cost Allocation**: AWS Activate credits offset standby compute, container registry storage, telemetry ingest infrastructure, and off-site backup archives.

### Non-Negotiable Invariants
1. **LLMs never calculate readiness scores.** Scoring is 100% deterministic and mathematical.
2. **One authoritative scoring engine.** AWS standby does NOT implement a second scoring algorithm.
3. **Evidence over attestation.** Telemetry from Splunk, Wazuh, or AWS Security Hub is normalized before evaluation.
4. **Tenant isolation.** Every connector, telemetry event, and evidence ledger is strictly organization-scoped.
5. **No split-brain writes.** AWS standby runs stateless in cold/warm standby; no uncoordinated dual-primary database replication is allowed.

---

## 2. Infrastructure Comparison

| Dimension | Primary (GCP) | Standby / DR (AWS) |
| :--- | :--- | :--- |
| **Compute** | Cloud Run (`airs-api`) | App Runner (`resilai-backend`) |
| **Container Registry** | Google Artifact Registry | Amazon ECR (`resilai-backend`) |
| **Persistence (Primary)** | Firestore / Cloud SQL | SQLite Cache / DR Restore |
| **Frontend** | Firebase Hosting (`resilai.org`) | Standby static bundle (optional) |
| **Disaster Recovery** | Continuous Snapshots | Encrypted S3 (`resilai-disaster-recovery-backups`) |
| **Intelligence** | Gemini 3 Flash (Vertex ADC) | Gemini 3 Flash (API key fallback) |
| **Telemetry Ingestion** | Splunk MCP, Wazuh, Security Hub | Security Hub, CloudTrail / EventBridge buffer |

---

## 3. Database Safety Strategy (Option B)

### Why Option B?
- Direct active-active cross-cloud multi-master replication between Cloud SQL/Firestore and AWS RDS creates network partition hazards, latency penalties, and split-brain risks.
- **Option B Implementation**:
  - The AWS App Runner container starts in application-ready standby mode (`CLOUD_PROVIDER=aws`, `AWS_STANDBY=true`).
  - Ephemeral SQLite is initialized for stateless execution.
  - Scheduled backups of compliance ledgers and database exports sync asynchronously to an encrypted AWS S3 bucket (`aws/backup_dr_export.sh`).
  - **RPO (Recovery Point Objective)**: 1 to 4 hours (snapshot interval).
  - **RTO (Recovery Time Objective)**: < 15 minutes (App Runner instance warmup + database attachment).

---

## 4. Operational Characteristics of AWS App Runner

- **Warmup Latency**: App Runner maintains provisioned memory even when paused, providing rapid scale-up (sub-second to few seconds), unlike cold-start from zero.
- **Automatic Health Checking**: Probes `GET /health` every 10 seconds.
- **Automatic TLS**: Built-in certificate management for custom domains (`backup-api.resilai.org`).
- **Configuration Spec**: Defined in [`aws/apprunner.yaml`](apprunner.yaml).

---

## 5. Failover Architecture & Runbook

```
                  ┌──────────────────────────────┐
                  │ DNS (Route 53 / Cloudflare)  │
                  └──────────────┬───────────────┘
                                 │
           ┌─────────────────────┴─────────────────────┐
           │ Health Probe: GET /health                 │
           ▼ (Primary Healthy)                         ▼ (Failover Declared)
┌───────────────────────────┐               ┌───────────────────────────┐
│     api.resilai.org       │               │   backup-api.resilai.org  │
│      GCP Cloud Run        │               │       AWS App Runner      │
│     (Provider: gcp)       │               │      (Provider: aws)      │
└───────────────────────────┘               └───────────────────────────┘
```

### Manual Failover Gate (Pre-requisites before redirecting traffic)
1. Verify GCP outage via Google Cloud Status / internal alerts.
2. Check AWS Standby health:
   ```bash
   curl -s -f https://backup-api.resilai.org/health
   # Expected response contains: "provider": "aws", "status": "ok"
   ```
3. If database restoration is required, execute the restore playbook using the latest S3 backup from `s3://resilai-disaster-recovery-backups/scheduled-exports/`.
4. Update DNS CNAME or Route 53 failover policy routing traffic to `backup-api.resilai.org`.
5. Invalidate client auth cache if Firebase Auth emulator or cross-provider token exchange is needed.

---

## 6. Credit Optimization (AWS Activate)

Target allocation of AWS credits:
1. **ECR Storage & Image Scanning**: Retaining immutable, vulnerability-scanned backend images.
2. **App Runner Provisioned Capacity**: Running low-overhead standby container (1 vCPU, 2 GB RAM).
3. **Amazon S3 Standard-IA**: Archival of compressed, encrypted compliance and database backups.
4. **AWS Security Hub & GuardDuty**: Generating live cloud security posture telemetry to feed ResilAI's verification engine via `AWSSecurityHubConnector`.

---

## 7. What Has NOT Been Implemented

To ensure architectural honesty, the following have deliberately **NOT** been activated:
- **Automatic unassisted DNS failover**: Automatic DNS flapping could inadvertently route customers to a standby database that lacks the very latest live writes. Failover remains gated.
- **Active-active bidirectional database replication**: Prevented by design to eliminate split-brain hazards.
- **Multi-region AWS redundancy**: Focus is GCP-primary with AWS single-region standby (`us-east-1`).
