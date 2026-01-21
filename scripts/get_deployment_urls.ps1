<#
.SYNOPSIS
    Prints the active deployment URLs for AIRS (Cloud Run backend + Firebase Hosting frontend).
    
.DESCRIPTION
    Helper script for operators to discover real origins before updating CORS configuration.
    
.EXAMPLE
    .\scripts\get_deployment_urls.ps1
#>

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AIRS Deployment URLs" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- Backend: Cloud Run ---
Write-Host "[Backend - Cloud Run]" -ForegroundColor Yellow

$cloudRunUrl = $null

# Try gcloud first
try {
    $cloudRunUrl = gcloud run services describe airs-api --region us-central1 --format="value(status.url)" 2>$null
    if ($cloudRunUrl) {
        Write-Host "  Service URL: $cloudRunUrl" -ForegroundColor Green
    }
} catch {
    # gcloud not available or failed
}

if (-not $cloudRunUrl) {
    # Fallback: check env.prod.yaml for project ID
    $envFile = Join-Path $PSScriptRoot "..\gcp\env.prod.yaml"
    if (Test-Path $envFile) {
        $content = Get-Content $envFile -Raw
        if ($content -match "GCP_PROJECT_ID:\s*[`"']?([^`"'\s]+)") {
            $projectId = $Matches[1]
            Write-Host "  (gcloud unavailable - using project ID from env.prod.yaml)" -ForegroundColor DarkGray
            Write-Host "  Estimated URL: https://airs-api-<project-number>.us-central1.run.app" -ForegroundColor DarkYellow
            Write-Host "  Project ID: $projectId" -ForegroundColor DarkGray
        }
    } else {
        Write-Host "  (Could not determine - run 'gcloud run services list' manually)" -ForegroundColor Red
    }
}

Write-Host ""

# --- Frontend: Firebase Hosting ---
Write-Host "[Frontend - Firebase Hosting]" -ForegroundColor Yellow

$firebaseRc = Join-Path $PSScriptRoot "..\.firebaserc"
$firebaseJson = Join-Path $PSScriptRoot "..\firebase.json"

$projectId = $null
$sites = @()

# Check .firebaserc for project and hosting targets
if (Test-Path $firebaseRc) {
    $rcContent = Get-Content $firebaseRc -Raw | ConvertFrom-Json -ErrorAction SilentlyContinue
    
    if ($rcContent.projects.default) {
        $projectId = $rcContent.projects.default
    }
    
    # Check for hosting targets
    if ($rcContent.targets -and $rcContent.targets.$projectId -and $rcContent.targets.$projectId.hosting) {
        $hostingTargets = $rcContent.targets.$projectId.hosting
        foreach ($target in $hostingTargets.PSObject.Properties) {
            $sites += $target.Value
        }
    }
}

if ($projectId) {
    Write-Host "  Firebase Project: $projectId" -ForegroundColor DarkGray
    Write-Host ""
    
    if ($sites.Count -gt 0) {
        Write-Host "  Hosting Sites:" -ForegroundColor Green
        foreach ($site in $sites) {
            Write-Host "    - https://$site.web.app" -ForegroundColor Green
            Write-Host "    - https://$site.firebaseapp.com" -ForegroundColor Green
        }
    } else {
        # Default site URLs based on project ID
        Write-Host "  Default Site URLs:" -ForegroundColor Green
        Write-Host "    - https://$projectId.web.app" -ForegroundColor Green
        Write-Host "    - https://$projectId.firebaseapp.com" -ForegroundColor Green
    }
} else {
    Write-Host "  (No .firebaserc found - Firebase Hosting not configured)" -ForegroundColor DarkGray
}

Write-Host ""

# --- CORS Origins Summary ---
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Suggested CORS Origins" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$origins = @()

if ($cloudRunUrl) {
    # Don't include backend in CORS - it's the server
}

if ($sites.Count -gt 0) {
    foreach ($site in $sites) {
        $origins += "https://$site.web.app"
        $origins += "https://$site.firebaseapp.com"
    }
} elseif ($projectId) {
    $origins += "https://$projectId.web.app"
    $origins += "https://$projectId.firebaseapp.com"
}

$origins += "http://localhost:5173"

if ($origins.Count -gt 0) {
    Write-Host "Copy this value for CORS_ALLOW_ORIGINS:" -ForegroundColor Yellow
    Write-Host ""
    $corsValue = $origins -join ","
    Write-Host "  $corsValue" -ForegroundColor White
    Write-Host ""
}

Write-Host "----------------------------------------" -ForegroundColor DarkGray
Write-Host "To update CORS in Cloud Run:" -ForegroundColor DarkGray
Write-Host "  1. Edit gcp/env.prod.yaml" -ForegroundColor DarkGray
Write-Host "  2. Run: gcloud run deploy airs-api --source . --region us-central1 --allow-unauthenticated --env-vars-file gcp/env.prod.yaml" -ForegroundColor DarkGray
Write-Host ""
