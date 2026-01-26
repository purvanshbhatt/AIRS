<#
.SYNOPSIS
    Splits the AIRS repository into public (AIRS-showcase) and private (AIRS-core) repositories.

.DESCRIPTION
    This script copies files from the AIRS repository into two separate folder structures:
    - AIRS-showcase: Public repository for demos and credibility
    - AIRS-core: Private repository with backend IP

.PARAMETER OutputDir
    The directory where the split repositories will be created. Defaults to parent of AIRS.

.EXAMPLE
    .\scripts\split_repos.ps1
    .\scripts\split_repos.ps1 -OutputDir "C:\repos"
#>

param(
    [string]$OutputDir = (Split-Path -Parent $PSScriptRoot | Split-Path -Parent)
)

$ErrorActionPreference = "Stop"

# Source directory (AIRS repo root)
$SourceDir = Split-Path -Parent $PSScriptRoot

# Output directories
$ShowcaseDir = Join-Path $OutputDir "AIRS-showcase"
$CoreDir = Join-Path $OutputDir "AIRS-core"

Write-Host "=== AIRS Repository Split ===" -ForegroundColor Cyan
Write-Host "Source: $SourceDir"
Write-Host "Showcase output: $ShowcaseDir"
Write-Host "Core output: $CoreDir"
Write-Host ""

# Confirm before proceeding
$confirm = Read-Host "This will create/overwrite the output directories. Continue? (y/N)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit 0
}

# Helper function to copy directory
function Copy-Directory {
    param(
        [string]$Source,
        [string]$Destination,
        [string[]]$Exclude = @()
    )
    
    if (Test-Path $Source) {
        # Create destination if it doesn't exist
        if (-not (Test-Path $Destination)) {
            New-Item -ItemType Directory -Path $Destination -Force | Out-Null
        }
        
        # Copy with exclusions
        $items = Get-ChildItem -Path $Source -Recurse -Force
        foreach ($item in $items) {
            $relativePath = $item.FullName.Substring($Source.Length + 1)
            $skip = $false
            
            foreach ($pattern in $Exclude) {
                if ($relativePath -like $pattern) {
                    $skip = $true
                    break
                }
            }
            
            if (-not $skip) {
                $destPath = Join-Path $Destination $relativePath
                if ($item.PSIsContainer) {
                    if (-not (Test-Path $destPath)) {
                        New-Item -ItemType Directory -Path $destPath -Force | Out-Null
                    }
                } else {
                    $destDir = Split-Path -Parent $destPath
                    if (-not (Test-Path $destDir)) {
                        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                    }
                    Copy-Item -Path $item.FullName -Destination $destPath -Force
                }
            }
        }
        Write-Host "  Copied: $Source" -ForegroundColor Green
    } else {
        Write-Host "  Skipped (not found): $Source" -ForegroundColor Yellow
    }
}

# Helper function to copy single file
function Copy-SingleFile {
    param(
        [string]$Source,
        [string]$Destination
    )
    
    if (Test-Path $Source) {
        $destDir = Split-Path -Parent $Destination
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        Copy-Item -Path $Source -Destination $Destination -Force
        Write-Host "  Copied: $(Split-Path -Leaf $Source)" -ForegroundColor Green
    } else {
        Write-Host "  Skipped (not found): $Source" -ForegroundColor Yellow
    }
}

# =============================================================================
# Create AIRS-showcase (Public Repository)
# =============================================================================
Write-Host ""
Write-Host "Creating AIRS-showcase (public)..." -ForegroundColor Cyan

# Clean and create directory
if (Test-Path $ShowcaseDir) {
    Remove-Item -Path $ShowcaseDir -Recurse -Force
}
New-Item -ItemType Directory -Path $ShowcaseDir -Force | Out-Null

# Copy frontend (exclude node_modules, dist, .env files)
Write-Host "  Copying frontend..."
Copy-Directory -Source (Join-Path $SourceDir "frontend") -Destination (Join-Path $ShowcaseDir "frontend") -Exclude @(
    "node_modules*",
    "dist*",
    ".env",
    ".env.local",
    ".env.*.local"
)

# Copy docs
Write-Host "  Copying docs..."
Copy-Directory -Source (Join-Path $SourceDir "docs") -Destination (Join-Path $ShowcaseDir "docs")

# Copy openapi (redacted)
Write-Host "  Copying openapi..."
Copy-Directory -Source (Join-Path $SourceDir "openapi") -Destination (Join-Path $ShowcaseDir "openapi")

# Copy sample_reports
Write-Host "  Copying sample_reports..."
Copy-Directory -Source (Join-Path $SourceDir "sample_reports") -Destination (Join-Path $ShowcaseDir "sample_reports")

# Copy showcase README
Copy-SingleFile -Source (Join-Path $SourceDir "docs\README.showcase.md") -Destination (Join-Path $ShowcaseDir "README.md")

# Create assets directory placeholder
$assetsDir = Join-Path $ShowcaseDir "docs\assets"
if (-not (Test-Path $assetsDir)) {
    New-Item -ItemType Directory -Path $assetsDir -Force | Out-Null
}
"# Placeholder for logo and screenshots" | Out-File (Join-Path $assetsDir ".gitkeep")

# Create LICENSE file
@"
MIT License

