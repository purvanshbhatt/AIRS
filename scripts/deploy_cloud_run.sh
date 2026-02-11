#!/bin/bash
# AIRS - Cloud Run Deployment Script (Bash)
# Deploys the AIRS API to Google Cloud Run

set -euo pipefail

# -----------------------------------------------------------------------------
# Safe defaults
# - Defaults to staging service + staging env file
# - Refuses deploying to the production demo unless --prod is provided
# -----------------------------------------------------------------------------

PROD_PROJECT_ID_DEFAULT="gen-lang-client-0384513977"
PROD_PROJECT_ID="${AIRS_PROD_PROJECT_ID:-$PROD_PROJECT_ID_DEFAULT}"

# Configuration (can be overridden by flags or legacy positional args)
SERVICE_NAME="airs-api-staging"
REGION="us-central1"
ENV_FILE="gcp/env.staging.yaml"
ALLOW_UNAUTHENTICATED="true"
CLOUDSQL_INSTANCE="${CLOUDSQL_INSTANCE:-}"  # e.g., "project:region:instance"
PROJECT_ID=""
ALLOW_PROD="false"

usage() {
    cat <<EOF
Usage:
  ./scripts/deploy_cloud_run.sh [service] [region] [env_file] [allow_unauthenticated]
  ./scripts/deploy_cloud_run.sh --service <name> --region <region> --env-file <path> [--project <id>] [--prod]

Defaults (safe):
  --service  airs-api-staging
  --env-file gcp/env.staging.yaml

Safety:
  Refuses production demo deploy unless --prod is provided.
  Production demo project id: ${PROD_PROJECT_ID}
EOF
}

# Parse flags (while keeping backward compatible positional args)
POSITIONAL=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --prod)
            ALLOW_PROD="true"
            shift
            ;;
        --service)
            SERVICE_NAME="${2:-}"
            shift 2
            ;;
        --region)
            REGION="${2:-}"
            shift 2
            ;;
        --env-file)
            ENV_FILE="${2:-}"
            shift 2
            ;;
        --project)
            PROJECT_ID="${2:-}"
            shift 2
            ;;
        --allow-unauthenticated)
            ALLOW_UNAUTHENTICATED="true"
            shift
            ;;
        --no-allow-unauthenticated)
            ALLOW_UNAUTHENTICATED="false"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        --)
            shift
            break
            ;;
        -*)
            echo "ERROR: Unknown flag: $1"
            usage
            exit 1
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done

