import abc
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class SoftwareInventoryRecord(BaseModel):
    """Normalized software inventory record returned by pollers."""
    software_name: str
    version: str
    component_type: str  # e.g., "language", "database", "server", "runtime"
    source: str          # e.g., "AWSConfig", "Kubernetes", "MicrosoftGraph"
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    host_id: Optional[str] = None
    raw_evidence: Dict[str, Any] = Field(default_factory=dict)

class DirectDiscoveryPoller(abc.ABC):
    """Abstract base class for direct technology discovery pollers."""
    
    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize the poller.
        
        Args:
            credentials: A dictionary containing secrets/keys. 
                         Must be isolated and not logged.
        """
        self._credentials = credentials
    
    @abc.abstractmethod
    async def poll(self) -> List[SoftwareInventoryRecord]:
        """
        Poll the data source and return a list of discovered software inventory records.
        Returns raw evidence in a normalized, fully auditable format without LLM usage.
        """
        pass

class MicrosoftGraphPoller(DirectDiscoveryPoller):
    """Poller for Microsoft Graph API device inventory."""
    
    async def poll(self) -> List[SoftwareInventoryRecord]:
        # Simulate async network call
        await asyncio.sleep(0.1)
        
        # Staging: return mock deterministic data
        return [
            SoftwareInventoryRecord(
                software_name="NodeJS",
                version="18",
                component_type="runtime",
                source="MicrosoftGraph",
                host_id="vm-graph-01",
                raw_evidence={"endpoint": "/deviceManagement/managedDevices", "mock": True}
            ),
            SoftwareInventoryRecord(
                software_name="Nginx",
                version="1.20",
                component_type="server",
                source="MicrosoftGraph",
                host_id="vm-graph-02",
                raw_evidence={"endpoint": "/deviceManagement/managedDevices", "mock": True}
            )
        ]

class AWSConfigPoller(DirectDiscoveryPoller):
    """Poller for AWS Config resource inventory."""
    
    async def poll(self) -> List[SoftwareInventoryRecord]:
        # Simulate async network call
        await asyncio.sleep(0.1)
        
        # Staging: return mock deterministic data
        return [
            SoftwareInventoryRecord(
                software_name="PostgreSQL",
                version="11",
                component_type="database",
                source="AWSConfig",
                host_id="rds-postgres-11",
                raw_evidence={"resourceType": "AWS::RDS::DBInstance", "mock": True}
            )
        ]

class KubernetesInventoryPoller(DirectDiscoveryPoller):
    """Poller for Kubernetes cluster workloads and images."""
    
    async def poll(self) -> List[SoftwareInventoryRecord]:
        # Simulate async network call
        await asyncio.sleep(0.1)
        
        # Staging: return mock deterministic data
        return [
            SoftwareInventoryRecord(
                software_name="Python",
                version="3.8.1",
                component_type="language",
                source="Kubernetes",
                host_id="pod-python-backend",
                raw_evidence={"apiVersion": "v1", "kind": "Pod", "mock": True}
            )
        ]
