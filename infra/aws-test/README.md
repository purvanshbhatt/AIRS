# ResilAI AWS Connector Test Environment

This directory contains infrastructure-as-code to deploy a **disposable test environment** for validating the ResilAI AWS connector.

## Overview

The current ResilAI AWS connector is designed to exclusively consume findings from AWS Security Hub (`securityhub:GetFindings`, `securityhub:DescribeHub`). Direct API ingestion for services like EC2, S3, CloudTrail, or CloudWatch is **not** implemented, and asset discovery is mocked.

Therefore, this test environment only provisions resources designed to generate Security Hub findings.

## What is created?

- **IAM Role for Connector** (`resilai-test-connector-role`): Configured with least-privilege access, allowing only Security Hub read operations.
- **AWS Security Hub**: Enabled to aggregate findings.
- **Amazon GuardDuty**: Enabled to generate intelligent threat detections for Security Hub.
- **Unencrypted S3 Bucket**: Intentionally deployed without default encryption to trigger a Security Hub finding (simulating TEST-002).
- **Overpermissive IAM Role**: Intentionally granted `s3:*` to trigger a Security Hub finding (simulating TEST-003).
- **CloudTrail**: Configured to log to the unencrypted bucket, required for Security Hub CIS compliance checks.

## Prerequisites

- [AWS CLI](https://aws.amazon.com/cli/) installed and configured with valid credentials.
- IAM permissions sufficient to deploy CloudFormation stacks, create IAM roles, S3 buckets, CloudTrail trails, GuardDuty detectors, and enable Security Hub.

## Deployment

To deploy the test environment, run:

```bash
./deploy.sh
```

This script will:
1. Validate your AWS CLI and template.
2. Deploy the CloudFormation stack `resilai-test-env`.
3. Save the stack outputs to `.stack-outputs.json` (which will contain the Role ARN for the connector).

> **Note**: After deployment, it may take several hours for AWS Security Hub to run its compliance checks and generate findings for the intentionally vulnerable resources.

## Teardown

To cleanly remove all resources created by this environment, run:

```bash
./teardown.sh
```

This script will:
1. Empty the intentionally unencrypted S3 bucket (CloudFormation cannot delete non-empty buckets).
2. Delete the `resilai-test-env` stack.
3. Wait for complete deletion and confirm no billable resources remain.

## Cost Estimates

This environment uses minimal resources but is **not strictly free**:
- CloudTrail (first trail is free)
- GuardDuty (30-day free trial, then priced per GB analyzed)
- Security Hub (30-day free trial, then priced per check)
- S3 (minimal storage costs)

**Please tear down the environment when testing is complete.**

## What this does NOT test

This environment does **not** test:
- Direct log ingestion from CloudWatch or CloudTrail.
- Resource discovery via direct API calls (e.g., `ec2:DescribeInstances`).
- Multi-region or multi-account AWS Organizations setups.

## Safety Warnings

- **DO NOT** store sensitive data in the created S3 bucket, as it is deliberately misconfigured.
- **DO NOT** attach the overpermissive IAM role to actual workloads.
- The `.stack-outputs.json` file is meant to be gitignored to prevent accidental committing of infrastructure ARNs/metadata.
