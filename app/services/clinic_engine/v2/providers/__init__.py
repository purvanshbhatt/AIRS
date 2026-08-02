from .base import EvidenceProvider, ProviderRegistry
from .microsoft_provider import MicrosoftProvider
from .wazuh_provider import WazuhProvider
from .veeam_provider import VeeamProvider

__all__ = [
    "EvidenceProvider",
    "ProviderRegistry",
    "MicrosoftProvider",
    "WazuhProvider",
    "VeeamProvider",
]

# Register providers
ProviderRegistry.register(MicrosoftProvider)
ProviderRegistry.register(WazuhProvider)
ProviderRegistry.register(VeeamProvider)
