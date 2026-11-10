"""
Representative technology stack for the demo organizations.

The recorded AWS demo environment (``fixtures/aws_healthcare.json`` /
``aws_legal.json``) captured three Amazon Linux 2023 servers per industry but
no software inventory, so the software rows below are a fixed, typical set
for a small clinic / law firm placed on those recorded server names.

Only the INVENTORY is fixed. Vulnerabilities, known-exploited flags and
end-of-life dates for it come from the same live lookup path real
organizations use (OSV, NVD, CISA KEV, endoflife.date, cached 24 h). When
those feeds cannot be reached the stack is returned with no vulnerabilities
and the feed status says so.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from app.services.demo.aws_demo_telemetry import _industry_for, load_recorded_fixture
from app.services.vuln_intel.catalog import parse_os
from app.services.vuln_intel.inventory import StackItem, make_item, os_item

SSM = "demo_aws_systems_manager"
INTUNE = "demo_microsoft_intune"
WEB = "demo_web_scan"
APP = "demo_application_manifest"

_PROFILES: Dict[str, Dict[str, Any]] = {
    "healthcare": {
        "slug": "metro-health",
        "servers": ["metro-health-ehr-app-server", "metro-health-backup-server",
                    "metro-health-front-desk-workstation"],
        "app_server": "metro-health-ehr-app-server",
        "backup_server": "metro-health-backup-server",
        "devices": ["FRONTDESK-PC-01", "FRONTDESK-PC-02", "NURSE-STATION-04"],
        "website": "www.metro-health.example",
        "website_label": "Patient website (sample)",
        "app": ("Django", "4.2.7"),          # patient-portal framework
    },
    "legal": {
        "slug": "northstar-cole",
        "servers": ["northstar-cole-dms-matter-server", "northstar-cole-file-server",
                    "northstar-cole-partner-laptop-vdi"],
        "app_server": "northstar-cole-dms-matter-server",
        "backup_server": "northstar-cole-file-server",
        "devices": ["PARTNER-LAPTOP-03", "PARALEGAL-PC-11", "RECEPTION-PC-01"],
        "website": "www.northstar-cole.example",
        "website_label": "Firm website (sample)",
        "app": ("Express", "4.17.1"),        # client-intake portal framework
    },
}


def demo_profile(org_id: str) -> Dict[str, Any]:
    industry = _industry_for(org_id)
    profile = dict(_PROFILES[industry])
    profile["industry"] = industry
    fixture = load_recorded_fixture(industry)
    if fixture:
        names = [r.get("name") for r in fixture.get("resources") or [] if r.get("name")]
        if names:
            profile["servers"] = names
            profile["app_server"] = next((n for n in names if "app" in n or "dms" in n), names[0])
            profile["backup_server"] = next((n for n in names if "backup" in n or "file" in n), names[-1])
    return profile


def demo_stack_items(org_id: str) -> List[StackItem]:
    profile = demo_profile(org_id)
    seen = datetime.now(timezone.utc) - timedelta(hours=3)
    al2023 = parse_os("Amazon Linux 2023")
    win10 = parse_os("Windows 10 22H2")
    items: List[StackItem] = []

    for server in profile["servers"]:
        items.append(os_item(al2023, SSM, asset=server, last_seen=seen))

    app_server, backup = profile["app_server"], profile["backup_server"]
    server_software = [
        ("nginx", "1.24.0", app_server),
        ("php8.1", "8.1.27", app_server),
        ("postgresql15", "15.4", app_server),       # PostgreSQL 15 client libraries
        ("openssl", "3.0.8", app_server),
        ("openssl", "3.0.8", backup),
    ]
    for name, version, asset in server_software:
        items.append(make_item(name, version, SSM, asset=asset, host_os=al2023, last_seen=seen))

    app_name, app_version = profile["app"]
    items.append(make_item(app_name, app_version, APP, asset=app_server, last_seen=seen))

    for device in profile["devices"][:2]:
        items.append(os_item(win10, INTUNE, asset=device, last_seen=seen))
        items.append(make_item("Google Chrome", "126.0.6478.127", INTUNE, asset=device,
                               host_os=win10, last_seen=seen))
    items.append(make_item("Microsoft 365 Apps for enterprise - en-us", "16.0.17328.20162", INTUNE,
                           asset=profile["devices"][0], host_os=win10, last_seen=seen))

    items.append(make_item("WordPress", "6.4.2", WEB, asset=profile["website"], last_seen=seen))
    return [i for i in items if i is not None]


def demo_inventory_sources() -> Dict[str, str]:
    return {"aws": "demo", "ms_graph": "demo", "wazuh": "not_connected", "web_scan": "demo"}


def demo_web_assets(org_id: str) -> List[Dict[str, Any]]:
    """One sample website with an illustrative scan result (reserved .example domain)."""
    profile = demo_profile(org_id)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=17)
    url = f"https://{profile['website']}/"
    scan = {
        "url": url,
        "reachable": True,
        "status_code": 200,
        "final_url": url,
        "tls": {
            "valid": True,
            "expires_at": expires.isoformat().replace("+00:00", "Z"),
            "days_left": 17,
            "issuer": "Let's Encrypt",
        },
        "headers": {"hsts": True, "csp": False, "x_frame_options": True,
                    "x_content_type_options": False, "referrer_policy": False},
        "detected": [
            {"name": "WordPress", "version": "6.4.2",
             "evidence": 'meta generator: "WordPress 6.4.2"', "confidence": "confirmed"},
            {"name": "WordPress plugin: contact-form-7", "version": "5.8.4",
             "evidence": "/wp-content/plugins/contact-form-7/...?ver=5.8.4", "confidence": "unverified"},
            {"name": "nginx", "version": None, "evidence": "Server: nginx", "confidence": "confirmed"},
        ],
        "issues": [
            {"title": "Certificate expires in 17 days", "severity": "medium",
             "fix": "Renew the TLS certificate now, or turn on automatic renewal with your host."},
            {"title": "No Content-Security-Policy header", "severity": "medium",
             "fix": "Ask your web developer or host to add a Content-Security-Policy header."},
            {"title": "No X-Content-Type-Options header", "severity": "low",
             "fix": "Add the header 'X-Content-Type-Options: nosniff' on the web server."},
            {"title": "Software version visible to visitors (WordPress 6.4.2)", "severity": "low",
             "fix": "Hide the generator tag and keep WordPress updated."},
        ],
        "scanned_at": (now - timedelta(hours=3)).isoformat().replace("+00:00", "Z"),
        "sample": True,
    }
    return [{
        "id": f"demo-web-{profile['slug']}",
        "url": url,
        "label": profile["website_label"],
        "last_scan": scan,
    }]
