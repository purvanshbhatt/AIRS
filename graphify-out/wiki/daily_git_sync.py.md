# daily_git_sync.py

> 54 nodes · cohesion 0.06

## Key Concepts

- **daily_git_sync.py** (14 connections) — `scripts/daily_git_sync.py`
- **perform_daily_git_sync()** (12 connections) — `scripts/daily_git_sync.py`
- **run_cmd()** (10 connections) — `scripts/daily_git_sync.py`
- **Path** (8 connections)
- **sanitize_staging_index()** (8 connections) — `scripts/daily_git_sync.py`
- **TestDailyBackupSyncWorkflow** (7 connections) — `tests/test_daily_git_sync.py`
- **TestDailyGitSyncSecurity** (7 connections) — `tests/test_daily_git_sync.py`
- **get_staged_files()** (6 connections) — `scripts/daily_git_sync.py`
- **is_forbidden_file()** (6 connections) — `scripts/daily_git_sync.py`
- **get_current_branch()** (5 connections) — `scripts/daily_git_sync.py`
- **get_repo_root()** (5 connections) — `scripts/daily_git_sync.py`
- **antigravity_trigger_handler()** (4 connections) — `scripts/daily_git_sync.py`
- **check_remote_branch_exists()** (4 connections) — `scripts/daily_git_sync.py`
- **GitSyncError** (4 connections) — `scripts/daily_git_sync.py`
- **run_antigravity_scheduler()** (4 connections) — `scripts/daily_git_sync.py`
- **test_daily_git_sync.py** (4 connections) — `tests/test_daily_git_sync.py`
- **.test_allowed_files_permitted()** (4 connections) — `tests/test_daily_git_sync.py`
- **.test_forbidden_files_detected()** (4 connections) — `tests/test_daily_git_sync.py`
- **.test_sanitize_staging_index_unstages_forbidden()** (4 connections) — `tests/test_daily_git_sync.py`
- **main()** (3 connections) — `scripts/daily_git_sync.py`
- **.test_dry_run_execution()** (3 connections) — `tests/test_daily_git_sync.py`
- **fixture** (2 connections)
- **parametrize** (2 connections)
- **.test_workflow_audit_log()** (2 connections) — `tests/test_daily_git_sync.py`
- **.test_workflow_branch_behavior_and_isolation()** (2 connections) — `tests/test_daily_git_sync.py`
- *... and 29 more nodes in this community*

## Relationships

- [app/db/database.py](app-db-database.py.md) (1 shared connections)

## Source Files

- `scripts/daily_git_sync.py`
- `tests/test_daily_git_sync.py`

## Audit Trail

- EXTRACTED: 79 (94%)
- INFERRED: 5 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*