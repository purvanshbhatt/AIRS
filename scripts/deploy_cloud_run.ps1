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
$envVars = @{}
Get-Content $EnvFilePath | ForEach-Object {
    $line = $_.Trim()
    # Skip empty lines and comments
    if ($line -and -not $line.StartsWith("#")) {
        $parts = $line -split "=", 2
        if ($parts.Count -eq 2) {
            $envVars[$parts[0]] = $parts[1]
        }
    }
}

# Build env vars string for gcloud (each key=value pair separately quoted)
$envVarsList = @()
foreach ($key in $envVars.Keys) {
    $envVarsList += "$key=$($envVars[$key])"
}
$envVarsString = $envVarsList -join ","

Write-Host ""
Write-Host "Deployment Configuration:" -ForegroundColor Yellow
Write-Host "  Service:  $ServiceName"
Write-Host "  Region:   $Region"
Write-Host "  Env vars: $($envVars.Count) variables loaded"
if ($CloudSqlInstance) {
    Write-Host "  Cloud SQL: $CloudSqlInstance" -ForegroundColor Cyan
}
Write-Host ""

# Create temp YAML env file for gcloud (handles special characters properly)
$tempEnvFile = [System.IO.Path]::GetTempFileName() -replace '\.tmp$', '.yaml'
$yamlContent = ""
foreach ($key in $envVars.Keys) {
    $value = $envVars[$key]
    # Quote values with special characters
    $yamlContent += "$key`: `"$value`"`n"
}
Set-Content -Path $tempEnvFile -Value $yamlContent -NoNewline

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

# Use env-vars-file for proper escaping of special characters
if ($tempEnvFile) {
    $deployArgs += "--env-vars-file"
    $deployArgs += $tempEnvFile
}

if ($AllowUnauthenticated) {
    $deployArgs += "--allow-unauthenticated"
}

Write-Host "Deploying to Cloud Run..." -ForegroundColor Green
Write-Host ""

# Run deployment
& gcloud @deployArgs

$exitCode = $LASTEXITCODE

# Cleanup temp file
if ($tempEnvFile -and (Test-Path $tempEnvFile)) {
    Remove-Item $tempEnvFile -Force
}

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
