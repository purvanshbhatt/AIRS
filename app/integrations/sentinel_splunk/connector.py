import os
from .schemas import SentinelSplunkConfig

def get_splunk_config() -> SentinelSplunkConfig:
    """Loads Sentinel Splunk config from environment variables only."""
    return SentinelSplunkConfig(
        host=os.environ.get("SENTINEL_SPLUNK_HOST", "localhost"),
        hec_port=int(os.environ.get("SENTINEL_SPLUNK_HEC_PORT", 8088)),
        mgmt_port=int(os.environ.get("SENTINEL_SPLUNK_MGMT_PORT", 8089)),
        token=os.environ.get("SENTINEL_SPLUNK_TOKEN", ""),
        username=os.environ.get("SENTINEL_SPLUNK_USERNAME", None),
        password=os.environ.get("SENTINEL_SPLUNK_PASSWORD", None),
        verify_ssl=os.environ.get("SENTINEL_SPLUNK_VERIFY_SSL", "false").lower() == "true"
    )
