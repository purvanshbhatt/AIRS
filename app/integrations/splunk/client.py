"""
Splunk MCP API Client with retry and timeout handling.
"""
import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import ValidationError
from .schemas import SplunkEvent, SplunkSearchResponse, SplunkHealthResponse
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger("airs.splunk_mcp")

class SplunkMCPClientError(Exception):
    pass

class SplunkMCPClient:
    """Async client for Splunk MCP Server."""
    
    def __init__(self, mcp_url: str, api_key: str, verify_ssl: bool = True):
        self.mcp_url = mcp_url.rstrip("/")
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def _request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.api_key}"
        
        async with httpx.AsyncClient(verify=self.verify_ssl, timeout=15.0) as client:
            url = f"{self.mcp_url}{endpoint}"
            response = await client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response

    async def get_health(self) -> SplunkHealthResponse:
        """Get the health status of the Splunk MCP server."""
        try:
            response = await self._request("GET", "/health")
            return SplunkHealthResponse(**response.json())
        except Exception as e:
            logger.error(f"Failed to check Splunk MCP health: {e}")
            raise SplunkMCPClientError("Health check failed") from e

    async def search(self, query: str, earliest_time: str = "-24h", latest_time: str = "now") -> SplunkSearchResponse:
        """Execute a search query on the Splunk MCP server."""
        try:
            payload = {"query": query, "earliest_time": earliest_time, "latest_time": latest_time}
            response = await self._request("POST", "/search", json=payload)
            return SplunkSearchResponse(**response.json())
        except Exception as e:
            logger.error(f"Splunk search failed: {e}")
            raise SplunkMCPClientError("Search failed") from e
