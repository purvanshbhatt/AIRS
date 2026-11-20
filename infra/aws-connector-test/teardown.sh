#!/usr/bin/env bash
# Delete the ResilAI connector test organization.
#
#   ./infra/aws-connector-test/teardown.sh
#
# Deletes the CloudFormation stack (instances, VPN, network, IAM user, access
# key, secret) and turns off Security Hub / GuardDuty only if deploy.sh was
# the one that turned them on. Then lists anything tagged for this test that
# is still there.
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGION="${AWS_REGION:-us-east-1}"
STACK="${STACK_NAME:-resilai-connector-test-org}"
STATE_FILE="$SCRIPT_DIR/.deploy-state"
export AWS_DEFAULT_REGION="$REGION"

ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)" || exit 1
echo "Account $ACCOUNT_ID  region $REGION  stack $STACK"

echo "Deleting stack $STACK"
aws cloudformation delete-stack --stack-name "$STACK"
if aws cloudformation wait stack-delete-complete --stack-name "$STACK"; then
  echo "Stack deleted"
else
  echo "WARN: stack delete did not finish cleanly. Reasons:"
  aws cloudformation describe-stack-events --stack-name "$STACK" \
    --query "StackEvents[?ResourceStatus=='DELETE_FAILED'].[LogicalResourceId,ResourceStatusReason]" --output text
fi

if [[ -f "$STATE_FILE" ]]; then
  if grep -q '^guardduty_detector_created_by_script=' "$STATE_FILE"; then
    DETECTOR="$(grep '^guardduty_detector_created_by_script=' "$STATE_FILE" | tail -1 | cut -d= -f2)"
    aws guardduty delete-detector --detector-id "$DETECTOR" && echo "GuardDuty turned off ($DETECTOR)"
  fi
  if grep -qx 'securityhub_enabled_by_script' "$STATE_FILE"; then
    aws securityhub disable-security-hub && echo "Security Hub turned off"
  fi
  rm -f "$STATE_FILE"
fi

echo
echo "Left over (should be empty):"
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE ROLLBACK_COMPLETE DELETE_FAILED \
  --query "StackSummaries[?StackName=='$STACK'].[StackName,StackStatus]" --output text
aws ec2 describe-instances \
  --filters "Name=tag:Environment,Values=ResilAI-Connector-Test" "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query 'Reservations[].Instances[].[InstanceId,State.Name]' --output text
aws ec2 describe-vpn-connections \
  --filters "Name=tag:Environment,Values=ResilAI-Connector-Test" \
  --query "VpnConnections[?State!='deleted'].[VpnConnectionId,State]" --output text
aws secretsmanager list-secrets \
  --filters Key=name,Values=resilai-test/ \
  --query 'SecretList[].[Name,DeletedDate]' --output text
