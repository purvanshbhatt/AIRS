#!/usr/bin/env bash
# Create the ResilAI connector test organization in the logged-in AWS account.
#
#   ./infra/aws-connector-test/deploy.sh
#
# What it does:
#   1. Turns on Security Hub and GuardDuty if they are off (and remembers
#      which ones it turned on, so teardown.sh can turn those off again).
#   2. Deploys the CloudFormation stack in test-org.yaml.
#   3. Asks GuardDuty for sample findings so Security Hub has something to show.
#
# The connector's access key goes straight into Secrets Manager. This script
# never prints it.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGION="${AWS_REGION:-us-east-1}"
STACK="${STACK_NAME:-resilai-connector-test-org}"
STATE_FILE="$SCRIPT_DIR/.deploy-state"
export AWS_DEFAULT_REGION="$REGION"

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
echo "Account $ACCOUNT_ID  region $REGION  stack $STACK"

touch "$STATE_FILE"
remember() { grep -qxF "$1" "$STATE_FILE" || echo "$1" >> "$STATE_FILE"; }

# 1a. Security Hub
if aws securityhub describe-hub >/dev/null 2>&1; then
  echo "Security Hub: already on"
else
  aws securityhub enable-security-hub --no-enable-default-standards >/dev/null
  remember "securityhub_enabled_by_script"
  echo "Security Hub: turned on"
fi

# 1b. GuardDuty
DETECTOR="$(aws guardduty list-detectors --query 'DetectorIds[0]' --output text 2>/dev/null || true)"
if [[ -z "$DETECTOR" || "$DETECTOR" == "None" ]]; then
  DETECTOR="$(aws guardduty create-detector --enable --query DetectorId --output text)"
  remember "guardduty_detector_created_by_script=$DETECTOR"
  echo "GuardDuty: turned on ($DETECTOR)"
else
  echo "GuardDuty: already on ($DETECTOR)"
fi

# 2. The test organization
aws cloudformation deploy \
  --template-file "$SCRIPT_DIR/test-org.yaml" \
  --stack-name "$STACK" \
  --capabilities CAPABILITY_NAMED_IAM \
  --tags Owner=ResilAI Environment=ResilAI-Connector-Test \
  --no-fail-on-empty-changeset

# 3. Sample findings (synthetic, safe; they flow into Security Hub)
aws guardduty create-sample-findings --detector-id "$DETECTOR" --finding-types \
  "UnauthorizedAccess:EC2/SSHBruteForce" \
  "Recon:EC2/PortProbeUnprotectedPort" \
  "CredentialAccess:IAMUser/AnomalousBehavior" \
  "Backdoor:EC2/C&CActivity.B!DNS" >/dev/null \
  && echo "GuardDuty sample findings requested"

echo
echo "Stack outputs:"
aws cloudformation describe-stacks --stack-name "$STACK" \
  --query 'Stacks[0].Outputs[].[OutputKey,OutputValue]' --output text
echo
echo "The access key is in Secrets Manager under the name shown above."
echo "Delete everything with: ./infra/aws-connector-test/teardown.sh"
