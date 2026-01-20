#!/bin/bash
# AIRS - Cloud Run Deployment Script (Bash)
# Deploys the AIRS API to Google Cloud Run

set -e

# Configuration
SERVICE_NAME="${1:-airs-api}"
REGION="${2:-us-central1}"
ENV_FILE="${3:-gcp/env.prod}"
ALLOW_UNAUTHENTICATED="${4:-true}"
CLOUDSQL_INSTANCE="${CLOUDSQL_INSTANCE:-}"  # e.g., "project:region:instance"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "AIRS - Cloud Run Deployment"
echo "========================================"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "ERROR: gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

# Check if env file exists
ENV_FILE_PATH="$PROJECT_ROOT/$ENV_FILE"
if [ ! -f "$ENV_FILE_PATH" ]; then
    echo "ERROR: Environment file not found: $ENV_FILE"
    echo "Please copy gcp/env.prod.example to gcp/env.prod and fill in values."
    exit 1
fi

# Read environment variables from file
echo "Reading environment variables from: $ENV_FILE"
ENV_VARS=""
while IFS= read -r line || [ -n "$line" ]; do
    # Trim whitespace
    line=$(echo "$line" | xargs)
    # Skip empty lines and comments
    if [ -n "$line" ] && [[ ! "$line" =~ ^# ]]; then
        if [ -n "$ENV_VARS" ]; then
            ENV_VARS="$ENV_VARS,$line"
        else
            ENV_VARS="$line"
        fi
    fi
done < "$ENV_FILE_PATH"

# Count env vars
ENV_COUNT=$(echo "$ENV_VARS" | tr ',' '\n' | grep -c . || echo 0)

echo ""
echo "Deployment Configuration:"
echo "  Service:  $SERVICE_NAME"
echo "  Region:   $REGION"
echo "  Env vars: $ENV_COUNT variables loaded"
if [ -n "$CLOUDSQL_INSTANCE" ]; then
    echo "  Cloud SQL: $CLOUDSQL_INSTANCE"
fi
echo ""

# Build gcloud command
DEPLOY_CMD="gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 120"

# Add Cloud SQL connection if specified
if [ -n "$CLOUDSQL_INSTANCE" ]; then
    DEPLOY_CMD="$DEPLOY_CMD --add-cloudsql-instances=$CLOUDSQL_INSTANCE"
    echo "Attaching Cloud SQL instance: $CLOUDSQL_INSTANCE"
fi

if [ -n "$ENV_VARS" ]; then
    DEPLOY_CMD="$DEPLOY_CMD --set-env-vars=\"$ENV_VARS\""
fi

if [ "$ALLOW_UNAUTHENTICATED" = "true" ]; then
    DEPLOY_CMD="$DEPLOY_CMD --allow-unauthenticated"
fi

echo "Deploying to Cloud Run..."
echo ""

# Run deployment
eval "$DEPLOY_CMD"

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Deployment failed!"
    exit 1
fi

echo ""
echo "========================================"
echo "Deployment successful!"
echo "========================================"
echo ""

# Get and display service URL
echo "Fetching service URL..."
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format "value(status.url)")

echo ""
echo "Service URL:"
echo "  $SERVICE_URL"
echo ""
echo "Health check:"
echo "  $SERVICE_URL/health"
echo ""
