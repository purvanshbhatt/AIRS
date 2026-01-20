# AIRS - GCP Bootstrap Script (PowerShell)
# Sets up GCP project, enables required APIs, and configures defaults

param(
    [string]$ProjectId = "gen-lang-client-0384513977",
    [string]$Region = "us-central1"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AIRS - GCP Bootstrap" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if gcloud is installed
try {
    $null = Get-Command gcloud -ErrorAction Stop
} catch {
    Write-Host "ERROR: gcloud CLI not found. Please install Google Cloud SDK." -ForegroundColor Red
    Write-Host "https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Set project
Write-Host "Setting project to: $ProjectId" -ForegroundColor Green
gcloud config set project $ProjectId

# Set default region
Write-Host "Setting default region to: $Region" -ForegroundColor Green
gcloud config set run/region $Region

# Set default platform to managed
Write-Host "Setting default platform to: managed" -ForegroundColor Green
gcloud config set run/platform managed

# Enable required APIs
Write-Host ""
Write-Host "Enabling required APIs..." -ForegroundColor Green

$apis = @(
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com"
)

foreach ($api in $apis) {
    Write-Host "  Enabling $api..." -ForegroundColor Yellow
    gcloud services enable $api --quiet
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Bootstrap complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project:  $ProjectId"
Write-Host "Region:   $Region"
Write-Host "Platform: managed"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Copy gcp/env.prod.example to gcp/env.prod"
Write-Host "  2. Fill in your production values"
Write-Host "  3. Run: .\scripts\deploy_cloud_run.ps1"
