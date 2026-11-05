"""Transport-Agnostic Evidence Collection Layer.

Public symbols re-exported so callers can do
``from app.services.evidence import EvidenceAdapter, EvidenceRecord,
AdapterHealth, EvidenceRegistry, get_instance, reset_instance``
without knowing the internal module layout.
"""

from app.services.evidence.base_adapter import (
    AdapterHealth,
    EvidenceAdapter,
    EvidenceRecord,
    WebhookEvidenceAdapter,
    ManualUploadAdapter,
)
from app.services.evidence.registry import (
    EvidenceRegistry,
    get_instance,
    reset_instance,
)

__all__ = [
    "AdapterHealth",
    "EvidenceAdapter",
    "EvidenceRecord",
    "EvidenceRegistry",
    "WebhookEvidenceAdapter",
    "ManualUploadAdapter",
    "get_instance",
    "reset_instance",
]
