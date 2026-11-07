#!/usr/bin/env bash
# Remove the demo organizations (instances, buckets, users) and, with --all,
# the base Security Hub/GuardDuty/Config stacks as well.
# Usage: AWS_PROFILE=resilai-demo ./infra/aws-demo-orgs/teardown.sh [--all]
set -uo pipefail
REGION="${AWS_REGION:-us-east-1}"
export AWS_DEFAULT_REGION="$REGION"
ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

empty_bucket() { aws s3 rm "s3://$1" --recursive >/dev/null 2>&1 || true; }

for stack in resilai-demo-healthcare resilai-demo-legal; do
  bucket="$(aws cloudformation describe-stacks --stack-name "$stack" --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" --output text 2>/dev/null || true)"
  [[ -n "$bucket" && "$bucket" != "None" ]] && empty_bucket "$bucket"
  user="$(aws cloudformation describe-stacks --stack-name "$stack" --query "Stacks[0].Outputs[?OutputKey=='DemoUserName'].OutputValue" --output text 2>/dev/null || true)"
  if [[ -n "$user" && "$user" != "None" ]]; then
    for k in $(aws iam list-access-keys --user-name "$user" --query 'AccessKeyMetadata[].AccessKeyId' --output text 2>/dev/null); do
      aws iam delete-access-key --user-name "$user" --access-key-id "$k" >/dev/null 2>&1 || true
    done
  fi
  echo "Deleting stack $stack"
  aws cloudformation delete-stack --stack-name "$stack"
done
for stack in resilai-demo-healthcare resilai-demo-legal; do
  aws cloudformation wait stack-delete-complete --stack-name "$stack" 2>/dev/null && echo "$stack deleted" || echo "WARN: $stack delete did not complete cleanly; check the console"
done

if [[ "${1:-}" == "--all" ]]; then
  "$SCRIPT_DIR/../aws-test/teardown-healthcare.sh" || true
  empty_bucket "resilai-test-${ACCOUNT_ID}-${REGION}"
  aws cloudformation delete-stack --stack-name resilai-connector-test
  aws cloudformation wait stack-delete-complete --stack-name resilai-connector-test && echo "base stack deleted"
fi
echo "Remaining ResilAI stacks:"; aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE DELETE_FAILED --query "StackSummaries[?starts_with(StackName,'resilai')].[StackName,StackStatus]" --output text
