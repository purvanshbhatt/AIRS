"""API key authentication dependencies for external integrations."""

from typing import List, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.api_key import ApiKey
from app.services.integrations import validate_api_key


def get_api_key_dependency(required_scopes: Optional[List[str]] = None):
    """Create an API key dependency with optional scope enforcement."""

    async def _dependency(
        x_airs_api_key: Optional[str] = Header(default=None, alias="X-AIRS-API-Key"),
        db: Session = Depends(get_db),
    ) -> ApiKey:
        if not x_airs_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-AIRS-API-Key header",
            )

        key = validate_api_key(db, x_airs_api_key, required_scopes=required_scopes)
        if not key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API key or insufficient scope",
            )
        return key

    return _dependency