"""
SQLAlchemy custom types for security and data integrity.
"""

from typing import Any, Optional
from sqlalchemy.types import TypeDecorator, Text
from app.core.security.encryption import get_encryption_service

class EncryptedString(TypeDecorator):
    """
    Transparently encrypts string values on write and decrypts them on read
    using the application's EncryptionService (AES-256-GCM).
    
    If the encryption service operates in passthrough mode, the plaintext
    will be stored and retrieved directly.
    """
    
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect: Any) -> Optional[str]:
        if value is None:
            return value
            
        svc = get_encryption_service()
        if not svc.enabled:
            return value
            
        # We need to simulate the dictionary structure that encrypt_fields expects,
        # or we can directly use the internal _encrypt_blob if we manage encoding.
        # Since encrypt_fields takes a dict, let's wrap our scalar.
        payload = {"value": value}
        encrypted_doc = svc.encrypt_fields(payload, sensitive_fields={"value"})
        
        # Save the resulting dict as a JSON string in the database.
        import json
        return json.dumps(encrypted_doc)

    def process_result_value(self, value: Optional[str], dialect: Any) -> Optional[str]:
        if value is None:
            return value
            
        # Try to parse it as JSON to see if it's our encrypted dictionary
        import json
        try:
            doc = json.loads(value)
        except json.JSONDecodeError:
            # It's either plaintext (passthrough mode from before) or malformed
            return value
            
        if not isinstance(doc, dict):
            return value
            
        # Check if it has encryption metadata
        if "encrypted_blob" in doc:
            svc = get_encryption_service()
            decrypted_doc = svc.decrypt_fields(doc)
            return decrypted_doc.get("value")
            
        # Plaintext JSON dict fallback
        return doc.get("value", value)
