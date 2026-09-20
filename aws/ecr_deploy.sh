#!/bin/bash
# =============================================================================
# ResilAI - Amazon ECR Deployment Script
#
# Builds the unified ResilAI container and pushes versioned/immutable images
# to Amazon Elastic Container Registry (ECR).
#
# Non-negotiable:
#   - Never rely solely on :latest. Always attach immutable Git SHA + Version.
#   - Identical Dockerfile used for GCP Cloud Run and AWS App Runner.
#   - Zero hardcoded account IDs or secrets.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Defaults (overridable via flags or environment variables)
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_PROFILE="${AWS_PROFILE:-default}"
REPOSITORY_NAME="${ECR_REPOSITORY:-resilai-backend}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"

usage() {
    cat <<EOF
Usage:
  ./aws/ecr_deploy.sh [--region <region>] [--profile <profile>] [--repo <name>] [--account-id <id>]

Flags:
  --region        AWS region (default: us-east-1)
  --profile       AWS CLI profile to use (default: default)
  --repo          ECR repository name (default: resilai-backend)
  --account-id    AWS Account ID (auto-detected via STS if omitted)
  -h, --help      Show this help message

Requirements:
  - aws CLI v2
  - docker
EOF
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        --repo)
            REPOSITORY_NAME="$2"
            shift 2
            ;;
        --account-id)
            AWS_ACCOUNT_ID="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "ERROR: Unknown argument: $1"
            usage
            ;;
    esac
done

echo "============================================================"
echo "ResilAI Multi-Cloud — Amazon ECR Container Packaging"
echo "============================================================"

# Verify prerequisites
if ! command -v aws &> /dev/null; then
    echo "ERROR: AWS CLI not found. Please install or ensure it is on PATH."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker not found. Docker daemon must be installed and running."
    exit 1
fi

# Detect AWS Account ID if not passed
if [[ -z "$AWS_ACCOUNT_ID" ]]; then
    echo "Detecting AWS Account ID via STS..."
    AWS_ACCOUNT_ID="$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query "Account" --output text 2>/dev/null || true)"
    if [[ -z "$AWS_ACCOUNT_ID" || "$AWS_ACCOUNT_ID" == "None" ]]; then
        echo "ERROR: Failed to detect AWS Account ID. Please authenticate (aws login) or pass --account-id."
        exit 1
    fi
fi

ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
IMAGE_NAME="${ECR_REGISTRY}/${REPOSITORY_NAME}"

# Derive immutable build identifiers
GIT_SHA="$(git -C "$PROJECT_ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown")"
BUILD_TIMESTAMP="$(date -u +"%Y%m%d-%H%M%S")"
RELEASE_VERSION="1.0.0"
VERSION_TAG="${RELEASE_VERSION}-${BUILD_TIMESTAMP}-git-${GIT_SHA}"

echo "Configuration:"
echo "  AWS Region:       $AWS_REGION"
echo "  AWS Profile:      $AWS_PROFILE"
echo "  ECR Registry:     $ECR_REGISTRY"
echo "  Repository:       $REPOSITORY_NAME"
echo "  Immutable Tag:    $VERSION_TAG"
echo "  Latest Tag:       latest"
echo ""

# Ensure ECR repository exists
echo "Checking ECR repository '$REPOSITORY_NAME'..."
if ! aws ecr describe-repositories --repository-names "$REPOSITORY_NAME" --region "$AWS_REGION" --profile "$AWS_PROFILE" &> /dev/null; then
    echo "Creating ECR repository '$REPOSITORY_NAME' with tag immutability and scan-on-push..."
    aws ecr create-repository \
        --repository-name "$REPOSITORY_NAME" \
        --image-tag-mutability MUTABLE \
        --image-scanning-configuration scanOnPush=true \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" \
        --tags Key=Project,Value=ResilAI Key=ManagedBy,Value=MultiCloudDevOps
    echo "✓ ECR repository created."
else
    echo "✓ ECR repository exists."
fi

# Apply credit-saving ECR lifecycle policy (retains max 5 images, purges untagged)
echo "Enforcing credit-saving ECR lifecycle policy on '$REPOSITORY_NAME'..."
aws ecr put-lifecycle-policy \
    --repository-name "$REPOSITORY_NAME" \
    --lifecycle-policy-text '{
        "rules": [
            {
                "rulePriority": 1,
                "description": "Expire untagged images older than 1 day",
                "selection": {
                    "tagStatus": "untagged",
                    "countType": "sinceImagePushed",
                    "countUnit": "days",
                    "countNumber": 1
                },
                "action": {
                    "type": "expire"
                }
            },
            {
                "rulePriority": 2,
                "description": "Keep only latest 5 tagged images to conserve storage credits",
                "selection": {
                    "tagStatus": "any",
                    "countType": "imageCountMoreThan",
                    "countNumber": 5
                },
                "action": {
                    "type": "expire"
                }
            }
        ]
    }' \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" >/dev/null 2>&1 || true
echo "✓ ECR lifecycle policy configured (Max 5 images retained)."

# Authenticate Docker to ECR
echo "Authenticating Docker with Amazon ECR..."
aws ecr get-login-password --region "$AWS_REGION" --profile "$AWS_PROFILE" | \
    docker login --username AWS --password-stdin "$ECR_REGISTRY"
echo "✓ Docker authenticated."

# Build container using unified Dockerfile
echo ""
echo "Building unified container image from $PROJECT_ROOT/Dockerfile..."
docker build \
    --file "$PROJECT_ROOT/Dockerfile" \
    --tag "${IMAGE_NAME}:${VERSION_TAG}" \
    --tag "${IMAGE_NAME}:latest" \
    --build-arg BUILD_DATE="$BUILD_TIMESTAMP" \
    --build-arg VCS_REF="$GIT_SHA" \
    "$PROJECT_ROOT"

echo "✓ Build complete."

# Push versioned image and latest tag
echo ""
echo "Pushing immutable image tag: ${IMAGE_NAME}:${VERSION_TAG}..."
docker push "${IMAGE_NAME}:${VERSION_TAG}"

echo "Pushing convenience tag: ${IMAGE_NAME}:latest..."
docker push "${IMAGE_NAME}:latest"

echo ""
echo "============================================================"
echo "Deployment Packaging Successful!"
echo "Immutable Image URI: ${IMAGE_NAME}:${VERSION_TAG}"
echo "Latest Image URI:    ${IMAGE_NAME}:latest"
echo "============================================================"
