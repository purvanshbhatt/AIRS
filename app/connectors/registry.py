"""
Connector Registry — Maps connector type identifiers to implementation classes.

Usage::

    from app.connectors.registry import register_connector, ConnectorRegistry

    @register_connector
    class MyConnector(BaseConnector):
        CONNECTOR_TYPE = "my_connector"
        ...

    cls = ConnectorRegistry.get_connector_class("my_connector")
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Dict, List, Type

from app.connectors.base import BaseConnector

logger = logging.getLogger("airs.connectors.registry")


# ---------------------------------------------------------------------------
# Supported connector types (extend as new connectors are added)
# ---------------------------------------------------------------------------

class ConnectorType(str, Enum):
    """Well-known connector types recognised by the platform."""

    GITHUB = "github"
    WAZUH = "wazuh"
    AWS_SECURITY_HUB = "aws_security_hub"
    OKTA = "okta"
    GITLAB = "gitlab"
    GCP_SCC = "gcp_scc"
    AZURE_SECURITY_CENTER = "azure_security_center"
    SPLUNK = "splunk"
    CROWDSTRIKE = "crowdstrike"
    VERTEX_AI = "vertex_ai"
    AWS_BEDROCK = "aws_bedrock"
    AZURE_OPENAI = "azure_openai"
    MICROSOFT = "microsoft"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class ConnectorRegistry:
    """Central registry that maps connector type strings to their classes."""

    _registry: Dict[str, Type[BaseConnector]] = {}

    @classmethod
    def register(cls, connector_class: Type[BaseConnector]) -> Type[BaseConnector]:
        """Register a connector class by its ``CONNECTOR_TYPE``.

        Intended to be used as a decorator (see ``register_connector``).
        """
        ctype = connector_class.CONNECTOR_TYPE
        if ctype in cls._registry:
            logger.warning(
                "Overwriting existing connector registration for %r", ctype
            )
        cls._registry[ctype] = connector_class
        logger.debug("Registered connector: %s -> %s", ctype, connector_class.__name__)
        return connector_class

    @classmethod
    def get_connector_class(cls, connector_type: str) -> Type[BaseConnector]:
        """Look up a connector class by type string.

        Raises ``KeyError`` if the type is not registered.
        """
        try:
            return cls._registry[connector_type]
        except KeyError:
            available = ", ".join(sorted(cls._registry)) or "(none)"
            raise KeyError(
                f"Unknown connector type {connector_type!r}. "
                f"Available: {available}"
            ) from None

    @classmethod
    def list_available_connectors(cls) -> List[str]:
        """Return sorted list of registered connector type identifiers."""
        return sorted(cls._registry.keys())


# ---------------------------------------------------------------------------
# Convenience decorator and helpers
# ---------------------------------------------------------------------------

def register_connector(cls: Type[BaseConnector]) -> Type[BaseConnector]:
    """Class decorator that auto-registers a connector in the global registry.

    Example::

        @register_connector
        class GitHubConnector(BaseConnector):
            CONNECTOR_TYPE = "github"
    """
    return ConnectorRegistry.register(cls)


def get_connector_class(connector_type: str) -> Type[BaseConnector]:
    """Look up a connector class by type string."""
    return ConnectorRegistry.get_connector_class(connector_type)

