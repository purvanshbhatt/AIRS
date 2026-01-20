# AIRS Makefile
# Cross-platform targets for development, testing, and deployment
# Works on Windows (with make) and Linux/macOS

.PHONY: dev test lint run run-prod deploy-gcp clean install frontend-dev frontend-build frontend-install

# Variables
PYTHON := python
VENV := venv
PROJECT_ID := gen-lang-client-0384513977
REGION := us-central1
SERVICE_NAME := airs
FRONTEND_DIR := frontend

# ============================================
# Backend Development
# ============================================

# Development server with auto-reload
dev:
	$(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	$(PYTHON) -m pytest tests/ -v

# Run linting (ruff preferred, falls back to flake8)
lint:
	$(PYTHON) -m ruff check app/ tests/ --fix || $(PYTHON) -m flake8 app/ tests/ || echo "No linter found. Install with: pip install ruff"

# ============================================
# Frontend Development
# ============================================

# Install frontend dependencies
frontend-install:
	cd $(FRONTEND_DIR) && npm install

# Run frontend dev server
frontend-dev:
	cd $(FRONTEND_DIR) && npm run dev

# Build frontend for production
frontend-build:
	cd $(FRONTEND_DIR) && npm run build

# Run frontend linting
frontend-lint:
	cd $(FRONTEND_DIR) && npm run lint

# ============================================
# Production
# ============================================

# Production server using gunicorn + uvicorn workers
# Use this to test production config locally
run-prod:
	gunicorn -k uvicorn.workers.UvicornWorker app.main:app \
		--bind 0.0.0.0:$${PORT:-8000} \
		--workers 2 \
		--timeout 120 \
		--access-logfile - \
		--error-logfile -

# Simple uvicorn production (single worker)
run:
	$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port $${PORT:-8000}

# ============================================
# Cloud Run Deployment
# ============================================

# Deploy to Google Cloud Run using source-based deploy (Buildpacks)
deploy-gcp:
	gcloud run deploy $(SERVICE_NAME) \
		--source . \
		--project $(PROJECT_ID) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--set-env-vars="DEBUG=false" \
		--memory 512Mi \
		--cpu 1 \
		--min-instances 0 \
		--max-instances 10

# Deploy with LLM enabled (requires GEMINI_API_KEY secret)
deploy-gcp-with-llm:
	gcloud run deploy $(SERVICE_NAME) \
		--source . \
		--project $(PROJECT_ID) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--set-env-vars="DEBUG=false,AIRS_USE_LLM=true" \
		--set-secrets="GEMINI_API_KEY=gemini-api-key:latest" \
		--memory 512Mi \
		--cpu 1 \
		--min-instances 0 \
		--max-instances 10

# ============================================
# Setup & Utilities
# ============================================

# Install dependencies
install:
	$(PYTHON) -m pip install -r requirements.txt

# Install dev dependencies
install-dev:
	$(PYTHON) -m pip install -r requirements.txt ruff pytest-cov

# Clean up cache files (cross-platform)
clean:
ifeq ($(OS),Windows_NT)
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul || echo.
	@for /d /r . %%d in (.pytest_cache) do @if exist "%%d" rd /s /q "%%d" 2>nul || echo.
	@del /s /q *.pyc 2>nul || echo.
	@if exist .ruff_cache rd /s /q .ruff_cache 2>nul || echo.
else
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .ruff_cache 2>/dev/null || true
endif

# Show help
help:
	@echo "AIRS Makefile Targets:"
	@echo ""
	@echo "Backend Development:"
	@echo "  dev            - Run backend dev server with auto-reload"
	@echo "  test           - Run pytest tests"
	@echo "  lint           - Run Python code linting (ruff/flake8)"
	@echo ""
	@echo "Frontend Development:"
	@echo "  frontend-dev   - Run frontend dev server (Vite)"
	@echo "  frontend-build - Build frontend for production"
	@echo "  frontend-install - Install frontend dependencies"
	@echo "  frontend-lint  - Run frontend linting (ESLint)"
	@echo ""
	@echo "Production:"
	@echo "  run            - Run production server (uvicorn, single worker)"
	@echo "  run-prod       - Run production server (gunicorn + uvicorn workers)"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy-gcp     - Deploy to Google Cloud Run"
	@echo ""
	@echo "Setup:"
	@echo "  install        - Install backend dependencies"
	@echo "  install-dev    - Install dev dependencies"
	@echo "  clean          - Clean cache files"
