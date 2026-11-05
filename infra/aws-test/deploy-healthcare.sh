#!/usr/bin/env bash
# deploy-healthcare.sh - Deploy ResilAI Healthcare Test Environment
#
# Deploys the CloudFormation stack and sets up AWS Config separately
# (Config recorder/delivery channel have a circular dependency in CFN).
#
# Usage: ./infra/aws-test/deploy-healthcare.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STACK_NAME="resilai-healthcare-test"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
TEMPLATE="${SCRIPT_DIR}/healthcare-env.yaml"

echo "=============================================="
echo "ResilAI Healthcare Test Environment Deployer"
echo "=============================================="
echo "Account  : ${ACCOUNT_ID}"
echo "Region   : ${REGION}"
echo "Stack    : ${STACK_NAME}"
echo ""

# ---------------------------------------------------
# Step 1: Deploy CloudFormation stack
# ---------------------------------------------------
echo "[1/3] Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file "${TEMPLATE}" \
  --stack-name "${STACK_NAME}" \
  --parameter-overrides AccountId="${ACCOUNT_ID}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "${REGION}" \
  --tags Owner=ResilAI Environment=ResilAI-Healthcare-Test Purpose=Telemetry-Validation \
  --no-fail-on-empty-changeset

echo "Stack deployed successfully."

# Get outputs
CONFIG_ROLE_ARN=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='ConfigRecorderRoleArn'].OutputValue" \
  --output text)

CONFIG_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='ConfigBucketName'].OutputValue" \
  --output text)

echo "Config Role : ${CONFIG_ROLE_ARN}"
echo "Config Bucket: ${CONFIG_BUCKET}"

# ---------------------------------------------------
# Step 2: Set up AWS Config (recorder + delivery channel)
# ---------------------------------------------------
echo ""
echo "[2/3] Setting up AWS Config..."

# Check if recorder already exists
EXISTING_RECORDER=$(aws configservice describe-configuration-recorders \
  --region "${REGION}" \
  --query 'ConfigurationRecorders[0].name' \
  --output text 2>/dev/null || echo "None")

if [ "${EXISTING_RECORDER}" = "None" ] || [ "${EXISTING_RECORDER}" = "" ]; then
  echo "Creating Config recorder..."
  aws configservice put-configuration-recorder \
    --configuration-recorder "{
      \"name\": \"resilai-test-recorder\",
      \"roleARN\": \"${CONFIG_ROLE_ARN}\",
      \"recordingGroup\": {
        \"allSupported\": true,
        \"includeGlobalResourceTypes\": true
      }
    }" \
    --region "${REGION}"
else
  echo "Config recorder already exists: ${EXISTING_RECORDER}"
fi

# Check if delivery channel exists
EXISTING_CHANNEL=$(aws configservice describe-delivery-channels \
  --region "${REGION}" \
  --query 'DeliveryChannels[0].name' \
  --output text 2>/dev/null || echo "None")

if [ "${EXISTING_CHANNEL}" = "None" ] || [ "${EXISTING_CHANNEL}" = "" ]; then
  echo "Creating delivery channel..."
  aws configservice put-delivery-channel \
    --delivery-channel "{
      \"name\": \"resilai-test-delivery\",
      \"s3BucketName\": \"${CONFIG_BUCKET}\",
      \"configSnapshotDeliveryProperties\": {
        \"deliveryFrequency\": \"TwentyFour_Hours\"
      }
    }" \
    --region "${REGION}"
else
  echo "Delivery channel already exists: ${EXISTING_CHANNEL}"
fi

# Start the recorder
echo "Starting Config recorder..."
aws configservice start-configuration-recorder \
  --configuration-recorder-name resilai-test-recorder \
  --region "${REGION}"

# Verify
RECORDING=$(aws configservice describe-configuration-recorder-status \
  --region "${REGION}" \
  --query 'ConfigurationRecordersStatus[0].recording' \
  --output text)

echo "Config recorder recording: ${RECORDING}"

# ---------------------------------------------------
# Step 3: Verify Security Hub standards
# ---------------------------------------------------
echo ""
echo "[3/3] Checking Security Hub standards..."
aws securityhub get-enabled-standards \
  --region "${REGION}" \
  --query 'StandardsSubscriptions[*].{Standard:StandardsArn,Status:StandardsStatus}' \
  --output table

echo ""
echo "=============================================="
echo "Healthcare Test Environment DEPLOYED"
echo "=============================================="
echo ""
echo "AWS Config is now recording all resources."
echo "Security Hub will start generating compliance findings"
echo "within 15-30 minutes as Config evaluates resources."
echo ""
echo "To check findings:"
echo "  aws securityhub get-findings --region ${REGION} --query 'Findings | length(@)'"
echo ""
echo "To tear down:"
echo "  ./infra/aws-test/teardown-healthcare.sh"
