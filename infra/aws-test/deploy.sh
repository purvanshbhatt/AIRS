#!/bin/bash
set -euo pipefail

# ResilAI AWS Test Environment Deployment Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STACK_NAME="resilai-test-env"
OUTPUT_FILE="${SCRIPT_DIR}/.stack-outputs.json"

echo "Deploying ResilAI AWS Test Environment..."

# Safety check: AWS CLI installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed or not in PATH."
    exit 1
fi

# Safety check: AWS credentials configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS credentials are not configured or are invalid."
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "Validating CloudFormation template..."
aws cloudformation validate-template --template-body "file://${SCRIPT_DIR}/template.yaml" > /dev/null

echo "Deploying CloudFormation stack: ${STACK_NAME}..."
aws cloudformation deploy \
    --template-file "${SCRIPT_DIR}/template.yaml" \
    --stack-name "${STACK_NAME}" \
    --parameter-overrides TrustedAccountId="${ACCOUNT_ID}" \
    --capabilities CAPABILITY_NAMED_IAM \
    --tags Environment=ResilAI-Test Purpose=Telemetry-Validation Owner=ResilAI

echo "Retrieving stack outputs..."
aws cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --query 'Stacks[0].Outputs' \
    --output json > "${OUTPUT_FILE}"

echo "Deployment complete! Outputs saved to ${OUTPUT_FILE}."
echo "Connector Role ARN:"
cat "${OUTPUT_FILE}" | grep ConnectorRoleArn -A 3 | grep OutputValue | cut -d'"' -f4 || true

echo ""
echo "Note: It may take some time for Security Hub findings to be generated."
