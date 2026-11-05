# Next Tasks

Priority 1
**Live AWS Telemetry Validation & Stack Deployment**
Status: Blocked on AWS Reauthentication (`AWS_ENVIRONMENT_STATUS=NOT_DEPLOYED`)
Owner: DevOps & Backend Security Team
Dependencies:
- Refresh `aws login` for `Resilai_admin` profile
- CloudFormation template ready at `infra/aws-test/template.yaml`
- Test suite passing locally (39/39 in `tests/aws_integration/`)

Next Actions:
- Reauthenticate AWS CLI and deploy `infra/aws-test/deploy.sh`.
- Run live integration test suite with `-m aws_integration`.
- Ingest live findings into `EvidenceLedger` and verify deterministic scoring in live tenant.
- Run `infra/aws-test/teardown.sh` to return to $0.00 idle cost.

Priority 2
**Connector Credential Encryption At Rest**
Status: Identified Gap (`CONNECTOR_CREDENTIAL_ENCRYPTION=GAP`)
Owner: Backend Security Team
Dependencies:
- `ConnectorManager._encrypt_credentials()` currently uses `json.dumps()`

Next Actions:
- Replace plaintext JSON storage with AES-256-GCM encryption using `SECRET_KEY` / AWS KMS / GCP Cloud KMS.
- Add unit tests validating ciphertext storage in `Connector.encrypted_credentials`.

Priority 3
**Self-Serve Acquisition & Onboarding Funnel Monitoring**
Status: In Progress
Owner: Growth & Customer Operations Team
Dependencies:
- Public Homepage Primary "Get Started" CTA live
- Google Login & Organization Onboarding active

Next Actions:
- Track visitor-to-login conversion rate (`/` → `/login` → Google OAuth).
- Monitor new organization creation and immediate connector linkage velocity.
- Surface in-app design-partner qualification triggers after users experience first material finding.

Priority 2
**Operational Monitoring & Customer Telemetry Integration**
Status: In Progress
Owner: Site Reliability / Customer Operations Team
Dependencies:
- Production Deployment Complete (Cloud Run `airs-api` + Firebase Hosting `https://resilai.org`)

Next Actions:
- Monitor live telemetry sync heartbeats for customer tenants.
- Track customer onboarding conversion and real-time audit ledger generation.
- Ongoing performance monitoring of Cloud Run auto-scaling and Firestore caching.

Priority 3
**Multi-Cloud Disaster Recovery & Production Evidence Validation**
Status: Complete (Phase 20 Verified — Real S3 & Container Evidence)
Owner: DevOps & Backend Infrastructure Team
Dependencies:
- Real AWS S3 bucket `resilai-dr-backup-505467908065` active with Block Public Access, AES-256 SSE, versioning, and lifecycle
- Snapshot sync, download, SHA-256 integrity, and 9-point restoration verified
- Standby container runtime, health probe (HTTP 200), and database lock (HTTP 503) verified
- Zero idle AWS compute maintained ($0.00/hr burn rate)

Next Actions:
- Schedule recurring automated DR export sync via Cloud Scheduler / EventBridge.
- Conduct simulated tabletop exercise with executive stakeholder reporting using empirical metrics.
- Prepare automated ECR smoke test upon CI release tagging.


