# DevOps State

Environments:
- Primary GCP Production: `airs-api` on Cloud Run (`https://api.resilai.org` / `gen-lang-client-0384513977`)
- Primary GCP Staging: `airs-api-staging` on Cloud Run (`https://airs-api-staging-227825933697.us-central1.run.app`)
- Standby AWS Production: `resilai-backend` on AWS App Runner (`https://backup-api.resilai.org` / `us-east-1`)
- Frontend Hosting: Firebase Hosting (`resilai.org`, `staging.resilai.org`, `resilai-marketing.web.app`)

Container Registries:
- GCP Artifact Registry: Primary Cloud Run deployments
- Amazon ECR: `resilai-backend` with immutable versioned image tagging (`release-timestamp-git-sha`)

Deployment & DR Infrastructure:
- Container Specification: `Dockerfile` (Multi-stage python:3.11-slim, non-root resilai user)
- GCP Cloud Run Deploy: `scripts/deploy_cloud_run.sh` / `scripts/deploy_cloud_run.ps1`
- AWS App Runner Spec: `aws/apprunner.yaml`
- AWS ECR Deployment Script: `aws/ecr_deploy.sh`
- Disaster Recovery Backup Sync: `aws/backup_dr_export.sh` (GCP / Local SQLite -> Encrypted S3 Standard-IA with checksums)
- Live AWS S3 DR Bucket: `s3://resilai-dr-backup-505467908065` (us-east-1, Block Public Access 4/4 true, default AES-256 SSE, versioning enabled, 30-day IA / 90-day expiration lifecycle)
- Live DR Snapshot: `scheduled-exports/2026/09/13/resilai_db_20260913_102317.db` (53,248 bytes, SHA-256 `a28df4e6b9cd3951cc57ba0b9ccd520110c4bda6a10917dccd48d6bf627f9efc`)
- DR Restore 9-Point Verification: `scripts/verify_dr_restore.py` (measured RTO 1.44s, restore 0.20ms, verification 2.12ms, RPO 12m, score 82.5% invariant)
- Standby Runtime & Health Verifier: `scripts/verify_aws_standby_runtime.py` (/health HTTP 200, 23.12ms, provider: aws, env: aws_standby, DB lock HTTP 503 DISASTER_RECOVERY_DATABASE_NOT_READY)
- DR Failover & Failback Simulator: `scripts/simulate_dr_failover_failback.py`
- Multi-Cloud Failure Simulation Suite: `tests/test_dr_failure_simulation.py`
- Multi-Cloud Operational Runbook: `aws/README_MULTICLOUD_RUNBOOK.md`
- GitHub Actions CI/CD: `.github/workflows/deploy.yml` (automated tests, governance gate, Cloud Run deploy, manual-gated `publish-aws-ecr` job)
- GitHub Actions Daily Backup Sync: `.github/workflows/daily-backup-sync.yml` (cron `0 4 * * *`, manual dispatch, syncs `staging` to `daily-sync` with audit step summary, strict branch protection blocking pushes to `main` and `demo-stable`)
- Disposable AWS Test Infrastructure (`infra/aws-test/`):
  - CloudFormation template: `infra/aws-test/template.yaml` (least privilege IAM connector role, GuardDuty, CloudTrail, S3 bucket with encryption disabled for TEST-002, overpermissive IAM role for TEST-003)
  - Lifecycle scripts: `infra/aws-test/deploy.sh`, `infra/aws-test/teardown.sh`
  - Active Resources: Stack `resilai-test-env`, Security Hub `arn:aws:securityhub:us-east-1:505467908065:hub/default`, S3 `resilai-test-505467908065-us-east-1`, Role `arn:aws:iam::505467908065:role/resilai-test-connector-role`
  - Current Status: `AWS_ENVIRONMENT_STATUS=DEPLOYED` (active for validation; teardown available via `./infra/aws-test/teardown.sh`)

Credit & Cost Optimization (Zero-Idle-Burn Enforcement):
- Testing & Development Principle: Scale-to-zero compute and strictly capped storage across all environments while testing and building.
- GCP Cloud Run CPU Throttling: Enforced `--cpu-throttling` and `--min-instances 0` on all Cloud Run services (`airs-api`, `airs-api-staging`) in `scripts/deploy_cloud_run.sh` and `scripts/deploy_cloud_run.ps1` to prevent continuous idle CPU billing.
- GCP Artifact Registry Lifecycle: Configured cleanup policies on `cloud-run-source-deploy` and `mcp-cloud-run-deployments` to keep only the 5 most recent versioned packages and delete unneeded packages older than 14 days, preventing ongoing storage fee accumulation.
- GCP Cloud Storage Lifecycle: Configured 14-day automated object expiration on ephemeral build and source buckets (`run-sources-*`, `*_cloudbuild`, `*-source-bucket`). Production report bucket (`airs-reports-*`) remains preserved.
- AWS Budget & Alerting: Created AWS Budget (`ResilAI-Cost-Safeguard`) on account `505467908065` capping monthly development spend at $50 USD with automated email notifications to `purvansh@resilai.org` at 50% ($25) and 80% ($40) thresholds.
- AWS Resource Idle Audit: Audited AWS account `505467908065` via `Resilai_admin` profile: 0 EC2, 0 RDS, 0 NAT Gateways, 0 active App Runner instances ($0.00/hr idle burn rate).
- AWS ECR Lifecycle: ECR deployment script configured with lifecycle policy keeping max 5 versioned images and purging untagged images after 24h.
- AWS S3 Storage Footprint: Single verified DR snapshot (~53 KB) with automated lifecycle transition to Standard-IA after 30 days and 90-day expiration.


