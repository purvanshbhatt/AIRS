from .base import EvidenceProvider, ProviderRegistry
from .microsoft_provider import MicrosoftProvider
from .wazuh_provider import WazuhProvider
from .veeam_provider import VeeamProvider
from .aws_provider import AWSProvider

__all__ = [
    "EvidenceProvider",
    "ProviderRegistry",
    "MicrosoftProvider",
    "WazuhProvider",
    "VeeamProvider",
    "AWSProvider",
]

# Register providers
ProviderRegistry.register(MicrosoftProvider)
ProviderRegistry.register(WazuhProvider)
ProviderRegistry.register(VeeamProvider)
ProviderRegistry.register(AWSProvider)
