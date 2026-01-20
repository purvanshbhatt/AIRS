from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.core.logging import setup_logging, event_logger
from app.core.middleware import (
    RequestIdMiddleware,
    global_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.db.database import engine, Base
from app.api import router as api_router
from app.api.routes.health import router as health_router

import logging

logger = logging.getLogger("airs.main")

# Initialize logging first
setup_logging()

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

# Initialize Firebase if auth is required
if settings.is_auth_required:
    init_firebase()
else:
    logger.info("AUTH_REQUIRED=false, skipping Firebase initialization")

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="AIRS - AI Incident Readiness Score API",
    version="1.0.0",
    debug=settings.DEBUG,
)

# Add request ID middleware (must be first to capture all requests)
app.add_middleware(RequestIdMiddleware)

# Configure CORS using parsed origins from config
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers for consistent error format
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Include API routes
app.include_router(health_router)
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to AIRS"}


if __name__ == "__main__":
    import uvicorn
    # Use PORT from environment (Cloud Run sets this)
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
