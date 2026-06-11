import httpx
import logging
import json
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .schemas import SentinelSplunkConfig, SplunkSearchResponse, SplunkEvent

logger = logging.getLogger("airs.sentinel_splunk")

class SplunkNativeClientError(Exception):
    pass

class SplunkNativeClient:
    """Direct HTTP Client for Splunk Enterprise (HEC and Management API)."""
    
    def __init__(self, config: SentinelSplunkConfig):
        self.config = config
        self.hec_url = f"https://{config.host}:{config.hec_port}/services/collector/event"
        self.mgmt_url = f"https://{config.host}:{config.mgmt_port}"
        
        self.hec_headers = {
            "Authorization": f"Splunk {self.config.token}"
        }
        
        self.auth = None
        if self.config.username and self.config.password:
            self.auth = (self.config.username, self.config.password)
            self.mgmt_headers = {}
        else:
            self.mgmt_headers = {
                "Authorization": f"Bearer {self.config.token}"
            }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def get_health(self) -> bool:
        """Verify Management API is reachable."""
        try:
            async with httpx.AsyncClient(verify=self.config.verify_ssl, timeout=10.0, auth=self.auth) as client:
                response = await client.get(f"{self.mgmt_url}/services/server/info?output_mode=json", headers=self.mgmt_headers)
                response.raise_for_status()
                return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # 401 implies the port is reachable but auth failed.
                raise SplunkNativeClientError("Management API reachable, but Unauthorized. Check Token.")
            raise SplunkNativeClientError(f"Management API Error: {e}")
        except Exception as e:
            raise SplunkNativeClientError(f"Failed to reach Management API: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def send_hec_event(self, event_data: dict, source: str = "sentinel", sourcetype: str = "_json") -> bool:
        """Push an event to Splunk HEC."""
        payload = {
            "event": event_data,
            "source": source,
            "sourcetype": sourcetype
        }
        try:
            async with httpx.AsyncClient(verify=self.config.verify_ssl, timeout=10.0) as client:
                response = await client.post(self.hec_url, json=payload, headers=self.hec_headers)
                response.raise_for_status()
                return response.json().get("code") == 0
        except Exception as e:
            logger.error(f"HEC Error: {e}")
            raise SplunkNativeClientError(f"HEC Error: {e}")

    async def search(self, query: str, earliest_time: str = "-24h", latest_time: str = "now") -> SplunkSearchResponse:
        """Execute a synchronous search against Splunk Management API."""
        if not query.strip().startswith("search "):
            query = f"search {query}"
            
        data = {
            "search": query,
            "earliest_time": earliest_time,
            "latest_time": latest_time,
            "output_mode": "json",
            "exec_mode": "oneshot"
        }
        try:
            async with httpx.AsyncClient(verify=self.config.verify_ssl, timeout=30.0, auth=self.auth) as client:
                response = await client.post(f"{self.mgmt_url}/services/search/jobs/export", data=data, headers=self.mgmt_headers)
                response.raise_for_status()
                
                # /export returns ndjson (newline delimited JSON)
                lines = [line for line in response.text.split("\n") if line.strip()]
                events = []
                for line in lines:
                    try:
                        record = json.loads(line)
                        if "result" in record:
                            res = record["result"]
                            events.append(SplunkEvent(
                                id=res.get("_bkt", "") + res.get("_cd", ""), # unique enough proxy
                                source=res.get("source", ""),
                                sourcetype=res.get("sourcetype", ""),
                                time=res.get("_time", ""),
                                host=res.get("host", ""),
                                raw=res.get("_raw", ""),
                                parsed_fields=res
                            ))
                    except json.JSONDecodeError:
                        continue
                        
                return SplunkSearchResponse(events=events, total_count=len(events))
                
        except Exception as e:
            logger.error(f"Search Error: {e}")
            raise SplunkNativeClientError(f"Search Error: {e}")
