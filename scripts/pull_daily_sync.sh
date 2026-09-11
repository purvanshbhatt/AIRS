#!/bin/bash
# =============================================================================
# ResilAI - Pull Daily Sync Script (Bash)
# Single-command synchronization for developers resuming work on a new device/machine.
# Fetches the isolated 'daily-sync' snapshot from remote and offers interactive
# or flag-driven checkout/rebase options.
# =============================================================================

set -euo pipefail

# Text formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

SYNC_BRANCH="daily-sync"
REMOTE="origin"
TARGET_NEW_BRANCH=""
ACTION=""
DRY_RUN=false
FORCE=false

usage() {
    cat <<EOF
${BOLD}ResilAI Daily Sync Pull Utility${NC}

Usage:
  ./scripts/pull_daily_sync.sh [options]

Options:
  --checkout                 Checkout the '${SYNC_BRANCH}' branch directly
  -b, --new-branch <name>    Create and checkout a new branch based on '${SYNC_BRANCH}'
  --rebase                   Rebase current working branch onto '${SYNC_BRANCH}'
  --merge                    Merge '${SYNC_BRANCH}' into current working branch
  --dry-run                  Fetch and display latest snapshot without changing branches
  -f, --force                Force checkout or fetch operations
  -h, --help                 Show this help message

Examples:
  ./scripts/pull_daily_sync.sh
  ./scripts/pull_daily_sync.sh --checkout
  ./scripts/pull_daily_sync.sh -b feature/continue-investigation
  ./scripts/pull_daily_sync.sh --rebase
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --checkout)
            ACTION="checkout"
            shift
            ;;
        -b|--new-branch|--branch)
            ACTION="new-branch"
            TARGET_NEW_BRANCH="${2:-}"
            if [[ -z "$TARGET_NEW_BRANCH" ]]; then
                echo -e "${RED}ERROR: Missing branch name for --new-branch${NC}"
                exit 1
            fi
            shift 2
            ;;
        --rebase)
            ACTION="rebase"
            shift
            ;;
        --merge)
            ACTION="merge"
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}ERROR: Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}${BOLD}ResilAI - Daily Git Sync Pull Utility${NC}"
echo -e "${CYAN}======================================================${NC}"
echo ""

# Check if git repository
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo -e "${RED}ERROR: Not inside a git repository.${NC}"
    exit 1
fi

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "HEAD")"
echo -e "Current active branch: ${BOLD}${YELLOW}${CURRENT_BRANCH}${NC}"

# Check remote
if ! git remote | grep -q "^${REMOTE}$"; then
    echo -e "${RED}ERROR: Remote '${REMOTE}' not found in this repository.${NC}"
    exit 1
fi

echo -e "Fetching latest '${SYNC_BRANCH}' snapshot from remote '${REMOTE}'..."
if ! git fetch "$REMOTE" "$SYNC_BRANCH" 2>/dev/null; then
    echo -e "${RED}ERROR: Branch '${SYNC_BRANCH}' does not exist on remote '${REMOTE}'.${NC}"
    echo -e "Ensure that 'daily_git_sync.py' has executed at least one daily snapshot."
    exit 1
fi

LATEST_COMMIT="$(git log -1 --format="%h - %s (%cr) <%an>" "${REMOTE}/${SYNC_BRANCH}")"
LATEST_TIMESTAMP="$(git log -1 --format="%cd" --date=iso "${REMOTE}/${SYNC_BRANCH}")"

echo -e "${GREEN}✓ Successfully fetched '${SYNC_BRANCH}' from ${REMOTE}${NC}"
echo -e "Latest Snapshot Commit: ${BOLD}${LATEST_COMMIT}${NC}"
echo -e "Snapshot Date:          ${LATEST_TIMESTAMP}"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[DRY-RUN] Showing latest commit details:${NC}"
    git log -1 --stat "${REMOTE}/${SYNC_BRANCH}"
    echo -e "${YELLOW}[DRY-RUN] No branch changes applied.${NC}"
    exit 0
fi

