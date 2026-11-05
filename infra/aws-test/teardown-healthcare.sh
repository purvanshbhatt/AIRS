#!/usr/bin/env bash
# teardown-healthcare.sh - Remove ResilAI Healthcare Test Environment
#
# Stops AWS Config, empties S3 buckets, and deletes the CloudFormation stack.
#
# Usage: ./infra/aws-test/teardown-healthcare.sh
set -euo pipefail

STACK_NAME="resilai-healthcare-test"
REGION="us-east-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "=============================================="
echo "ResilAI Healthcare Test Environment Teardown"
echo "=============================================="
echo "Account  : ${ACCOUNT_ID}"
echo "Stack    : ${STACK_NAME}"
echo ""

# Step 1: Stop and delete AWS Config
echo "[1/3] Removing AWS Config..."
aws configservice stop-configuration-recorder \
  --configuration-recorder-name resilai-test-recorder \
  --region "${REGION}" 2>/dev/null || echo "  Recorder not found (already deleted)"

aws configservice delete-delivery-channel \
  --delivery-channel-name resilai-test-delivery \
  --region "${REGION}" 2>/dev/null || echo "  Delivery channel not found"

aws configservice delete-configuration-recorder \
  --configuration-recorder-name resilai-test-recorder \
  --region "${REGION}" 2>/dev/null || echo "  Recorder not found"

echo "  Config resources removed."

# Step 2: Empty S3 buckets (CloudFormation can't delete non-empty buckets)
echo ""
echo "[2/3] Emptying S3 buckets..."
for BUCKET in \
  "resilai-config-${ACCOUNT_ID}" \
  "resilai-patient-records-${ACCOUNT_ID}" \
  "resilai-medical-images-${ACCOUNT_ID}" \
  "resilai-clinic-website-${ACCOUNT_ID}"; do
  if aws s3api head-bucket --bucket "${BUCKET}" 2>/dev/null; then
    echo "  Emptying ${BUCKET}..."
    aws s3 rm "s3://${BUCKET}" --recursive --region "${REGION}" 2>/dev/null || true
  else
    echo "  Bucket ${BUCKET} not found (already deleted)"
  fi
done

# Step 3: Delete CloudFormation stack
echo ""
echo "[3/3] Deleting CloudFormation stack..."
aws cloudformation delete-stack \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}"

echo "Waiting for stack deletion..."
aws cloudformation wait stack-delete-complete \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}"

echo ""
echo "=============================================="
echo "Healthcare Test Environment DELETED"
echo "=============================================="
