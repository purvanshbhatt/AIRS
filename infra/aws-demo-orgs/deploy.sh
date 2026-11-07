#!/usr/bin/env bash
# Deploy the two ResilAI demo organizations (healthcare clinic + legal practice)
# on top of the base Security Hub / GuardDuty / Config environment, then seed
# GuardDuty sample findings so the capture has "attack" telemetry too.
#
# Usage: AWS_PROFILE=resilai-demo ./infra/aws-demo-orgs/deploy.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
export AWS_DEFAULT_REGION="$REGION"

echo "Account $ACCOUNT_ID  region $REGION"

# 1. Base services: Security Hub + GuardDuty + CloudTrail + connector role
aws cloudformation deploy \
  --template-file "$SCRIPT_DIR/../aws-test/template.yaml" \
  --stack-name resilai-connector-test \
  --parameter-overrides TrustedAccountId="$ACCOUNT_ID" \
  --capabilities CAPABILITY_NAMED_IAM --region "$REGION" \
  --no-fail-on-empty-changeset

# Security Hub standards: FSBP + CIS 1.4 (generate control findings for the misconfigs)
for std in \
  "arn:aws:securityhub:${REGION}::standards/aws-foundational-security-best-practices/v/1.0.0" \
  "arn:aws:securityhub:${REGION}::standards/cis-aws-foundations-benchmark/v/1.4.0"; do
  aws securityhub batch-enable-standards --standards-subscription-requests "StandardsArn=$std" --region "$REGION" >/dev/null 2>&1 || true
done

# 2. Config recorder (required for most FSBP controls) — reuse the healthcare base stack
"$SCRIPT_DIR/../aws-test/deploy-healthcare.sh" || echo "WARN: healthcare base stack step reported an error; continuing"

# 3. Two demo organizations
aws cloudformation deploy \
  --template-file "$SCRIPT_DIR/demo-org.yaml" \
  --stack-name resilai-demo-healthcare \
  --parameter-overrides Industry=healthcare OrgSlug=metro-health VpcCidr=10.20.0.0/16 \
  --capabilities CAPABILITY_NAMED_IAM --region "$REGION" \
  --tags Owner=ResilAI Environment=ResilAI-Demo-Org Industry=healthcare \
  --no-fail-on-empty-changeset
aws cloudformation deploy \
  --template-file "$SCRIPT_DIR/demo-org.yaml" \
  --stack-name resilai-demo-legal \
  --parameter-overrides Industry=legal OrgSlug=northstar-cole VpcCidr=10.30.0.0/16 \
  --capabilities CAPABILITY_NAMED_IAM --region "$REGION" \
  --tags Owner=ResilAI Environment=ResilAI-Demo-Org Industry=legal \
  --no-fail-on-empty-changeset

# 4. GuardDuty sample findings (safe, synthetic, flow into Security Hub)
DETECTOR="$(aws guardduty list-detectors --region "$REGION" --query 'DetectorIds[0]' --output text)"
if [[ -n "$DETECTOR" && "$DETECTOR" != "None" ]]; then
  aws guardduty create-sample-findings --detector-id "$DETECTOR" --region "$REGION" --finding-types \
    "UnauthorizedAccess:EC2/SSHBruteForce" \
    "Recon:EC2/PortProbeUnprotectedPort" \
    "CredentialAccess:IAMUser/AnomalousBehavior" \
    "Exfiltration:S3/AnomalousBehavior" \
    "Impact:EC2/WinRMBruteForce" \
    "Backdoor:EC2/C&CActivity.B!DNS" \
    "UnauthorizedAccess:IAMUser/ConsoleLoginSuccess.B" >/dev/null
  echo "GuardDuty sample findings created on detector $DETECTOR"
fi

echo
echo "Deployed. Security Hub control findings for the misconfigured resources typically appear within 15-60 minutes."
echo "Capture with: AWS_PROFILE=... python3 scripts/capture_aws_demo_telemetry.py"
echo "Tear down with: AWS_PROFILE=... ./infra/aws-demo-orgs/teardown.sh"
