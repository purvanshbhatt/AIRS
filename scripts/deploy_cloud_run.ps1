# AIRS - Cloud Run Deployment Script (PowerShell)
# Deploys the AIRS API to Google Cloud Run

param(
    [string]$ServiceName = "airs-api",
    [string]$Region = "us-central1",
    [string]$EnvFile = "gcp/env.prod",
    [switch]$AllowUnauthenticated = $true,
    [string]$CloudSqlInstance = $env:CLOUDSQL_INSTANCE  # e.g., "project:region:instance"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AIRS - Cloud Run Deployment" -ForegroundColor Cyan
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
    Write-Host "Please copy gcp/env.prod.example to gcp/env.prod and fill in values." -ForegroundColor Yellow
    exit 1
}

# Read environment variables from file
Write-Host "Reading environment variables from: $EnvFile" -ForegroundColor Green
$envVars = @()
Get-Content $EnvFilePath | ForEach-Object {
    $line = $_.Trim()
    # Skip empty lines and comments
    if ($line -and -not $line.StartsWith("#")) {
        $envVars += $line
    }
}

# Build env vars string for gcloud
$envVarsString = $envVars -join ","

Write-Host ""
Write-Host "Deployment Configuration:" -ForegroundColor Yellow
Write-Host "  Service:  $ServiceName"
Write-Host "  Region:   $Region"
Write-Host "  Env vars: $($envVars.Count) variables loaded"
if ($CloudSqlInstance) {
    Write-Host "  Cloud SQL: $CloudSqlInstance" -ForegroundColor Cyan
}
Write-Host ""

# Build gcloud command
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

if ($envVarsString) {
    $deployArgs += "--set-env-vars"
    $deployArgs += $envVarsString
}

if ($AllowUnauthenticated) {
    $deployArgs += "--allow-unauthenticated"
}

Write-Host "Deploying to Cloud Run..." -ForegroundColor Green
Write-Host ""

# Run deployment
& gcloud @deployArgs

if ($LASTEXITCODE -ne 0) {
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
