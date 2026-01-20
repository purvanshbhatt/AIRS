#!/bin/bash
# AIRS - GCP Bootstrap Script (Bash)
# Sets up GCP project, enables required APIs, and configures defaults

set -e

# Configuration
PROJECT_ID="${1:-gen-lang-client-0384513977}"
REGION="${2:-us-central1}"

echo "========================================"
echo "AIRS - GCP Bootstrap"
echo "========================================"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "ERROR: gcloud CLI not found. Please install Google Cloud SDK."
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo "Setting project to: $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

# Set default region
echo "Setting default region to: $REGION"
gcloud config set run/region "$REGION"

# Set default platform to managed
echo "Setting default platform to: managed"
gcloud config set run/platform managed

# Enable required APIs
echo ""
echo "Enabling required APIs..."

APIS=(
    "run.googleapis.com"
    "cloudbuild.googleapis.com"
    "artifactregistry.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo "  Enabling $api..."
    gcloud services enable "$api" --quiet
done

echo ""
echo "========================================"
echo "Bootstrap complete!"
echo "========================================"
echo ""
echo "Project:  $PROJECT_ID"
echo "Region:   $REGION"
echo "Platform: managed"
echo ""
echo "Next steps:"
echo "  1. Copy gcp/env.prod.example to gcp/env.prod"
echo "  2. Fill in your production values"
echo "  3. Run: ./scripts/deploy_cloud_run.sh"
