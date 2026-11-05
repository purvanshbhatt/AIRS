import os
import sys
import json
import requests
import argparse
from datetime import datetime, timezone

def get_payloads():
    return {
        "mfa": {
            "evidence_type": "missing_mfa",
            "severity": "high",
            "title": "MFA Disabled for Root Account",
            "description": "AWS CloudTrail event indicating root account MFA was disabled.",
            "raw_log": "eventVersion=1.08, eventName=DeactivateMFADevice, userIdentity={type=Root}"
        },
        "ransomware": {
            "evidence_type": "ransomware_indicator",
            "severity": "critical",
            "title": "Ransomware behavior detected - multiple file encryptions",
            "description": "Wazuh EDR alert indicating rapid file encryption matching ransomware signatures.",
            "raw_log": "rule.description=Ransomware behavior detected, decoder.name=ossec"
        },
        "exfiltration": {
            "evidence_type": "data_exfiltration_indicator",
            "severity": "critical",
            "title": "Unusual outbound data transfer (500GB)",
            "description": "Network traffic analyzer detected 500GB outbound transfer to unknown IP.",
            "raw_log": "src_ip=10.0.0.5, dest_ip=198.51.100.22, bytes_out=500000000000"
        }
    }

def send_event(hec_url: str, token: str, payload_data: dict, source: str = "sentinel_injector", sourcetype: str = "_json"):
    headers = {
        "Authorization": f"Splunk {token}",
        "Content-Type": "application/json"
    }
    
    event = {
        "time": datetime.now(timezone.utc).timestamp(),
        "source": source,
        "sourcetype": sourcetype,
        "index": "main",
        "event": payload_data
    }
    
    try:
        response = requests.post(hec_url, headers=headers, json=event, verify=False)
        response.raise_for_status()
        res_data = response.json()
        if res_data.get("code") == 0:
            print(f"[SUCCESS] Sent event: {payload_data['title']}")
        else:
            print(f"[ERROR] Splunk returned non-zero code: {res_data}")
    except Exception as e:
        print(f"[FAILED] Could not send event: {e}")

def main():
    parser = argparse.ArgumentParser(description="Inject synthetic security logs to Splunk HEC")
    parser.add_argument(
        "--event", 
        choices=["mfa", "ransomware", "exfiltration", "all"], 
        required=True,
        help="Which payload to send"
    )
    args = parser.parse_args()

    hec_url = os.environ.get("SPLUNK_HEC_URL", "https://localhost:8088/services/collector/event")
    token = os.environ.get("SENTINEL_SPLUNK_TOKEN")

    if not token:
        print("[ERROR] SENTINEL_SPLUNK_TOKEN environment variable is required.")
        sys.exit(1)

    # Disable insecure request warnings for local testing
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    payloads = get_payloads()
    
    if args.event == "all":
        for key, p in payloads.items():
            send_event(hec_url, token, p)
    else:
        send_event(hec_url, token, payloads[args.event])

if __name__ == "__main__":
    main()