Copyright (c) 2025 Purvansh Bhatt

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"@ | Out-File (Join-Path $ShowcaseDir "LICENSE") -Encoding utf8

# Create .gitignore for showcase
@"
# Dependencies
node_modules/
.pnpm-store/

# Build outputs
dist/
build/

# Environment files
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Logs
*.log
"@ | Out-File (Join-Path $ShowcaseDir ".gitignore") -Encoding utf8

Write-Host "AIRS-showcase created!" -ForegroundColor Green

# =============================================================================
# Create AIRS-core (Private Repository)
# =============================================================================
Write-Host ""
Write-Host "Creating AIRS-core (private)..." -ForegroundColor Cyan

# Clean and create directory
if (Test-Path $CoreDir) {
    Remove-Item -Path $CoreDir -Recurse -Force
}
New-Item -ItemType Directory -Path $CoreDir -Force | Out-Null

# Copy app (backend)
Write-Host "  Copying app..."
Copy-Directory -Source (Join-Path $SourceDir "app") -Destination (Join-Path $CoreDir "app") -Exclude @(
    "__pycache__*",
    "*.pyc"
)

# Copy alembic (migrations)
Write-Host "  Copying alembic..."
Copy-Directory -Source (Join-Path $SourceDir "alembic") -Destination (Join-Path $CoreDir "alembic") -Exclude @(
    "__pycache__*"
)

# Copy tests
Write-Host "  Copying tests..."
Copy-Directory -Source (Join-Path $SourceDir "tests") -Destination (Join-Path $CoreDir "tests") -Exclude @(
    "__pycache__*",
    "*.pyc"
)

# Copy scripts
Write-Host "  Copying scripts..."
Copy-Directory -Source (Join-Path $SourceDir "scripts") -Destination (Join-Path $CoreDir "scripts")

# Copy gcp config
Write-Host "  Copying gcp..."
Copy-Directory -Source (Join-Path $SourceDir "gcp") -Destination (Join-Path $CoreDir "gcp") -Exclude @(
    "env.prod"
)

# Copy individual files
Write-Host "  Copying config files..."
Copy-SingleFile -Source (Join-Path $SourceDir "requirements.txt") -Destination (Join-Path $CoreDir "requirements.txt")
Copy-SingleFile -Source (Join-Path $SourceDir "alembic.ini") -Destination (Join-Path $CoreDir "alembic.ini")
Copy-SingleFile -Source (Join-Path $SourceDir "Makefile") -Destination (Join-Path $CoreDir "Makefile")
Copy-SingleFile -Source (Join-Path $SourceDir "Dockerfile") -Destination (Join-Path $CoreDir "Dockerfile")
Copy-SingleFile -Source (Join-Path $SourceDir "Procfile") -Destination (Join-Path $CoreDir "Procfile")
Copy-SingleFile -Source (Join-Path $SourceDir "gunicorn.conf.py") -Destination (Join-Path $CoreDir "gunicorn.conf.py")
Copy-SingleFile -Source (Join-Path $SourceDir ".env.example") -Destination (Join-Path $CoreDir ".env.example")

# Create private README
@"
# AIRS-core (Private)

Backend implementation for AIRS (AI Incident Readiness Score).

## Structure

- ``app/`` - FastAPI application
- ``alembic/`` - Database migrations
- ``tests/`` - Test suite
- ``scripts/`` - Deployment scripts
- ``gcp/`` - Cloud Run configuration

## Development

``````bash
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start dev server
make dev
``````

## Deployment

See ``scripts/deploy_cloud_run.ps1`` for Cloud Run deployment.

## Testing

``````bash
make test
``````
"@ | Out-File (Join-Path $CoreDir "README.md") -Encoding utf8

# Create .gitignore for core
@"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.venv/

# Environment
.env
.env.local
gcp/env.prod

# Database
*.db
*.sqlite

# IDE
.vscode/
.idea/

# Testing
.pytest_cache/
.coverage
htmlcov/

# Build
dist/
build/
*.egg-info/

# Logs
*.log

# OS
.DS_Store
Thumbs.db

# Generated
generated_reports/
test_reports/
"@ | Out-File (Join-Path $CoreDir ".gitignore") -Encoding utf8

Write-Host "AIRS-core created!" -ForegroundColor Green

# =============================================================================
# Summary
# =============================================================================
Write-Host ""
Write-Host "=== Split Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "AIRS-showcase (public): $ShowcaseDir" -ForegroundColor White
Write-Host "  - frontend/"
Write-Host "  - docs/ (overview, methodology, frameworks, security, privacy)"
Write-Host "  - openapi/ (redacted spec)"
Write-Host "  - sample_reports/"
Write-Host "  - README.md (buyer-ready)"
Write-Host ""
Write-Host "AIRS-core (private): $CoreDir" -ForegroundColor White
Write-Host "  - app/ (backend)"
Write-Host "  - alembic/ (migrations)"
Write-Host "  - tests/"
Write-Host "  - scripts/"
Write-Host "  - gcp/"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Add screenshots to $ShowcaseDir\docs\assets\"
Write-Host "  2. Initialize git repos:"
Write-Host "     cd $ShowcaseDir && git init && git add . && git commit -m 'Initial commit'"
Write-Host "     cd $CoreDir && git init && git add . && git commit -m 'Initial commit'"
Write-Host "  3. Create GitHub repos and push"
Write-Host ""
