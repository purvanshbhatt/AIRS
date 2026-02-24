"""
AIRS Authentication Module

Provides auth dependencies for FastAPI routes.
Auth is controlled by AUTH_REQUIRED env var (default: false).
In production (ENV=prod), auth is always required.

## Firebase Integration

To integrate Firebase Admin SDK for token verification:

1. Install Firebase Admin:
   ```bash
   pip install firebase-admin
   ```

2. Initialize Firebase Admin (add to app startup):
   ```python
   import firebase_admin
   from firebase_admin import credentials

   # Option A: Use default credentials (Cloud Run with service account)
   firebase_admin.initialize_app()

   # Option B: Use explicit credentials file
   cred = credentials.Certificate("path/to/serviceAccountKey.json")
   firebase_admin.initialize_app(cred)
   ```

3. The verify_firebase_token() function below will use Firebase Admin SDK
   when available, otherwise falls back to mock user for development.
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings
from app.core.logging import get_request_id

logger = logging.getLogger("airs.auth")

# Security scheme for OpenAPI docs
security = HTTPBearer(auto_error=False)


class User:
    """Simple user model for auth context."""

    def __init__(
        self,
        uid: str,
        email: Optional[str] = None,
        name: Optional[str] = None,
    ):
        self.uid = uid
        self.email = email
        self.name = name

    def __repr__(self):
        return f"User(uid={self.uid!r}, email={self.email!r})"


def _create_auth_error(code: str, message: str, status_code: int = 401) -> HTTPException:
    """Create a consistent auth error response."""
    request_id = get_request_id() or "-"
    return HTTPException(
        status_code=status_code,
        detail={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id
            }
        },
        headers={"WWW-Authenticate": "Bearer"} if status_code == 401 else None,
    )


def verify_firebase_token(token: str) -> dict:
    """
    Verify Firebase ID token.
    
    Uses Firebase Admin SDK if available. Mock fallback is ONLY allowed
    in local environment — in prod/staging, missing SDK raises an error.
    """
    try:
        # Try to use Firebase Admin SDK
        from firebase_admin import auth
        decoded = auth.verify_id_token(token)
        return {
            "uid": decoded["uid"],
            "email": decoded.get("email"),
            "name": decoded.get("name"),
        }
    except ImportError:
        # Firebase Admin not installed
        if settings.is_prod:
            logger.error("Firebase Admin SDK not installed in production — cannot verify tokens.")
            raise _create_auth_error(
                "AUTH_CONFIG_ERROR",
                "Authentication service unavailable. Contact administrator.",
                status_code=503,
            )
        # Local development only: mock auth
        logger.warning("Firebase Admin SDK not installed. Using mock authentication (local dev only).")
        if token and len(token) > 10:
            return {
                "uid": f"mock-{token[:8]}",
                "email": "mock@example.com",
                "name": "Mock User",
            }
        raise _create_auth_error("INVALID_TOKEN", "Invalid authentication token")
    except Exception as e:
        logger.error(f"Firebase token verification failed: {e}")
        raise _create_auth_error("INVALID_TOKEN", "Invalid or expired authentication token")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """
    Get current authenticated user.

    Behavior depends on AUTH_REQUIRED setting:
    - AUTH_REQUIRED=false (default): Returns None, allows all requests
    - AUTH_REQUIRED=true or ENV=prod: Requires Bearer token, returns 401 if missing/invalid

    Usage:
        @router.get("/protected")
        def protected_route(user: Optional[User] = Depends(get_current_user)):
            # user is None when auth not required, User object when authenticated
            ...
    """
    # If auth is not required, allow all requests
    if not settings.is_auth_required:
        if credentials and credentials.credentials:
            # Token provided even when not required - validate it
            try:
                user_data = verify_firebase_token(credentials.credentials)
                return User(**user_data)
            except Exception:
                # Don't fail on invalid tokens when auth not required
                pass
        return None

    # Auth is required - validate token
    if not credentials or not credentials.credentials:
        raise _create_auth_error(
            "UNAUTHORIZED",
            "Authentication required. Provide a valid Bearer token."
        )

    try:
        user_data = verify_firebase_token(credentials.credentials)
        return User(**user_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise _create_auth_error("INVALID_TOKEN", "Invalid or expired authentication token")


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    """
    Require authentication - use as a dependency for protected routes.

    When AUTH_REQUIRED=false, returns a mock dev user for local development.
    When AUTH_REQUIRED=true or ENV=prod, requires valid Firebase token.

    Usage:
        @router.post("/", dependencies=[Depends(require_auth)])
        def create_item(...):
            ...

        # Or to access user:
        @router.get("/profile")
        def get_profile(user: User = Depends(require_auth)):
            return {"uid": user.uid, "email": user.email}
    """
    # If auth is not required, return dev user
    if not settings.is_auth_required:
        if credentials and credentials.credentials:
            # Token provided - try to validate
            try:
                user_data = verify_firebase_token(credentials.credentials)
                return User(**user_data)
            except Exception:
                pass
        # Return dev user for local development
        return User(
            uid="dev-user",
            email="dev@localhost",
            name="Development User",
        )

    # Auth is required - must have valid token
    if not credentials or not credentials.credentials:
        raise _create_auth_error(
            "UNAUTHORIZED",
            "Authentication required. Provide a valid Bearer token."
        )

    try:
        user_data = verify_firebase_token(credentials.credentials)
        return User(**user_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise _create_auth_error("INVALID_TOKEN", "Invalid or expired authentication token")


# Convenience alias
CurrentUser = Optional[User]
RequiredUser = User


__all__ = [
    "User",
    "get_current_user",
    "require_auth",
    "CurrentUser",
    "RequiredUser",
]
