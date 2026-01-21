# AIRS - AI Incident Readiness Score

A FastAPI application for AI security readiness assessments with scoring, findings, PDF reports, and optional LLM-powered narratives.

## Live Demo

| Resource | URL |
|----------|-----|
| **Web App** | [airs-demo.web.app](https://airs-demo.web.app) |
| **API Health** | [/health](https://airs-api-knu3wsxymq-uc.a.run.app/health) |
| **LLM Status** | [/health/llm](https://airs-api-knu3wsxymq-uc.a.run.app/health/llm) |

### What AI Does (and Doesn't Do)

| ✅ AI Generates | ❌ AI Does NOT Modify |
|----------------|----------------------|
| Executive summary narrative | Assessment scores |
| Roadmap narrative text | Finding severity/priority |
| Natural language insights | Compliance mappings |

> **Demo Mode Notice:** The live demo uses AI to generate narrative insights based on assessment results. Scores and findings are computed deterministically and are not modified by AI.

## Features

- **Security Assessment Questionnaire** - Structured assessment across multiple domains
- **Deterministic Scoring Engine** - Consistent, reproducible scoring rubric
- **Automated Findings** - Rule-based findings generation with recommendations
- **PDF Reports** - Professional assessment reports with charts
- **LLM Narratives** (Optional) - AI-generated executive summaries using Google Gemini
- **React Frontend** - Interactive assessment interface

## Project Structure

```
AIRS/
├── app/
│   ├── api/              # API route handlers
│   │   └── routes/       # Additional routes (health checks)
│   ├── core/             # Core configuration and settings
│   ├── db/               # Database configuration
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic services
│   ├── reports/          # Report generation
│   └── main.py           # FastAPI application entry point
├── frontend/             # React frontend
├── tests/                # Test files
├── gunicorn.conf.py      # Gunicorn production config
├── Makefile              # Build and deploy commands
├── Procfile              # Cloud Run process definition
├── requirements.txt
└── README.md
```

## Local Development

### Prerequisites

- Python 3.11+
- pip

### Quick Start

1. **Clone and setup:**
   ```bash
   git clone <repository>
   cd AIRS
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   make install
   # or: pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Run development server:**
   ```bash
   make dev
   # or: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the application:**
   - API: http://localhost:8000
   - Swagger Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Running Tests

```bash
make test
# or: pytest tests/ -v
```

### Linting

```bash
make lint
```

## Production Server

### Using Gunicorn + Uvicorn Workers (Recommended)

For production, use gunicorn with uvicorn workers for better performance and reliability:

```bash
# Using Makefile
make run-prod

# Or directly
gunicorn -k uvicorn.workers.UvicornWorker app.main:app \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120

# Or with config file
gunicorn -c gunicorn.conf.py app.main:app
```

### Using Uvicorn Only (Simple)

```bash
make run
# or: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Start Commands Summary

| Environment | Command |
|-------------|---------|
| **Development** | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| **Production (simple)** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Production (recommended)** | `gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120` |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | `AIRS` |
| `DEBUG` | Enable debug mode | `false` |
| `ENV` | Environment mode (`local` or `prod`) | `local` |
| `DATABASE_URL` | Database connection string | `sqlite:///./airs.db` |
| `PORT` | Server port (set by Cloud Run) | `8000` |
| `AIRS_USE_LLM` | Enable LLM narratives | `false` |
| `GEMINI_API_KEY` | Google Gemini API key | - |
| `LLM_MODEL` | Gemini model to use | `gemini-3-pro-preview` |
| `GUNICORN_WORKERS` | Number of gunicorn workers | `2` |
| `LOG_LEVEL` | Logging level | `info` |

## Database Configuration

AIRS supports both SQLite (local development) and PostgreSQL (production).

### Local Development (SQLite)

SQLite is used by default - no configuration needed:

```bash
# Default - uses SQLite
DATABASE_URL=sqlite:///./airs.db

# Run migrations (first time or after model changes)
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

### Production (Cloud SQL PostgreSQL)

For Cloud Run with Cloud SQL PostgreSQL:

```bash
# Unix socket connection (recommended for Cloud Run)
DATABASE_URL=postgresql://user:password@/dbname?host=/cloudsql/PROJECT:REGION:INSTANCE

# Example with AIRS project defaults:
DATABASE_URL=postgresql://airs_user:your_password@/airs_db?host=/cloudsql/gen-lang-client-0384513977:us-central1:airs-db

# TCP connection (for local dev via Cloud SQL Proxy):
DATABASE_URL=postgresql://user:password@127.0.0.1:5432/dbname
```

**Deploy with Cloud SQL:**
```powershell
# PowerShell - set instance and deploy
$env:CLOUDSQL_INSTANCE = "gen-lang-client-0384513977:us-central1:airs-db"
.\scripts\deploy_cloud_run.ps1

# Or pass directly
.\scripts\deploy_cloud_run.ps1 -CloudSqlInstance "gen-lang-client-0384513977:us-central1:airs-db"
```

```bash
# Bash
export CLOUDSQL_INSTANCE="gen-lang-client-0384513977:us-central1:airs-db"
./scripts/deploy_cloud_run.sh
```

📖 **See [docs/CLOUD_SQL_SETUP.md](docs/CLOUD_SQL_SETUP.md) for complete Cloud SQL setup guide.**

**Recommended Cloud SQL Settings:**
- Instance: `db-f1-micro` for dev, `db-custom-2-4096` for production
- PostgreSQL version: 15+
- Enable private IP for Cloud Run connection
- Create dedicated user with minimal privileges

**Connection Pooling:**

The SQLAlchemy engine is pre-configured with pool settings optimized for Cloud Run:
- `pool_size=5` - Base pool connections
- `max_overflow=10` - Up to 15 total connections
- `pool_recycle=1800` - Recycle connections every 30 minutes
- `pool_pre_ping=True` - Verify connections before use

### Running Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Check current migration status
alembic current

# Generate new migration after model changes
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1
```

### Existing Database (Stamp Only)

If you have an existing database and want to start using migrations:

```bash
# Mark current state without running migrations
alembic stamp head
```

## Google Cloud Run Deployment

### Prerequisites

1. **Install Google Cloud CLI:**
   ```bash
   # See: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate:**
   ```bash
   gcloud auth login
   ```

### Step 1: Bootstrap GCP Project

Run the bootstrap script to configure project, region, and enable required APIs:

```powershell
# Windows PowerShell
.\scripts\bootstrap_gcp.ps1
```

```bash
# Linux/macOS
chmod +x scripts/*.sh
./scripts/bootstrap_gcp.sh
```

This will:
- Set project to `gen-lang-client-0384513977`
- Set default region to `us-central1`
- Enable Cloud Run, Cloud Build, and Artifact Registry APIs

### Step 2: Configure Production Environment

```bash
# Copy the example environment file
cp gcp/env.prod.example gcp/env.prod

# Edit with your production values
# - Update CORS_ALLOW_ORIGINS with your frontend URL
# - Configure DATABASE_URL if using Cloud SQL
# - Set GEMINI_API_KEY if using LLM features
```

### How to Get Real Deployment URLs for CORS

Before updating CORS configuration, use the helper scripts to discover your actual deployment URLs:

**Windows PowerShell:**
```powershell
.\scripts\get_deployment_urls.ps1
```

**Linux/macOS:**
```bash
chmod +x scripts/get_deployment_urls.sh
./scripts/get_deployment_urls.sh
```

**Sample Output:**
```
========================================
  AIRS Deployment URLs
========================================

[Backend - Cloud Run]
  Service URL: https://airs-api-227825933697.us-central1.run.app

[Frontend - Firebase Hosting]
  Firebase Project: gen-lang-client-0384513977
  Hosting Sites:
    - https://airs-demo.web.app
    - https://airs-demo.firebaseapp.com

========================================
  Suggested CORS Origins
========================================

Copy this value for CORS_ALLOW_ORIGINS:

  https://airs-demo.web.app,https://airs-demo.firebaseapp.com,http://localhost:5173
```

The script will:
- Query Cloud Run for the active backend service URL (if `gcloud` is available)
- Read `.firebaserc` to find Firebase Hosting site names
- Generate a ready-to-copy CORS origins string

### Step 3: Deploy to Cloud Run

```powershell
# Windows PowerShell
.\scripts\deploy_cloud_run.ps1
```

```bash
# Linux/macOS
./scripts/deploy_cloud_run.sh
```

Or use the Makefile:

```bash
make deploy-gcp
```

### Step 4: Verify Deployment

After deployment, verify the service is running:

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe airs-api --region us-central1 --format='value(status.url)')

# Check health endpoint
curl $SERVICE_URL/health
# Expected: {"status":"ok"}

# Check root endpoint  
curl $SERVICE_URL/
# Expected: {"message":"Welcome to AIRS"}
```

### ⚠️ Database Note

> **SQLite is MVP-only.** Data does NOT persist across Cloud Run instances or deployments.
> 
> For production at scale, use **Cloud SQL PostgreSQL**:
> ```
> DATABASE_URL=postgresql://user:password@/dbname?host=/cloudsql/gen-lang-client-0384513977:us-central1:airs-db
> ```
> See [Cloud SQL documentation](https://cloud.google.com/sql/docs/postgres/connect-run) for setup.

### How It Works

1. Cloud Run uses **Google Cloud Buildpacks** to build the image
2. Buildpacks detect Python from `requirements.txt`
3. The `Procfile` specifies the start command:
   ```
   web: gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```
4. Cloud Run sets the `$PORT` environment variable automatically

### Deploy with LLM Features

1. **Create a secret for the API key:**
   ```bash
   echo -n "YOUR_GEMINI_API_KEY" | \
     gcloud secrets create gemini-api-key --data-file=-
   
   # Grant Cloud Run access to the secret
   gcloud secrets add-iam-policy-binding gemini-api-key \
     --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
     --role="roles/secretmanager.secretAccessor"
   ```

2. **Deploy with LLM enabled:**
   ```bash
   make deploy-gcp-with-llm
   ```

### View Deployment

```bash
# Get service URL
gcloud run services describe airs --region us-central1 --format='value(status.url)'

# View logs
gcloud run logs read airs --region us-central1

# List revisions
gcloud run revisions list --service airs --region us-central1
```

### Environment Variables in Cloud Run

Set environment variables during deployment:

```bash
gcloud run deploy airs \
    --source . \
    --set-env-vars="DEBUG=false,AIRS_USE_LLM=true" \
    --update-secrets="GEMINI_API_KEY=gemini-api-key:latest"
```

## API Endpoints

### Health & Status
- `GET /health` - Health check (for load balancers)
- `GET /health/llm` - LLM configuration status
- `GET /health/cors` - CORS configuration verification (see below)
- `GET /` - Welcome message

### CORS Verification

The `/health/cors` endpoint helps debug CORS issues without exposing secrets:

```bash
# From terminal
curl https://your-api.run.app/health/cors

# Response:
{
  "env": "prod",
  "localhost_allowed": false,
  "allowed_origins": ["https://airs-demo.web.app", "https://airs-demo.firebaseapp.com"],
  "request_origin": null,
  "origin_allowed": false
}
```

**From browser console** (includes Origin header):
```javascript
fetch('https://your-api.run.app/health/cors')
  .then(r => r.json())
  .then(console.log);

// Response includes your origin:
{
  "env": "prod",
  "localhost_allowed": false,
  "allowed_origins": ["https://airs-demo.web.app"],
  "request_origin": "https://airs-demo.web.app",
  "origin_allowed": true
}
```

Use this to verify:
- Your frontend origin is in the allowed list
- The environment is correct (prod vs local)
- Localhost is enabled/disabled as expected

### Organizations
- `POST /api/orgs/` - Create organization
- `GET /api/orgs/` - List organizations
- `GET /api/orgs/{id}` - Get organization

### Assessments
- `POST /api/assessments/` - Create assessment
- `GET /api/assessments/{id}` - Get assessment
- `POST /api/assessments/{id}/answers` - Submit answers
- `POST /api/assessments/{id}/score` - Calculate score
- `GET /api/assessments/{id}/report` - Download PDF report

### Scoring
- `GET /api/scoring/rubric` - Get scoring rubric
- `GET /api/scoring/questionnaire` - Get questionnaire

### Narratives (LLM)
- `GET /api/narratives/status` - LLM availability status
- `POST /api/narratives/{id}/narratives` - Generate all narratives
- `GET /api/narratives/{id}/executive-summary` - Get executive summary

## Troubleshooting

### Cloud Run Build Fails

Ensure `requirements.txt` is present and valid:
```bash
pip install -r requirements.txt  # Test locally first
```

### Port Binding Issues

Cloud Run sets the `PORT` environment variable. The app and gunicorn config automatically use it.

### Database in Cloud Run

SQLite works for demos but data doesn't persist across instances. For production:
- Use Cloud SQL (PostgreSQL/MySQL)
- Use Firestore
- Use Cloud Storage for data files

### Gunicorn Not Found

Make sure gunicorn is in requirements.txt:
```
gunicorn>=21.0.0
uvicorn[standard]>=0.32.0
```

## License

MIT
