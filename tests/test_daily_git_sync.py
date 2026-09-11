"""
Unit tests for scripts/daily_git_sync.py.
Verifies git isolation invariants, forbidden file detection, index sanitization, and Antigravity triggers.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Ensure scripts directory is in sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from daily_git_sync import (
    is_forbidden_file,
    TARGET_SYNC_BRANCH,
    PROTECTED_BRANCHES,
    FORBIDDEN_PATTERNS,
    ALLOWED_EXCEPTIONS,
    perform_daily_git_sync,
    sanitize_staging_index,
    get_repo_root,
    get_current_branch,
    get_staged_files,
    check_remote_branch_exists,
    GitSyncError,
)


class TestDailyGitSyncSecurity:
    """Tests for file exclusion, governance rules, and sensitive pattern protection."""

    @pytest.mark.parametrize(
        "file_path",
        [
            ".env",
            ".env.local",
            ".env.secret",
            "backend/.env",
            "backend/.env.local",
            "airs_dev.db",
            "path/to/data.sqlite3",
            "scratch/scratchpad.py",
            "backend/scratch/temp.txt",
            "__pycache__/module.cpython-313.pyc",
            "app/__pycache__/main.pyc",
            "config/service-account.json",
            "keys/gcp_service_account.json",
            "certs/server.pem",
            "certs/private.key",
            ".firebase/hosting.cache",
            "gcp/env.prod",
            "gcp/env.staging",
            "debug.log",
        ],
    )
    def test_forbidden_files_detected(self, file_path: str):
        """Verify that secret and ignored files are detected as forbidden."""
        assert is_forbidden_file(file_path) is True, f"File {file_path} should be forbidden"

    @pytest.mark.parametrize(
        "file_path",
        [
            ".env.example",
            ".env.dev.example",
            "frontend/.env.example",
            "frontend/.env.development",
            "frontend/.env.staging",
            "frontend/.env.production",
            "scripts/daily_git_sync.py",
            "app/main.py",
            "README.md",
            "docs/agent_memory/DEVOPS_STATE.md",
        ],
    )
    def test_allowed_files_permitted(self, file_path: str):
        """Verify that benign files and example templates are permitted."""
        assert is_forbidden_file(file_path) is False, f"File {file_path} should be permitted"

    def test_target_sync_branch_not_protected(self):
        """Enforce that TARGET_SYNC_BRANCH is isolated and not in protected branches."""
        assert TARGET_SYNC_BRANCH == "daily-sync"
        assert TARGET_SYNC_BRANCH not in PROTECTED_BRANCHES
        for branch in ["main", "master", "staging", "demo", "prod", "production"]:
            assert branch in PROTECTED_BRANCHES

    def test_dry_run_execution(self):
        """Verify that dry-run mode executes cleanly without modifying repository state."""
        success, msg = perform_daily_git_sync(dry_run=True)
        assert success is True
        assert "Dry-run" in msg

    @patch("daily_git_sync.get_staged_files")
    @patch("daily_git_sync.run_cmd")
    def test_sanitize_staging_index_unstages_forbidden(self, mock_run_cmd, mock_get_staged):
        """Verify sanitize_staging_index identifies and unstages forbidden files."""
        mock_get_staged.return_value = [
            "scripts/daily_git_sync.py",
            ".env.local",
            "airs_dev.db",
            "frontend/src/App.tsx",
            "scratch/notes.txt",
        ]
        mock_run_cmd.return_value = MagicMock(returncode=0)

        unstaged = sanitize_staging_index(Path("/fake/repo"))
        assert len(unstaged) == 3
        assert ".env.local" in unstaged
        assert "airs_dev.db" in unstaged
        assert "scratch/notes.txt" in unstaged

        # Verify git reset was called for forbidden files
        assert mock_run_cmd.call_count == 3
        calls = [c[0][0] for c in mock_run_cmd.call_args_list]
        assert ["git", "reset", "HEAD", ".env.local"] in calls
        assert ["git", "reset", "HEAD", "airs_dev.db"] in calls
        assert ["git", "reset", "HEAD", "scratch/notes.txt"] in calls
