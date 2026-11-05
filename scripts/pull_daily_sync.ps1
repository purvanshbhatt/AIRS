# =============================================================================
# ResilAI - Pull Daily Sync Script (PowerShell)
# Single-command synchronization for developers resuming work on a new device/machine.
# Fetches the isolated 'daily-sync' snapshot from remote and offers interactive
# or flag-driven checkout/rebase options.
# =============================================================================

[CmdletBinding()]
param (
    [Parameter(Mandatory = $false)]
    [switch]$Checkout,

    [Parameter(Mandatory = $false)]
    [Alias("b")]
    [string]$NewBranch,

    [Parameter(Mandatory = $false)]
    [switch]$Rebase,

    [Parameter(Mandatory = $false)]
    [switch]$Merge,

    [Parameter(Mandatory = $false)]
    [switch]$DryRun,

    [Parameter(Mandatory = $false)]
    [Alias("f")]
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$SYNC_BRANCH = "daily-sync"
$REMOTE = "origin"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "ResilAI - Daily Git Sync Pull Utility (PowerShell)" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""

# Validate git repository
try {
    $isGit = git rev-parse --is-inside-work-tree 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Not inside a git repository."
        exit 1
    }
} catch {
    Write-Error "Git command failed or git is not installed."
    exit 1
}

$currentBranch = (git rev-parse --abbrev-ref HEAD 2>$null).Trim()
Write-Host "Current active branch: " -NoNewline
Write-Host $currentBranch -ForegroundColor Yellow

# Verify remote exists
$remotes = git remote
if (-not ($remotes -contains $REMOTE)) {
    Write-Error "Remote '$REMOTE' not found in this repository."
    exit 1
}

Write-Host "Fetching latest '$SYNC_BRANCH' snapshot from remote '$REMOTE'..." -ForegroundColor Gray
git fetch $REMOTE $SYNC_BRANCH 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Branch '$SYNC_BRANCH' does not exist on remote '$REMOTE'. Ensure daily_git_sync.py has executed at least once."
    exit 1
}

$latestCommit = (git log -1 --format="%h - %s (%cr) <%an>" "$REMOTE/$SYNC_BRANCH").Trim()
$latestTimestamp = (git log -1 --format="%cd" --date=iso "$REMOTE/$SYNC_BRANCH").Trim()

Write-Host "✓ Successfully fetched '$SYNC_BRANCH' from $REMOTE" -ForegroundColor Green
Write-Host "Latest Snapshot Commit: $latestCommit" -ForegroundColor White
Write-Host "Snapshot Date:          $latestTimestamp" -ForegroundColor White
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY-RUN] Showing latest commit details:" -ForegroundColor Yellow
    git log -1 --stat "$REMOTE/$SYNC_BRANCH"
    Write-Host "[DRY-RUN] No branch changes applied." -ForegroundColor Yellow
    exit 0
}

# Determine Action
$action = ""
if ($Checkout) {
    $action = "checkout"
} elseif (-not [string]::IsNullOrWhiteSpace($NewBranch)) {
    $action = "new-branch"
} elseif ($Rebase) {
    $action = "rebase"
} elseif ($Merge) {
    $action = "merge"
}

if ([string]::IsNullOrWhiteSpace($action)) {
    if ($Host.UI.RawUI.KeyAvailable -or [Environment]::UserInteractive) {
        Write-Host "Select how to apply the daily snapshot:" -ForegroundColor White
        Write-Host "  1) Checkout '$SYNC_BRANCH' directly" -ForegroundColor Cyan
        Write-Host "  2) Create a new branch from '$SYNC_BRANCH' (Recommended for new work)" -ForegroundColor Cyan
        Write-Host "  3) Rebase current branch ('$currentBranch') onto '$SYNC_BRANCH'" -ForegroundColor Cyan
        Write-Host "  4) Merge '$SYNC_BRANCH' into current branch ('$currentBranch')" -ForegroundColor Cyan
        Write-Host "  5) Exit without changes" -ForegroundColor Cyan
        Write-Host ""
        
        $choice = Read-Host "Select option [1-5] (default: 2)"
        if ([string]::IsNullOrWhiteSpace($choice)) { $choice = "2" }

        switch ($choice) {
            "1" { $action = "checkout" }
            "2" {
                $action = "new-branch"
                $NewBranch = Read-Host "Enter new branch name (e.g. feature/resume-sync)"
                if ([string]::IsNullOrWhiteSpace($NewBranch)) {
                    $dateStr = Get-Date -Format "yyyyMMdd"
                    $NewBranch = "feature/resumed-sync-$dateStr"
                    Write-Host "Defaulting branch name to: $NewBranch" -ForegroundColor Gray
                }
            }
            "3" { $action = "rebase" }
            "4" { $action = "merge" }
            "5" {
                Write-Host "Exiting without applying changes." -ForegroundColor Gray
                exit 0
            }
            Default {
                Write-Error "Invalid selection. Aborting."
                exit 1
            }
        }
    } else {
        $action = "checkout"
    }
}

# Execute Action
switch ($action) {
    "checkout" {
        Write-Host "Checking out '$SYNC_BRANCH'..." -ForegroundColor Gray
        git checkout "$SYNC_BRANCH" 2>$null
        if ($LASTEXITCODE -eq 0) {
            git reset --hard "$REMOTE/$SYNC_BRANCH"
        } else {
            git checkout -b "$SYNC_BRANCH" "$REMOTE/$SYNC_BRANCH"
        }
        Write-Host "✓ Checked out '$SYNC_BRANCH'. Workspace updated to latest snapshot." -ForegroundColor Green
    }
    "new-branch" {
        Write-Host "Creating and checking out branch '$NewBranch' based on '$REMOTE/$SYNC_BRANCH'..." -ForegroundColor Gray
        if ($Force) {
            git checkout -B "$NewBranch" "$REMOTE/$SYNC_BRANCH"
        } else {
            git checkout -b "$NewBranch" "$REMOTE/$SYNC_BRANCH"
        }
        Write-Host "✓ Created and active on branch '$NewBranch' based on latest snapshot." -ForegroundColor Green
    }
    "rebase" {
        Write-Host "Rebasing current branch '$currentBranch' onto '$REMOTE/$SYNC_BRANCH'..." -ForegroundColor Gray
        git rebase "$REMOTE/$SYNC_BRANCH"
        Write-Host "✓ Successfully rebased '$currentBranch' onto latest daily snapshot." -ForegroundColor Green
    }
    "merge" {
        Write-Host "Merging '$REMOTE/$SYNC_BRANCH' into '$currentBranch'..." -ForegroundColor Gray
        git merge "$REMOTE/$SYNC_BRANCH" -m "chore(sync): merge daily-sync snapshot into $currentBranch"
        Write-Host "✓ Successfully merged latest daily snapshot into '$currentBranch'." -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Daily sync recovery complete! You may now resume development." -ForegroundColor Green
