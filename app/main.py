from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings, Environment, validate_deployment, DeploymentValidationError
from app.core.logging import setup_logging, event_logger
from app.core.cors import get_allowed_origins, log_cors_config
from app.core.middleware import (
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi import Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from app.db.database import engine, Base
from app.api.routes.health import router as health_router
from app.api import router as api_router
from app.services.audit import register_system_auditor

import logging

logger = logging.getLogger("airs.main")

# Initialize logging first
setup_logging()

# Initialize tracing
from app.observability.tracing import setup_tracing
setup_tracing()

# ── Deployment Validation (Fail-Fast) ──
# CRITICAL: This MUST run before any other initialization.
# Crashes immediately if ENV doesn't match expected GCP project.
try:
    validate_deployment()
except DeploymentValidationError as e:
    logger.critical(f"DEPLOYMENT VALIDATION FAILED: {e}")
    raise SystemExit(1) from e

# ── Environment Guardrails ──
def _validate_environment():
    """Log environment mode and validate configuration on startup."""
    env = settings.ENV
    if env == Environment.DEMO:
        logger.warning(
            "⚠️  DEMO MODE ACTIVE — All write endpoints return 403 Forbidden. "
            "Synthetic data is frozen for investor presentations."
        )
    elif env == Environment.STAGING:
        logger.info("STAGING environment — write operations enabled")
    elif env == Environment.LOCAL:
        logger.info("LOCAL development environment")
    else:
        logger.info(f"Environment: {env}")

_validate_environment()

# ── Rate Limiter ──
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])

# Initialize Firebase Admin SDK (for token verification)
def init_firebase():
    """Initialize Firebase Admin SDK using Application Default Credentials."""
    try:
        import firebase_admin
        from firebase_admin import credentials
        
        # Check if already initialized
        try:
            firebase_admin.get_app()
            logger.info("Firebase Admin SDK already initialized")
            return True
        except ValueError:
            pass
        
        # Initialize with ADC (Application Default Credentials)
        # On Cloud Run, this uses the service account automatically
        # Locally, use: gcloud auth application-default login
        firebase_admin.initialize_app()
        logger.info("Firebase Admin SDK initialized with ADC")
        return True
    except ImportError:
        logger.warning("firebase-admin not installed. Token verification will use mock mode.")
        return False
    except Exception as e:
        logger.warning(f"Firebase Admin SDK initialization failed: {e}. Token verification will use mock mode.")
        return False

# Try to initialize Firebase (non-blocking - app will work with mock auth if it fails)
try:
    if settings.is_auth_required:
        init_firebase()
    else:
        logger.info("AUTH_REQUIRED=false, skipping Firebase initialization")
except Exception as e:
    logger.warning(f"Firebase initialization error (non-fatal): {e}")

# NOTE: Schema is managed by Alembic migrations (alembic upgrade head).
# In production/staging with PostgreSQL, run `alembic upgrade head` before starting.
# For SQLite (ephemeral Cloud Run filesystem), auto-create tables on startup
# since there is no persistent migration state to track.
def _auto_create_sqlite_tables():
    """Create all tables for SQLite databases (ephemeral filesystem on Cloud Run)."""
    if settings.DATABASE_URL.startswith("sqlite"):
        import app.models  # noqa: F401 — registers all models with Base
        Base.metadata.create_all(bind=engine)
        logger.info("SQLite auto-create: tables initialized")

_auto_create_sqlite_tables()

# ── Firestore → SQLite sync on startup ──
def _sync_firestore_on_startup():
    """Pull persistent data from Firestore into ephemeral SQLite."""
    try:
        from app.db.firestore import sync_orgs_from_firestore, sync_assessments_from_firestore
        from app.db.database import SessionLocal
        db = SessionLocal()
        try:
            org_count = sync_orgs_from_firestore(db)
            assessment_count = sync_assessments_from_firestore(db)
            if org_count or assessment_count:
                logger.info(
                    "Firestore startup sync: %d orgs restored, %d assessments restored",
                    org_count,
                    assessment_count,
                )
        finally:
            db.close()
    except Exception as e:
        logger.warning("Firestore startup sync skipped: %s", e)

_sync_firestore_on_startup()

# Register the system auditing trace to record all configuration mutations
register_system_auditor()

