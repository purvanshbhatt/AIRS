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

Write-Host "Step 1: Building frontend for target '$Target'..." -ForegroundColor Green
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