# Legacy positional args: [service] [region] [env_file] [allow_unauthenticated]
if [[ ${#POSITIONAL[@]} -ge 1 ]]; then SERVICE_NAME="${POSITIONAL[0]}"; fi
if [[ ${#POSITIONAL[@]} -ge 2 ]]; then REGION="${POSITIONAL[1]}"; fi
if [[ ${#POSITIONAL[@]} -ge 3 ]]; then ENV_FILE="${POSITIONAL[2]}"; fi
if [[ ${#POSITIONAL[@]} -ge 4 ]]; then ALLOW_UNAUTHENTICATED="${POSITIONAL[3]}"; fi

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

# Helper: strip surrounding quotes
strip_quotes() {
    local v="$1"
    v="${v#\"}"; v="${v%\"}"
    v="${v#\'}"; v="${v%\'}"
    echo "$v"
}

# Helper: extract GCP_PROJECT_ID from env file (supports .env and .yaml)
extract_project_id() {
    local file_path="$1"
    local lower="${file_path,,}"

    if [[ "$lower" == *.yaml || "$lower" == *.yml ]]; then
        local line
        line="$(grep -E '^[[:space:]]*GCP_PROJECT_ID[[:space:]]*:' "$file_path" | head -n 1 || true)"
        if [[ -n "$line" ]]; then
            local val
            val="$(echo "$line" | sed -E 's/^[[:space:]]*GCP_PROJECT_ID[[:space:]]*:[[:space:]]*//')"
            val="$(echo "$val" | sed -E 's/[[:space:]]*#.*$//')"
            val="$(strip_quotes "$val")"
            echo "$val"
            return 0
        fi
        return 1
    fi

    local line
    line="$(grep -E '^[[:space:]]*GCP_PROJECT_ID=' "$file_path" | head -n 1 || true)"
    if [[ -n "$line" ]]; then
        local val="${line#*=}"
        val="$(echo "$val" | sed -E 's/[[:space:]]*#.*$//')"
        val="$(strip_quotes "$val")"
        echo "$val"
        return 0
    fi

    return 1
}

# Check if env file exists
if [[ "$ENV_FILE" == /* || "$ENV_FILE" =~ ^[A-Za-z]:[\\/].* ]]; then
    ENV_FILE_PATH="$ENV_FILE"
else
    ENV_FILE_PATH="$PROJECT_ROOT/$ENV_FILE"
fi

if [ ! -f "$ENV_FILE_PATH" ]; then
    echo "ERROR: Environment file not found: $ENV_FILE"
    echo "For staging, start from: gcp/env.staging.yaml"
    echo "For production, use:     gcp/env.prod.yaml (requires --prod)"
    exit 1
fi

# Resolve project id (flag > env file > gcloud config)
if [[ -z "$PROJECT_ID" ]]; then
    PROJECT_ID="$(extract_project_id "$ENV_FILE_PATH" 2>/dev/null || true)"
fi
if [[ -z "$PROJECT_ID" ]]; then
    PROJECT_ID="$(gcloud config get-value project 2>/dev/null || true)"
fi
PROJECT_ID="$(strip_quotes "${PROJECT_ID:-}")"

# Safety: block production deploys unless explicitly allowed with --prod
REQUIRE_PROD_CONFIRM="false"
if [[ "$SERVICE_NAME" == "airs-api" ]]; then
    REQUIRE_PROD_CONFIRM="true"
elif [[ -n "$PROJECT_ID" && "$PROJECT_ID" == "$PROD_PROJECT_ID" ]]; then
    REQUIRE_PROD_CONFIRM="true"
elif [[ "$ENV_FILE" == *"env.prod"* ]]; then
    REQUIRE_PROD_CONFIRM="true"
fi

if [[ "$REQUIRE_PROD_CONFIRM" == "true" && "$ALLOW_PROD" != "true" ]]; then
    echo "ERROR: Refusing to deploy to the PRODUCTION demo."
    echo "  Service:  $SERVICE_NAME"
    echo "  Project:  ${PROJECT_ID:-"(unknown)"}"
    echo "  Env file: $ENV_FILE"
    echo ""
    echo "Re-run with --prod to confirm."
    exit 2
fi

echo ""
echo "Deployment Configuration:"
echo "  Service:  $SERVICE_NAME"
if [ -n "$PROJECT_ID" ]; then
    echo "  Project:  $PROJECT_ID"
fi
echo "  Region:   $REGION"
echo "  Env file: $ENV_FILE"
if [ -n "$CLOUDSQL_INSTANCE" ]; then
    echo "  Cloud SQL: $CLOUDSQL_INSTANCE"
fi
echo ""

# Build gcloud command (array form to avoid eval/quoting issues)
DEPLOY_ARGS=(
    run deploy "$SERVICE_NAME"
    --source .
    --region "$REGION"
    --memory 512Mi
    --cpu 1
    --min-instances 0
    --max-instances 10
    --timeout 120
)

if [ -n "$PROJECT_ID" ]; then
    DEPLOY_ARGS+=(--project "$PROJECT_ID")
fi

if [ -n "$CLOUDSQL_INSTANCE" ]; then
    DEPLOY_ARGS+=(--add-cloudsql-instances="$CLOUDSQL_INSTANCE")
    echo "Attaching Cloud SQL instance: $CLOUDSQL_INSTANCE"
fi

# Env vars (prefer --env-vars-file for YAML)
ENV_COUNT=""
ENV_FILE_LOWER="${ENV_FILE_PATH,,}"
if [[ "$ENV_FILE_LOWER" == *.yaml || "$ENV_FILE_LOWER" == *.yml ]]; then
    DEPLOY_ARGS+=(--env-vars-file "$ENV_FILE_PATH")
    ENV_COUNT=$(grep -E '^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*[[:space:]]*:' "$ENV_FILE_PATH" | grep -vE '^[[:space:]]*#' | wc -l | tr -d ' ')
else
    echo "Reading environment variables from: $ENV_FILE"
    ENV_VARS=""
    while IFS= read -r line || [ -n "$line" ]; do
        line="$(echo "$line" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
        if [ -z "$line" ] || [[ "$line" =~ ^# ]]; then
            continue
        fi
        if [ -n "$ENV_VARS" ]; then
            ENV_VARS="$ENV_VARS,$line"
        else
            ENV_VARS="$line"
        fi
    done < "$ENV_FILE_PATH"

    ENV_COUNT=$(echo "$ENV_VARS" | tr ',' '\n' | grep -c . || echo 0)
    if [ -n "$ENV_VARS" ]; then
        DEPLOY_ARGS+=(--set-env-vars "$ENV_VARS")
    fi
fi

if [ -n "$ENV_COUNT" ]; then
    echo "  Env vars: $ENV_COUNT variables loaded"
fi

if [ "$ALLOW_UNAUTHENTICATED" = "true" ]; then
    DEPLOY_ARGS+=(--allow-unauthenticated)
fi

echo "Deploying to Cloud Run..."
echo ""

# Run deployment
gcloud "${DEPLOY_ARGS[@]}"

echo ""
echo "========================================"
echo "Deployment successful!"
echo "========================================"
echo ""

# Get and display service URL
echo "Fetching service URL..."
DESCRIBE_ARGS=(run services describe "$SERVICE_NAME" --region "$REGION" --format "value(status.url)")
if [ -n "$PROJECT_ID" ]; then
    DESCRIBE_ARGS+=(--project "$PROJECT_ID")
fi
SERVICE_URL=$(gcloud "${DESCRIBE_ARGS[@]}")

echo ""
echo "Service URL:"
echo "  $SERVICE_URL"
echo ""
echo "Health check:"
echo "  $SERVICE_URL/health"
echo ""
