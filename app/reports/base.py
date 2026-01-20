from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseReport(ABC):
    """Abstract base class for report generation."""
    
    @abstractmethod
    def generate(self, data: Dict[str, Any]) -> bytes:
        """Generate report from data."""
        pass
    
    @abstractmethod
    def get_content_type(self) -> str:
        """Return the MIME content type of the report."""
        pass
