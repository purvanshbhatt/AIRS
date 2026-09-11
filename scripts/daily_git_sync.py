#!/usr/bin/env python3
"""
ResilAI - Automated Daily Git Synchronization & Branch Isolation Runner.

Adheres strictly to the ResilAI Agent Governance Protocol:
- Target branch is strictly 'daily-sync' (NEVER push automatically to main or staging).
- Verifies that ignored & sensitive files (.env*, *.db, scratch/, __pycache__/, etc.) are NEVER committed.
- Embeds Google Antigravity SDK periodic triggers (every 24h / 86400s).
- Returns the developer cleanly to their original working branch after synchronization.
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import fnmatch
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [ResilAI-DailySync] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("daily_git_sync")

# Constants & Governance Rules
TARGET_SYNC_BRANCH = "daily-sync"
PROTECTED_BRANCHES = {"main", "master", "staging", "demo", "prod", "production"}

# Sensitive & Ignored file patterns that must NEVER be committed to daily-sync
FORBIDDEN_PATTERNS = [
    ".env",
    ".env.*",
    "*.local",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.pem",
    "*.p12",
    "*.key",
    "*service-account*.json",
    "*service_account*.json",
    "scratch/*",
    "*/scratch/*",
    "__pycache__/*",
    "*/__pycache__/*",
    "*.pyc",
    ".firebase/*",
    "*/.firebase/*",
    "gcp/env.prod",
    "gcp/env.staging",
    "*.log",
    "archive/logs/*",
    ".pytest_cache/*",
]

# Explicitly allowed non-sensitive templates/stubs
ALLOWED_EXCEPTIONS = [
    ".env.example",
    ".env.dev.example",
    "frontend/.env.example",
    "frontend/.env.development",
    "frontend/.env.staging",
    "frontend/.env.production",
]


class GitSyncError(Exception):
    """Custom exception for daily git synchronization errors."""
    pass


def run_cmd(
    cmd: List[str],
    cwd: Optional[Path] = None,
    check: bool = True,
    capture_output: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess:
    """Execute a shell command via subprocess with error logging."""
    cwd_path = cwd or Path.cwd()
    cmd_str = " ".join(cmd)
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd_path),
            check=check,
            capture_output=capture_output,
            text=text,
        )
        return result
    except subprocess.CalledProcessError as err:
        logger.error(f"Command failed: {cmd_str}")
        if err.stdout:
            logger.error(f"Stdout: {err.stdout.strip()}")
        if err.stderr:
            logger.error(f"Stderr: {err.stderr.strip()}")
        raise


def get_repo_root() -> Path:
    """Find the root directory of the git repository."""
    result = run_cmd(["git", "rev-parse", "--show-toplevel"])
    return Path(result.stdout.strip())


def get_current_branch(repo_root: Path) -> str:
    """Get the name of the currently checked out branch."""
    result = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
    branch = result.stdout.strip()
    return branch


def get_staged_files(repo_root: Path) -> List[str]:
    """Return a list of all staged file paths relative to repo root."""
    result = run_cmd(["git", "diff", "--cached", "--name-only"], cwd=repo_root)
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return lines


def is_forbidden_file(file_path: str) -> bool:
    """Check if a staged file path matches forbidden/sensitive patterns."""
    norm_path = file_path.replace("\\", "/")
    
    # Check exceptions first
    for allowed in ALLOWED_EXCEPTIONS:
        if norm_path == allowed or fnmatch.fnmatch(norm_path, allowed):
            return False
            
    # Check forbidden patterns
    for pattern in FORBIDDEN_PATTERNS:
        if fnmatch.fnmatch(norm_path, pattern) or fnmatch.fnmatch(Path(norm_path).name, pattern):
            return True
            
    # Explicit check for local environment secrets
    if re.search(r"(^|/)\.env(\.[^/]+)?$", norm_path) and norm_path not in ALLOWED_EXCEPTIONS:
        return True
        
    return False


def sanitize_staging_index(repo_root: Path) -> List[str]:
    """
    Inspect all staged files. If any sensitive or ignored file is staged,
    unstage it immediately and return list of uncommitted/unstaged sensitive files.
    """
    staged = get_staged_files(repo_root)
    unseated: List[str] = []
    
    for file_path in staged:
        if is_forbidden_file(file_path):
            logger.warning(f"SECURITY GUARD: Unstaging forbidden/sensitive file: {file_path}")
            run_cmd(["git", "reset", "HEAD", file_path], cwd=repo_root)
            unseated.append(file_path)
            
    return unseated


def check_remote_branch_exists(repo_root: Path, remote: str, branch: str) -> bool:
    """Check if branch exists on the specified git remote."""
    result = run_cmd(["git", "ls-remote", "--heads", remote, branch], cwd=repo_root, check=False)
    return bool(result.stdout.strip())


def perform_daily_git_sync(
    repo_root: Optional[Path] = None,
    dry_run: bool = False,
    force_push: bool = True,
) -> Tuple[bool, str]:
    """
    Core automated synchronization routine:
    1. Records original working branch.
    2. Enforces target branch invariant (daily-sync).
    3. Stages updates with 'git add -A'.
    4. Sanitizes index against forbidden/sensitive files.
    5. Commits to daily-sync snapshot branch.
    6. Pushes to remote origin/daily-sync.
    7. Restores developer safely to original working branch.
    """
    root = repo_root or get_repo_root()
    original_branch = get_current_branch(root)
    logger.info(f"Initiating daily git sync from active branch: '{original_branch}'")
    
    # Invariant checks
    if TARGET_SYNC_BRANCH in PROTECTED_BRANCHES:
        raise GitSyncError(f"Target sync branch '{TARGET_SYNC_BRANCH}' conflicts with protected branch list!")
        
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    commit_msg = f"chore(sync): automated daily agent snapshot [{timestamp}]"
    
    if dry_run:
        logger.info("[DRY-RUN] Simulating daily sync routine...")
        logger.info(f"[DRY-RUN] Original branch: {original_branch}")
        logger.info(f"[DRY-RUN] Target branch: {TARGET_SYNC_BRANCH}")
        logger.info(f"[DRY-RUN] Snapshot commit message: {commit_msg}")
        return True, "Dry-run completed successfully"

    try:
        # Step 1: Stage all changes
        logger.info("Staging pending workspace updates ('git add -A')...")
        run_cmd(["git", "add", "-A"], cwd=root)
        
        # Step 2: Sanitize staging index
        unseated = sanitize_staging_index(root)
        if unseated:
            logger.info(f"Unstaged {len(unseated)} forbidden files prior to snapshot.")

        # Check if there are staged changes
        staged_files = get_staged_files(root)
        has_staged_changes = bool(staged_files)
        logger.info(f"Staged files for snapshot: {len(staged_files)}")

        # Step 3: Handle branch isolation for daily-sync
        if original_branch == TARGET_SYNC_BRANCH:
            if has_staged_changes:
                logger.info(f"Committing snapshot directly on {TARGET_SYNC_BRANCH}...")
                run_cmd(["git", "commit", "-m", commit_msg], cwd=root)
            else:
                logger.info("No new changes to commit on daily-sync.")
        else:
            logger.info(f"Capturing working tree snapshot for branch: {TARGET_SYNC_BRANCH}...")
            if has_staged_changes:
                # Checkout or create daily-sync carrying changes
                run_cmd(["git", "checkout", "-B", TARGET_SYNC_BRANCH], cwd=root)
                run_cmd(["git", "commit", "-m", commit_msg], cwd=root)
            else:
                # No uncommitted changes, sync current commit pointer
                run_cmd(["git", "branch", "-f", TARGET_SYNC_BRANCH, "HEAD"], cwd=root)
                run_cmd(["git", "checkout", TARGET_SYNC_BRANCH], cwd=root)

        # Step 4: Push to remote daily-sync
        remotes_result = run_cmd(["git", "remote"], cwd=root)
        remotes = [r.strip() for r in remotes_result.stdout.splitlines() if r.strip()]
        
        if "origin" in remotes:
            logger.info(f"Pushing '{TARGET_SYNC_BRANCH}' to remote 'origin'...")
            push_cmd = ["git", "push", "-u", "origin", TARGET_SYNC_BRANCH]
            if force_push:
                push_cmd.append("--force")
            run_cmd(push_cmd, cwd=root)
            logger.info(f"Successfully pushed '{TARGET_SYNC_BRANCH}' to origin.")
        else:
            logger.warning("No 'origin' remote found. Snapshot committed locally only.")

        # Step 5: Always return developer to original working branch
        if original_branch != TARGET_SYNC_BRANCH:
            logger.info(f"Returning to original working branch: '{original_branch}'...")
            run_cmd(["git", "checkout", original_branch], cwd=root)
            current = get_current_branch(root)
            logger.info(f"Active branch restored to: '{current}'")

        summary = f"Daily sync successful: [{timestamp}] on branch '{TARGET_SYNC_BRANCH}'."
        logger.info(summary)
        return True, summary

    except Exception as exc:
        logger.error(f"Error during daily git sync: {exc}")
        # Attempt recovery to original branch
        try:
            current = get_current_branch(root)
            if current != original_branch:
                logger.info(f"Restoring to original branch '{original_branch}' following error...")
                run_cmd(["git", "checkout", original_branch], cwd=root, check=False)
        except Exception:
            pass
        raise


# =============================================================================
# Google Antigravity SDK Periodic Trigger Integration
# =============================================================================

async def antigravity_trigger_handler(ctx) -> None:
    """Antigravity periodic trigger callback."""
    logger.info("Antigravity trigger fired: executing daily_git_sync routine.")
    try:
        success, msg = perform_daily_git_sync()
        logger.info(f"Trigger execution result: {msg}")
        if hasattr(ctx, "send") and callable(ctx.send):
            await ctx.send(f"[ResilAI-DailySync] {msg}")
    except Exception as err:
        logger.error(f"Trigger execution failed: {err}")
        if hasattr(ctx, "send") and callable(ctx.send):
            await ctx.send(f"[ResilAI-DailySync ERROR] {err}")


def run_antigravity_scheduler(interval_seconds: int = 86400) -> None:
    """
    Start the Google Antigravity SDK Agent with a periodic trigger.
    Runs every `interval_seconds` (default: 86400s / 24 hours).
    """
    logger.info(f"Initializing Google Antigravity Agent with periodic trigger (interval: {interval_seconds}s)...")
    
    try:
        from google.antigravity import Agent, LocalAgentConfig
        from google.antigravity.triggers import every, TriggerContext

        periodic_trigger = every(interval_seconds, antigravity_trigger_handler)

        config = LocalAgentConfig(
            system_instructions=(
                "You are the ResilAI DevOps & Tooling Automation Agent. "
                "Your duty is to run periodic daily git snapshots to the isolated daily-sync branch."
            ),
            triggers=[periodic_trigger],
        )

        async def _main():
            async with Agent(config) as agent:
                logger.info("Google Antigravity Agent active. Listening for periodic triggers...")
                while True:
                    await asyncio.sleep(3600)

        asyncio.run(_main())

    except ImportError:
        logger.warning("google.antigravity SDK not available in environment. Falling back to native async timer.")
        
        async def _fallback_scheduler():
            while True:
                logger.info("Native fallback scheduler triggering daily sync...")
                try:
                    perform_daily_git_sync()
                except Exception as e:
                    logger.error(f"Sync error: {e}")
                logger.info(f"Sleeping for {interval_seconds} seconds until next sync cycle...")
                await asyncio.sleep(interval_seconds)

        asyncio.run(_fallback_scheduler())


def main():
    parser = argparse.ArgumentParser(
        description="ResilAI Automated Daily Git Sync & Antigravity Periodic Runner"
    )
    parser.add_argument(
        "--once",
        "--now",
        action="store_true",
        default=False,
        help="Execute a single daily sync run immediately and exit (default mode if --schedule not set)",
    )
    parser.add_argument(
        "--schedule",
        "--daemon",
        action="store_true",
        default=False,
        help="Start the Google Antigravity scheduled periodic runner daemon",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=86400,
        help="Periodic sync interval in seconds (default: 86400 = 24h)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Simulate the sync without committing or pushing changes",
    )
    parser.add_argument(
        "--no-force",
        action="store_true",
        default=False,
        help="Disable force push to daily-sync (fast-forward only)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Enable debug logging output",
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.schedule:
        run_antigravity_scheduler(interval_seconds=args.interval)
    else:
        perform_daily_git_sync(dry_run=args.dry_run, force_push=not args.no_force)


if __name__ == "__main__":
    main()