# If action is not specified via flags, prompt interactively
if [[ -z "$ACTION" ]]; then
    if [ -t 0 ]; then
        echo -e "${BOLD}Select how to apply the daily snapshot:${NC}"
        echo -e "  ${CYAN}1)${NC} Checkout '${SYNC_BRANCH}' directly"
        echo -e "  ${CYAN}2)${NC} Create a new branch from '${SYNC_BRANCH}' (Recommended for new work)"
        echo -e "  ${CYAN}3)${NC} Rebase current branch ('${CURRENT_BRANCH}') onto '${SYNC_BRANCH}'"
        echo -e "  ${CYAN}4)${NC} Merge '${SYNC_BRANCH}' into current branch ('${CURRENT_BRANCH}')"
        echo -e "  ${CYAN}5)${NC} Exit without changes"
        echo ""
        read -r -p "Select option [1-5] (default: 2): " choice
        choice="${choice:-2}"

        case "$choice" in
            1) ACTION="checkout" ;;
            2)
                ACTION="new-branch"
                read -r -p "Enter new branch name (e.g. feature/resume-sync): " TARGET_NEW_BRANCH
                if [[ -z "$TARGET_NEW_BRANCH" ]]; then
                    TARGET_NEW_BRANCH="feature/resumed-sync-$(date +%Y%m%d)"
                    echo -e "Defaulting branch name to: ${TARGET_NEW_BRANCH}"
                fi
                ;;
            3) ACTION="rebase" ;;
            4) ACTION="merge" ;;
            5)
                echo -e "Exiting without applying changes."
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid selection. Aborting.${NC}"
                exit 1
                ;;
        esac
    else
        # Non-interactive without flags defaults to checkout
        ACTION="checkout"
    fi
fi

# Execute selected action
case "$ACTION" in
    checkout)
        echo -e "Checking out '${SYNC_BRANCH}'..."
        if git show-ref --verify --quiet "refs/heads/${SYNC_BRANCH}"; then
            git checkout "$SYNC_BRANCH"
            git reset --hard "${REMOTE}/${SYNC_BRANCH}"
        else
            git checkout -b "$SYNC_BRANCH" "${REMOTE}/${SYNC_BRANCH}"
        fi
        echo -e "${GREEN}✓ Checked out '${SYNC_BRANCH}'. Workspace is now up to date with latest daily snapshot.${NC}"
        ;;
    new-branch)
        echo -e "Creating and checking out new branch '${TARGET_NEW_BRANCH}' based on '${REMOTE}/${SYNC_BRANCH}'..."
        if git show-ref --verify --quiet "refs/heads/${TARGET_NEW_BRANCH}"; then
            if [ "$FORCE" = true ]; then
                git checkout -B "$TARGET_NEW_BRANCH" "${REMOTE}/${SYNC_BRANCH}"
            else
                echo -e "${RED}ERROR: Branch '${TARGET_NEW_BRANCH}' already exists locally. Use -f or a different name.${NC}"
                exit 1
            fi
        else
            git checkout -b "$TARGET_NEW_BRANCH" "${REMOTE}/${SYNC_BRANCH}"
        fi
        echo -e "${GREEN}✓ Created and active on branch '${TARGET_NEW_BRANCH}' based on latest snapshot.${NC}"
        ;;
    rebase)
        echo -e "Rebasing current branch '${CURRENT_BRANCH}' onto '${REMOTE}/${SYNC_BRANCH}'..."
        git rebase "${REMOTE}/${SYNC_BRANCH}"
        echo -e "${GREEN}✓ Successfully rebased '${CURRENT_BRANCH}' onto latest daily snapshot.${NC}"
        ;;
    merge)
        echo -e "Merging '${REMOTE}/${SYNC_BRANCH}' into '${CURRENT_BRANCH}'..."
        git merge "${REMOTE}/${SYNC_BRANCH}" -m "chore(sync): merge daily-sync snapshot into ${CURRENT_BRANCH}"
        echo -e "${GREEN}✓ Successfully merged latest daily snapshot into '${CURRENT_BRANCH}'.${NC}"
        ;;
    *)
        echo -e "${RED}ERROR: Invalid action '${ACTION}'${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}${BOLD}Daily sync recovery complete! You may now resume development.${NC}"
