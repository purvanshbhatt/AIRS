from abc import ABC, abstractmethod
from typing import List, Type, Dict

from app.services.clinic_engine.v2.schema import Evidence, EvidenceKind, RawEvent

class EvidenceProvider(ABC):
    @classmethod
    @abstractmethod
    def connector_type(cls) -> str: ...
    
    @classmethod
    @abstractmethod  
    def provides(cls) -> List[EvidenceKind]: ...
    
    @classmethod
    @abstractmethod
    def extract(cls, events: List[RawEvent]) -> List[Evidence]: ...

class ProviderRegistry:
    _providers: Dict[str, Type['EvidenceProvider']] = {}

    @classmethod
    def register(cls, provider: Type['EvidenceProvider']) -> None:
        cls._providers[provider.connector_type()] = provider

    @classmethod
    def get_provider(cls, connector_type: str) -> Type['EvidenceProvider']:
        if connector_type not in cls._providers:
            raise ValueError(f"No provider registered for connector type: {connector_type}")
        return cls._providers[connector_type]

    @classmethod
    def list_all(cls) -> Dict[str, Type['EvidenceProvider']]:
        """Return all registered providers."""
        return dict(cls._providers)

    @classmethod
    def get_providers_for_evidence(cls, kind: EvidenceKind) -> List[Type['EvidenceProvider']]:
        """Return all providers that can produce a given evidence kind."""
        return [p for p in cls._providers.values() if kind in p.provides()]

    @classmethod
    def reset(cls):
        """Reset registry. Only for testing."""
        cls._providers.clear()