app = FastAPI(
    title=settings.APP_NAME,
    description="ResilAI - AI Incident Readiness Score API",
    version="1.0.0",
    debug=settings.DEBUG,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

async def poll_wazuh_telemetry():
    """Background task to periodically poll Wazuh manager telemetry and update cache."""
    import asyncio
    from app.db.database import SessionLocal
    from app.models.wazuh_config import WazuhConfig
    from app.services.wazuh_client import WazuhClientFactory
    from app.models.wazuh_telemetry_cache import WazuhTelemetryCache
    from app.services.audit import record_connector_audit
    import json
    
    # Wait for the app to initialize
    await asyncio.sleep(5)
    
    while True:
        try:
            db = SessionLocal()
            try:
                configs = db.query(WazuhConfig).all()
                for cfg in configs:
                    org_id = cfg.org_id
                    client = WazuhClientFactory.get_client(org_id, db)
                    if client:
                        try:
                            status_resp = await client.get_agent_status()
                            vuln_resp = await client.get_vulnerabilities()
                            
                            cache = db.query(WazuhTelemetryCache).filter(WazuhTelemetryCache.org_id == org_id).first()
                            if not cache:
                                cache = WazuhTelemetryCache(org_id=org_id)
                                db.add(cache)
                            
                            cache.agent_status = json.dumps(status_resp.to_dict())
                            cache.vulnerabilities = json.dumps(vuln_resp.to_dict())
                            db.commit()
                            
                            record_connector_audit(
                                db=db,
                                org_id=org_id,
                                action="poll_success",
                                actor="system",
                                connector_type="wazuh",
                                status="success"
                            )
                        except Exception as poll_err:
                            logger.error(f"Failed polling telemetry for org {org_id}: {poll_err}")
                            record_connector_audit(
                                db=db,
                                org_id=org_id,
                                action="poll_failed",
                                actor="system",
                                connector_type="wazuh",
                                status="failed",
                                extra_details={"error": str(poll_err)}
                            )
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error in poll_wazuh_telemetry loop: {e}")
            
        await asyncio.sleep(60)

@app.on_event("startup")
async def start_background_tasks():
    """Start background tasks and schedulers."""
    import asyncio
    asyncio.create_task(poll_wazuh_telemetry())
    
    # Start the global task scheduler
    from app.tasks.scheduler import scheduler
    scheduler.start()

    # Start the intelligence task scheduler
    from app.tasks.intelligence_task import start_intelligence_scheduler
    start_intelligence_scheduler()

@app.on_event("shutdown")
async def stop_background_tasks():
    """Stop all background tasks."""
    from app.tasks.scheduler import scheduler
    scheduler.stop()

    # Stop the intelligence task scheduler
    from app.tasks.intelligence_task import stop_intelligence_scheduler
    stop_intelligence_scheduler()

security = HTTPBasic()

def get_docs_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, settings.DOCS_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, settings.DOCS_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/docs", include_in_schema=False)
async def get_swagger_documentation(username: str = Depends(get_docs_username)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")

@app.get("/redoc", include_in_schema=False)
async def get_redoc_documentation(username: str = Depends(get_docs_username)):
    return get_redoc_html(openapi_url="/openapi.json", title="docs")

@app.get("/openapi.json", include_in_schema=False)
async def openapi(username: str = Depends(get_docs_username)):
    return get_openapi(title=app.title, version=app.version, routes=app.routes)


# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add request ID middleware (must be first to capture all requests)
app.add_middleware(RequestIdMiddleware)

# Add security response headers
app.add_middleware(SecurityHeadersMiddleware)

# Get validated CORS origins - single source of truth
# This validates scheme, hostname, and blocks wildcards in production
# Relax CORS in staging to allow local frontend testing
is_strict_cors = settings.ENV in ("prod", "demo")

cors_origins = get_allowed_origins(
    env_var="CORS_ALLOW_ORIGINS",
    default=settings.CORS_ALLOW_ORIGINS,
    is_production=is_strict_cors
)

# Log CORS configuration at startup for operator visibility
log_cors_config(cors_origins, is_production=is_strict_cors)

# Configure CORS middleware
# Explicitly allow Authorization header for Firebase token auth
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["X-Request-ID"],
)

# Register exception handlers for consistent error format
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Include API routes
app.include_router(health_router)
app.include_router(api_router, prefix="/api")

# Internal assurance endpoints (staging-only, gated by ENV check)
from app.api.internal import router as internal_router
app.include_router(internal_router, prefix="/internal")

# ── Real-Time Telemetry WebSocket Endpoint ──
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket, org_id: str | None = None):
    """WebSocket connection that registers clients for real-time, event-driven GHI posture updates."""
    from app.core.websocket_manager import telemetry_ws_manager
    from app.db.database import SessionLocal
    from app.models.organization import Organization
    import json

    # Resolve active organization
    db = SessionLocal()
    resolved_org_id = org_id
    try:
        if not resolved_org_id:
            org = db.query(Organization).first()
            if org:
                resolved_org_id = org.id
    except Exception as exc:
        logger.error(f"Error resolving default organization for WebSocket: {exc}")
    finally:
        db.close()

    if not resolved_org_id:
        await websocket.accept()
        await websocket.send_text(json.dumps({"error": "No organization found"}))
        await websocket.close()
        return

    await telemetry_ws_manager.connect(resolved_org_id, websocket)

    # Send the current posture state immediately upon connection
    await telemetry_ws_manager.broadcast_org_update(resolved_org_id)

    try:
        while True:
            # Keep connection open and listen for client disconnects
            await websocket.receive_text()
    except WebSocketDisconnect:
        telemetry_ws_manager.disconnect(resolved_org_id, websocket)
    except Exception as exc:
        logger.error(f"WebSocket telemetry client error: {exc}")
        telemetry_ws_manager.disconnect(resolved_org_id, websocket)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": f"Welcome to {settings.APP_NAME}"}

@app.get("/api/debug/build-info")
async def build_info():
    import os
    import subprocess
    git_sha = "unknown"
    try:
        git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("ascii").strip()
    except Exception:
        pass
    return {
        "git_sha": git_sha,
        "build_date": os.environ.get("BUILD_DATE", "unknown"),
        "environment": settings.ENV.value
    }


if __name__ == "__main__":
    import uvicorn
    # Use PORT from environment (Cloud Run sets this)
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
