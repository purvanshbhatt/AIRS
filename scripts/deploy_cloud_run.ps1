# AIRS - Cloud Run Deployment Script (PowerShell)
# Deploys the AIRS API to Google Cloud Run
# Defaults to STAGING — use -Prod flag for production deployment

param(
    [string]$Region = "us-central1",
    [switch]$Prod,
    [switch]$AllowUnauthenticated = $true,
    [string]$CloudSqlInstance = $env:CLOUDSQL_INSTANCE,  # e.g., "project:region:instance"
    [string]$SetSecrets = "",
    [string]$Target = ""
)

$ErrorActionPreference = "Stop"

# Handle Target shortcut parameter
if ($Target) {
    if ($Target -eq "staging") {
        $Prod = $false
    } elseif ($Target -eq "demo" -or $Target -eq "production") {
        $Prod = $true
    } elseif ($Target -eq "marketing") {
        Write-Host "INFO: Marketing target is frontend-only. No Cloud Run backend service is associated with marketing." -ForegroundColor Green
        exit 0
    } else {
        Write-Host "ERROR: Invalid target: $Target. Must be one of: staging, demo, marketing." -ForegroundColor Red
        exit 1
    }
}

# Determine target environment
if ($Prod) {
    $ServiceName = "airs-api"
    $EnvFile = "gcp/env.demo.yaml" # Demands env.demo.yaml for production deployment/demo domain mapping
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
    Write-Host "This will affect the live demo at resilai.org / demo.resilai.org." -ForegroundColor Red
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
$EnvFilePath = Join-Path (Join-Path $PSScriptRoot "..") $EnvFile
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
if ($SetSecrets) {
    Write-Host "  Secret bindings: configured" -ForegroundColor Cyan
}
Write-Host ""

if (-not $SetSecrets) {
    Write-Host "WARNING: -SetSecrets not provided. ENCRYPTION_SECRET must already be set on the Cloud Run service." -ForegroundColor Yellow
}
elseif ($SetSecrets -notmatch "ENCRYPTION_SECRET=") {
    Write-Host "WARNING: -SetSecrets does not include ENCRYPTION_SECRET. Firestore encryption may be disabled at runtime." -ForegroundColor Yellow
}

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

if ($SetSecrets) {
    $deployArgs += "--set-secrets"
    $deployArgs += $SetSecrets
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
