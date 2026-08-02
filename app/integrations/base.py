import abc
from typing import Any, Dict, List

class BaseTelemetryConnector(abc.ABC):
    """
    Abstract interface for enterprise SIEM connectors (Splunk, Wazuh, Security Hub, etc).
    All integrations must implement this interface to ensure deterministic telemetry ingestion.
    """

    @abc.abstractmethod
    async def health_check(self) -> bool:
        """
        Verify connection and authentication.
        """
        pass

    @abc.abstractmethod
    async def search(self, query: str, **kwargs) -> Any:
        """
        Execute a search query against the source system and return results.
        """
        pass

    @abc.abstractmethod
    async def ingest(self, db, org_id: str, query: str, **kwargs) -> int:
        """
        Execute a search and map the results into deterministic TelemetryEvent records.
        Returns the number of events ingested.
        """
        pass

