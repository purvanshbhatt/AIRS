# AIRS - Cloud Run Deployment Script (PowerShell)
# Deploys the AIRS API to Google Cloud Run
# Defaults to STAGING — use -Prod flag for production deployment

param(
    [string]$Region = "us-central1",
    [switch]$Prod,
    [switch]$AllowUnauthenticated = $true,
    [string]$CloudSqlInstance = $env:CLOUDSQL_INSTANCE  # e.g., "project:region:instance"
)

$ErrorActionPreference = "Stop"

# Determine target environment
if ($Prod) {
    $ServiceName = "airs-api"
    $EnvFile = "gcp/env.prod.yaml"
    $envLabel = "PRODUCTION"

    # ── Branch guardrail: only main branch may deploy to prod ─────────
    try {
        $currentBranch = (git rev-parse --abbrev-ref HEAD 2>$null).Trim()
    } catch {
        $currentBranch = "unknown"
    }
    if ($currentBranch -and $currentBranch -ne "main") {
        Write-Host ""
        Write-Host "CRITICAL: Production deployments are only allowed from the 'main' branch." -ForegroundColor Red
        Write-Host "Current branch: $currentBranch" -ForegroundColor Red
        Write-Host "Merge your changes to 'main' first, then re-run." -ForegroundColor Yellow
        exit 1
    }

    Write-Host ""
    Write-Host "WARNING: You are deploying to PRODUCTION!" -ForegroundColor Red
    Write-Host "This will affect the live demo at v0.5-demo-locked." -ForegroundColor Red
    $confirm = Read-Host "Type 'yes' to continue"
    if ($confirm -ne "yes") {
        Write-Host "Aborted." -ForegroundColor Yellow
        exit 0
    }
} else {
    $ServiceName = "airs-api-staging"
    $EnvFile = "gcp/env.staging.yaml"
    $envLabel = "STAGING"
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AIRS - Cloud Run Deployment ($envLabel)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if gcloud is installed
try {
    $null = Get-Command gcloud -ErrorAction Stop
} catch {
    Write-Host "ERROR: gcloud CLI not found. Please install Google Cloud SDK." -ForegroundColor Red
    exit 1
}

# Check if env file exists
$EnvFilePath = Join-Path $PSScriptRoot ".." $EnvFile
if (-not (Test-Path $EnvFilePath)) {
    Write-Host "ERROR: Environment file not found: $EnvFile" -ForegroundColor Red
    exit 1
}

Write-Host "Using env vars file: $EnvFile" -ForegroundColor Green
Write-Host ""
Write-Host "Deployment Configuration:" -ForegroundColor Yellow
Write-Host "  Service:  $ServiceName"
Write-Host "  Region:   $Region"
Write-Host "  Env file: $EnvFile"
if ($CloudSqlInstance) {
    Write-Host "  Cloud SQL: $CloudSqlInstance" -ForegroundColor Cyan
}
Write-Host ""

# Build gcloud command — use the YAML env-vars-file directly
$deployArgs = @(
    "run", "deploy", $ServiceName,
    "--source", ".",
    "--region", $Region,
    "--memory", "512Mi",
    "--cpu", "1",
    "--min-instances", "0",
    "--max-instances", "10",
    "--timeout", "120"
)

# Add Cloud SQL connection if specified
if ($CloudSqlInstance) {
    $deployArgs += "--add-cloudsql-instances"
    $deployArgs += $CloudSqlInstance
    Write-Host "Attaching Cloud SQL instance: $CloudSqlInstance" -ForegroundColor Green
}

# Use env-vars-file for proper YAML env config
$deployArgs += "--env-vars-file"
$deployArgs += $EnvFilePath

if ($AllowUnauthenticated) {
    $deployArgs += "--allow-unauthenticated"
}

Write-Host "Deploying to Cloud Run..." -ForegroundColor Green
Write-Host ""

# Run deployment
& gcloud @deployArgs

$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Deployment failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment successful!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get and display service URL
Write-Host "Fetching service URL..." -ForegroundColor Green
$serviceUrl = gcloud run services describe $ServiceName --region $Region --format "value(status.url)"

Write-Host ""
Write-Host "Service URL:" -ForegroundColor Yellow
Write-Host "  $serviceUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "Health check:" -ForegroundColor Yellow
Write-Host "  $serviceUrl/health" -ForegroundColor Cyan
Write-Host ""
