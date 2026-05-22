#!/bin/bash
# AIRS - Frontend Deployment Script (Bash)
# Builds and deploys the frontend to specific Firebase Hosting targets

set -euo pipefail

TARGET=""

usage() {
    cat <<EOF
Usage:
  ./scripts/deploy_frontend.sh --target <marketing|demo|staging>

Targets:
  marketing   Deploys landing page to resilai.org (builds with .env.production)
  demo        Deploys demo portal to demo.resilai.org (builds with .env.demo)
  staging     Deploys staging portal to staging.resilai.org (builds with .env.staging)
EOF
}

# Parse flags
while [[ $# -gt 0 ]]; do
    case "$1" in
        --target|-t)
            TARGET="${2:-}"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "ERROR: Unknown argument: $1"
            usage
            exit 1
            ;;
    esac
done

if [[ -z "$TARGET" ]]; then
    echo "ERROR: --target parameter is required."
    usage
    exit 1
fi

if [[ "$TARGET" != "marketing" && "$TARGET" != "demo" && "$TARGET" != "staging" ]]; then
    echo "ERROR: Invalid target: $TARGET. Must be one of: marketing, demo, staging."
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "AIRS - Frontend Deployment: $TARGET"
echo "========================================"
echo ""

# Check if firebase-tools (firebase CLI) is installed
if ! command -v firebase &> /dev/null; then
    echo "ERROR: firebase CLI not found. Please install firebase-tools npm package."
    exit 1
fi

cd "$PROJECT_ROOT/frontend"

# Run build based on target
echo "Step 1: Building frontend for target '$TARGET'..."
if [[ "$TARGET" == "marketing" ]]; then
    npm run build:production
elif [[ "$TARGET" == "demo" ]]; then
    npm run build:demo
elif [[ "$TARGET" == "staging" ]]; then
    npm run build:staging
fi

echo ""
echo "Step 2: Deploying to Firebase Hosting target '$TARGET'..."
cd "$PROJECT_ROOT"
firebase deploy --only "hosting:$TARGET"

echo ""
echo "========================================"
echo "Frontend deployment for '$TARGET' completed successfully!"
echo "========================================"
