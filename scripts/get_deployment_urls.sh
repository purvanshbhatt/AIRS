#!/bin/bash
#
# Prints the active deployment URLs for AIRS (Cloud Run backend + Firebase Hosting frontend).
# Helper script for operators to discover real origins before updating CORS configuration.
#
# Usage: ./scripts/get_deployment_urls.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo ""
echo "========================================"
echo "  AIRS Deployment URLs"
echo "========================================"
echo ""

# --- Backend: Cloud Run ---
echo -e "\033[33m[Backend - Cloud Run]\033[0m"

CLOUD_RUN_URL=""

# Try gcloud first
if command -v gcloud &> /dev/null; then
    CLOUD_RUN_URL=$(gcloud run services describe airs-api --region us-central1 --format="value(status.url)" 2>/dev/null || true)
    if [ -n "$CLOUD_RUN_URL" ]; then
        echo -e "  Service URL: \033[32m$CLOUD_RUN_URL\033[0m"
    fi
fi

if [ -z "$CLOUD_RUN_URL" ]; then
    # Fallback: check env.prod.yaml for project ID
    ENV_FILE="$PROJECT_ROOT/gcp/env.prod.yaml"
    if [ -f "$ENV_FILE" ]; then
        PROJECT_ID=$(grep -oP 'GCP_PROJECT_ID:\s*["'"'"']?\K[^"'"'"'\s]+' "$ENV_FILE" 2>/dev/null || true)
        if [ -n "$PROJECT_ID" ]; then
            echo "  (gcloud unavailable - using project ID from env.prod.yaml)"
            echo "  Estimated URL: https://airs-api-<project-number>.us-central1.run.app"
            echo "  Project ID: $PROJECT_ID"
        fi
    else
        echo -e "  \033[31m(Could not determine - run 'gcloud run services list' manually)\033[0m"
    fi
fi

echo ""

# --- Frontend: Firebase Hosting ---
echo -e "\033[33m[Frontend - Firebase Hosting]\033[0m"

FIREBASE_RC="$PROJECT_ROOT/.firebaserc"
FIREBASE_PROJECT=""
SITES=()

if [ -f "$FIREBASE_RC" ]; then
    # Extract default project
    FIREBASE_PROJECT=$(grep -oP '"default":\s*"\K[^"]+' "$FIREBASE_RC" 2>/dev/null || true)
    
    # Try to extract hosting sites from targets
    if command -v jq &> /dev/null; then
        SITE_NAMES=$(jq -r ".targets.\"$FIREBASE_PROJECT\".hosting | to_entries[]?.value[]?" "$FIREBASE_RC" 2>/dev/null || true)
        if [ -n "$SITE_NAMES" ]; then
            while IFS= read -r site; do
                SITES+=("$site")
            done <<< "$SITE_NAMES"
        fi
    fi
fi

if [ -n "$FIREBASE_PROJECT" ]; then
    echo "  Firebase Project: $FIREBASE_PROJECT"
    echo ""
    
    if [ ${#SITES[@]} -gt 0 ]; then
        echo -e "  \033[32mHosting Sites:\033[0m"
        for site in "${SITES[@]}"; do
            echo -e "    - \033[32mhttps://$site.web.app\033[0m"
            echo -e "    - \033[32mhttps://$site.firebaseapp.com\033[0m"
        done
    else
        echo -e "  \033[32mDefault Site URLs:\033[0m"
        echo -e "    - \033[32mhttps://$FIREBASE_PROJECT.web.app\033[0m"
        echo -e "    - \033[32mhttps://$FIREBASE_PROJECT.firebaseapp.com\033[0m"
    fi
else
    echo "  (No .firebaserc found - Firebase Hosting not configured)"
fi

echo ""

# --- CORS Origins Summary ---
echo "========================================"
echo "  Suggested CORS Origins"
echo "========================================"
echo ""

ORIGINS=()

if [ ${#SITES[@]} -gt 0 ]; then
    for site in "${SITES[@]}"; do
        ORIGINS+=("https://$site.web.app")
        ORIGINS+=("https://$site.firebaseapp.com")
    done
elif [ -n "$FIREBASE_PROJECT" ]; then
    ORIGINS+=("https://$FIREBASE_PROJECT.web.app")
    ORIGINS+=("https://$FIREBASE_PROJECT.firebaseapp.com")
fi

ORIGINS+=("http://localhost:5173")

if [ ${#ORIGINS[@]} -gt 0 ]; then
    echo -e "\033[33mCopy this value for CORS_ALLOW_ORIGINS:\033[0m"
    echo ""
    CORS_VALUE=$(IFS=,; echo "${ORIGINS[*]}")
    echo "  $CORS_VALUE"
    echo ""
fi

echo "----------------------------------------"
echo "To update CORS in Cloud Run:"
echo "  1. Edit gcp/env.prod.yaml"
echo "  2. Run: gcloud run deploy airs-api --source . --region us-central1 --allow-unauthenticated --env-vars-file gcp/env.prod.yaml"
echo ""
