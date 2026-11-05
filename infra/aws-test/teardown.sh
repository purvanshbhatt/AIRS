#!/bin/bash
set -euo pipefail

# ResilAI AWS Test Environment Teardown Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STACK_NAME="resilai-test-env"
OUTPUT_FILE="${SCRIPT_DIR}/.stack-outputs.json"

echo "Tearing down ResilAI AWS Test Environment..."

# Safety check: AWS CLI installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed or not in PATH."
    exit 1
fi

# Check if stack exists
if ! aws cloudformation describe-stacks --stack-name "${STACK_NAME}" &> /dev/null; then
    echo "Stack ${STACK_NAME} does not exist. Nothing to tear down."
    exit 0
fi

# We need to empty the S3 bucket before the stack can be deleted
echo "Looking for S3 buckets to empty..."
BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name "${STACK_NAME}" --query "Stacks[0].Outputs[?OutputKey=='TestBucketName'].OutputValue" --output text || true)

if [ -n "${BUCKET_NAME}" ] && [ "${BUCKET_NAME}" != "None" ]; then
    echo "Emptying S3 bucket: ${BUCKET_NAME}..."
    # Empty bucket using AWS CLI (might take time if there are many objects)
    aws s3 rm "s3://${BUCKET_NAME}" --recursive || true
fi

echo "Deleting CloudFormation stack: ${STACK_NAME}..."
aws cloudformation delete-stack --stack-name "${STACK_NAME}"

echo "Waiting for stack deletion to complete..."
aws cloudformation wait stack-delete-complete --stack-name "${STACK_NAME}"

if [ -f "${OUTPUT_FILE}" ]; then
    rm -f "${OUTPUT_FILE}"
    echo "Removed local outputs file."
fi

echo "Teardown complete! All billable resources from this stack have been removed."
