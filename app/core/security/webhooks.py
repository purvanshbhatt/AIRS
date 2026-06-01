"""
Webhook interceptor for incoming telemetry payloads.
Provides strict validation, size boundaries, and signature verification.
"""

import hmac
import hashlib
import json
from typing import Callable, Any

from fastapi import Request, HTTPException, status
from pydantic import BaseModel, Field

# Strict structure for incoming telemetry to prevent arbitrary injection
class TelemetryPayloadSchema(BaseModel):
    event_type: str = Field(..., max_length=100)
    source: str = Field(..., max_length=100)
    timestamp: str = Field(..., max_length=100)
    data: dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "forbid"  # Reject any unrecognized fields to prevent payload smuggling

class TelemetryInterceptor:
    """
    FastAPI Dependency that acts as a runtime protection guardrail for incoming webhooks.
    - Enforces maximum payload size.
    - Validates HMAC-SHA256 signature if required.
    - Parses and strictly validates JSON schema boundaries.
    """
    
    def __init__(self, max_size_bytes: int = 1024 * 1024, require_signature: bool = True):
        self.max_size_bytes = max_size_bytes
        self.require_signature = require_signature
        
    async def __call__(self, request: Request) -> TelemetryPayloadSchema:
        # 1. Payload size boundary
        body_bytes = await request.body()
        if len(body_bytes) > self.max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Payload exceeds maximum allowed size of {self.max_size_bytes} bytes"
            )
            
        # 2. Structural boundary validation
        try:
            payload_dict = json.loads(body_bytes.decode("utf-8"))
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed JSON payload"
            )
            
        try:
            validated_payload = TelemetryPayloadSchema(**payload_dict)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Payload failed strict boundary validation: {str(e)}"
            )
            
        # 3. Cryptographic Signature Validation
        if self.require_signature:
            signature_header = request.headers.get("X-Hub-Signature-256")
            if not signature_header:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing X-Hub-Signature-256 header"
                )
                
            # In a real scenario, retrieve the secret associated with the client/org
            # Here we use a dummy secret for the interceptor logic
            secret = b"shared-telemetry-secret"
            expected_signature = "sha256=" + hmac.new(secret, body_bytes, hashlib.sha256).hexdigest()
            
            if not hmac.compare_digest(signature_header, expected_signature):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid cryptographic signature"
                )
                
        return validated_payload

verify_telemetry_webhook = TelemetryInterceptor()
