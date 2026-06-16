# AIRS - Frontend Deployment Script (PowerShell)
# Builds and deploys the frontend to specific Firebase Hosting targets

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("marketing", "demo", "staging")]
    [string]$Target
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AIRS - Frontend Deployment ($Target)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if firebase is installed
try {
    $null = Get-Command firebase -ErrorAction Stop
} catch {
    Write-Host "ERROR: firebase CLI not found. Please install firebase-tools globally via npm." -ForegroundColor Red
    exit 1
}

# Change directory to frontend
$FrontendDir = Join-Path $ProjectRoot "frontend"
Set-Location $FrontendDir

# ── Branch guardrail: only main or staging branch may deploy to marketing or demo ──
if ($Target -eq "marketing" -or $Target -eq "demo") {
    try {
        $currentBranch = (git rev-parse --abbrev-ref HEAD 2>$null).Trim()
    } catch {
        $currentBranch = "unknown"
    }
    if ($currentBranch -and $currentBranch -ne "main" -and $currentBranch -ne "staging") {
        Write-Host ""
        Write-Host "CRITICAL: Deploying to target '$Target' is only allowed from the 'main' or 'staging' branch." -ForegroundColor Red
        Write-Host "Current branch: $currentBranch" -ForegroundColor Red
        Write-Host "Merge your changes to 'main' first, then re-run." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Step 1: Building frontend for target '$Target'..." -ForegroundColor Green
# Demo environment lock removed

if ($Target -eq "marketing") {
    npm run build:production
} elseif ($Target -eq "demo") {
    npm run build:demo
} elseif ($Target -eq "staging") {
    npm run build:staging
}

Write-Host ""
Write-Host "Step 2: Deploying to Firebase Hosting target '$Target'..." -ForegroundColor Green
Set-Location $ProjectRoot
firebase deploy --only "hosting:$Target"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Frontend deployment for '$Target' completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
