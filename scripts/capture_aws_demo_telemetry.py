#!/usr/bin/env python3
"""
Capture real AWS telemetry from the ResilAI demo organizations into
industry fixtures used by the demo workspace.

Runs the same code paths a customer connector uses:
  * AWSSecurityHubConnector.sync()  -> Security Hub / GuardDuty findings
  * AWSDiscoveryService.fetch_aws_resources() -> EC2 / RDS / SSM inventory
  * IAM credential report                -> MFA / stale key hygiene

Findings and resources are split by the `Industry` tag (healthcare / legal)
so each demo organization only sees its own environment. Secrets never land
in the fixture: access keys, account-wide ARNs and IPs are left as recorded
resource identifiers only.

Usage:
  AWS_PROFILE=resilai-demo python3 scripts/capture_aws_demo_telemetry.py [--region us-east-1]
Writes:
  app/services/demo/fixtures/aws_healthcare.json
  app/services/demo/fixtures/aws_legal.json
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

FIXTURE_DIR = PROJECT_ROOT / "app" / "services" / "demo" / "fixtures"
INDUSTRIES = ("healthcare", "legal")
DEMO_STACK_SLUG = {"healthcare": "metro-health", "legal": "northstar-cole"}


def _session(region: str):
    import boto3
    return boto3.Session(region_name=region)


def _frozen_credentials(session, region: str) -> Dict[str, str]:
    creds = session.get_credentials()
    if not creds:
        raise SystemExit("No AWS credentials. Run: aws login --profile resilai-demo and set AWS_PROFILE.")
    frozen = creds.get_frozen_credentials()
    return {
        "aws_access_key_id": frozen.access_key,
        "aws_secret_access_key": frozen.secret_key,
        "aws_session_token": frozen.token or "",
        "aws_region": region,
    }


def _industry_of(resource_ids: List[str], tagged: Dict[str, str]) -> str | None:
    """Resolve the industry of a finding from its resource ids via the tag index."""
    for rid in resource_ids:
        for key, industry in tagged.items():
            if key and key in rid:
                return industry
    low = " ".join(resource_ids).lower()
    for industry, slug in DEMO_STACK_SLUG.items():
        if slug in low:
            return industry
    return None


def _tag_index(session) -> Dict[str, str]:
    """Map resource identifiers (instance ids, bucket names, SG ids, user names) -> industry."""
    index: Dict[str, str] = {}
    ec2 = session.client("ec2")
    for page in ec2.get_paginator("describe_instances").paginate(Filters=[{"Name": "tag:Environment", "Values": ["ResilAI-Demo-Org"]}]):
        for res in page.get("Reservations", []):
            for inst in res.get("Instances", []):
                tags = {t["Key"]: t["Value"] for t in inst.get("Tags", [])}
                if tags.get("Industry") in INDUSTRIES:
                    index[inst["InstanceId"]] = tags["Industry"]
                    for v in inst.get("BlockDeviceMappings", []):
                        vid = v.get("Ebs", {}).get("VolumeId")
                        if vid:
                            index[vid] = tags["Industry"]
    for sg in ec2.describe_security_groups(Filters=[{"Name": "tag:Environment", "Values": ["ResilAI-Demo-Org"]}]).get("SecurityGroups", []):
        tags = {t["Key"]: t["Value"] for t in sg.get("Tags", [])}
        if tags.get("Industry") in INDUSTRIES:
            index[sg["GroupId"]] = tags["Industry"]
    for vpc in ec2.describe_vpcs(Filters=[{"Name": "tag:Environment", "Values": ["ResilAI-Demo-Org"]}]).get("Vpcs", []):
        tags = {t["Key"]: t["Value"] for t in vpc.get("Tags", [])}
        if tags.get("Industry") in INDUSTRIES:
            index[vpc["VpcId"]] = tags["Industry"]
    s3 = session.client("s3")
    for b in s3.list_buckets().get("Buckets", []):
        name = b["Name"]
        for industry, slug in DEMO_STACK_SLUG.items():
            if f"resilai-{slug}-" in name:
                index[name] = industry
    iam = session.client("iam")
    for u in iam.list_users().get("Users", []):
        for industry, slug in DEMO_STACK_SLUG.items():
            if f"resilai-{slug}-" in u["UserName"]:
                index[u["UserName"]] = industry
    # Resources recorded by an earlier capture keep their industry even after
    # the stacks are torn down (Security Hub findings outlive the instances).
    for industry in INDUSTRIES:
        prior = FIXTURE_DIR / f"aws_{industry}.json"
        if prior.exists():
            try:
                for r in json.loads(prior.read_text(encoding="utf-8")).get("resources", []):
                    for k in ("instance_id", "identifier", "id", "name"):
                        if r.get(k):
                            index.setdefault(str(r[k]), industry)
            except Exception:
                pass
    return index


async def _sync_findings(credentials: Dict[str, str]) -> List[Dict[str, Any]]:
    from app.connectors.aws_security_hub import AWSSecurityHubConnector
    connector = AWSSecurityHubConnector(
        connector_id="demo-capture", org_id="demo-capture", credentials=credentials, config={}
    )
    if not await connector.authenticate():
        raise SystemExit("Security Hub authentication failed")
    events = await connector.sync()
    return [e.model_dump() if hasattr(e, "model_dump") else e.__dict__ for e in events]


def _inventory(session, region: str, credentials: Dict[str, str]) -> Dict[str, List[Dict[str, Any]]]:
    from app.services.discovery.aws_discovery import AWSDiscoveryService
    from app.services.discovery.discovery import SourceDiscoveryResult
    svc = AWSDiscoveryService(db=None, org_id="demo-capture", is_demo=False)
    result = SourceDiscoveryResult(source="aws")
    resources = svc.fetch_aws_resources(session, result)
    return {"resources": resources, "status": result.status, "denied_apis": list(result.denied_apis)}


def _credential_report(session) -> List[Dict[str, Any]]:
    iam = session.client("iam")
    for _ in range(12):
        state = iam.generate_credential_report().get("State")
        if state == "COMPLETE":
            break
        time.sleep(5)
    content = iam.get_credential_report()["Content"].decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(content)))
    users = []
    for r in rows:
        users.append({
            "user_name": r.get("user"),
            "mfa_active": r.get("mfa_active") == "true",
            "password_enabled": r.get("password_enabled") == "true",
            "password_last_used": r.get("password_last_used"),
            "access_key_1_active": r.get("access_key_1_active") == "true",
            "access_key_1_last_rotated": r.get("access_key_1_last_rotated"),
            "access_key_1_last_used_date": r.get("access_key_1_last_used_date"),
        })
    return users


import re

_KEY_RE = re.compile(r"\b(ASIA|AKIA)[0-9A-Z]{16}\b")
_SAMPLE_MARKERS = ("i-99999999", "generatedfinding", "generated finding")
_REDACT = {
    r"root/[a-z0-9._-]*stephanedev[a-z0-9._-]*": "Root/it-admin",
    r"iamuser/[a-z0-9._-]*jobagent[a-z0-9._-]*": "IAMUser/backup-automation",
    r"[a-z0-9._-]*stephanedev[a-z0-9._-]*": "it-admin",
    r"[a-z0-9._-]*jobagent[a-z0-9._-]*": "backup-automation",
}
_ACCOUNT_LEVEL = ("aws::::account", "arn:aws:iam::", "arn:aws:cloudtrail", "arn:aws:config", "arn:aws:securityhub", "arn:aws:kms", "arn:aws:ec2:us-east-1:")


def sanitize_finding(f: Dict[str, Any], tagged: Dict[str, str], account: str, slug: str) -> Dict[str, Any] | None:
    """Keep only findings about the demo environment, GuardDuty SAMPLE findings,
    or account-level controls; strip real principal names and access key ids.
    Returns None when the finding references something that is not part of
    the demo (another bucket, a real IAM user, a real temporary key)."""
    payload = dict(f.get("payload") or {})
    resources = [str(r) for r in (payload.get("resources") or [])]
    kept_resources: List[str] = []
    for r in resources:
        low = r.lower()
        if "aws::iam::accesskey" in low:
            continue  # real session keys are never part of the demo
        if any(m in low for m in _SAMPLE_MARKERS):
            kept_resources.append(r); continue
        if any(k.lower() in low for k in tagged.keys()) or f"resilai-{slug}" in low:
            kept_resources.append(r); continue
        if low == account or low.endswith(f":{account}") or any(low.startswith(a) for a in _ACCOUNT_LEVEL) and account in low and "resilai" in low:
            kept_resources.append(r); continue
        # EC2 resources (instances, security groups, volumes, VPCs) in this
        # account only exist for the demo stacks during a capture window.
        if low.startswith("arn:aws:ec2:") and account in low:
            kept_resources.append(r); continue
        if low.startswith("aws::::account") or low == f"arn:aws:iam::{account}:root" or f"{account}" == low:
            kept_resources.append(r); continue
        # anything else (foreign bucket, non-demo instance, other user) disqualifies the finding
        return None
    if not kept_resources and resources:
        return None
    payload["resources"] = kept_resources
    # Redact the operator's real principals/keys; the finding itself (what was
    # done to a demo resource) stays, attributed to a generic demo identity.
    for key in ("title", "description", "generator_id"):
        if isinstance(payload.get(key), str):
            text = _KEY_RE.sub("ASIADEMOKEY0000000000", payload[key])
            for real, fake in _REDACT.items():
                text = re.sub(real, fake, text, flags=re.IGNORECASE)
            payload[key] = text
    if any(bad in json.dumps(payload).lower() for bad in ("dropzone",)):
        return None  # foreign bucket activity is not part of the demo story
    out = dict(f)
    out["payload"] = payload
    return out


def sanitize_fixture(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    account = str(data.get("source", {}).get("account_id", ""))
    slug = data.get("org_slug", "")
    tagged = {}
    for r in data.get("resources", []):
        for k in ("instance_id", "identifier", "id", "name"):
            if r.get(k):
                tagged[str(r[k])] = data.get("industry")
    for u in data.get("iam_users", []):
        if (u.get("user_name") or "").startswith("resilai-"):
            tagged[u["user_name"]] = data.get("industry")
    before = len(data.get("securityhub_findings", []))
    cleaned = [x for x in (sanitize_finding(f, tagged, account, slug) for f in data.get("securityhub_findings", [])) if x]
    data["securityhub_findings"] = cleaned
    data["iam_users"] = [u for u in data.get("iam_users", []) if (u.get("user_name") or "").startswith("resilai-") or u.get("user_name") == "<root_account>"]
    data["counts"]["findings"] = len(cleaned)
    data["sanitized"] = True
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print(f"sanitized {path.name}: {before} -> {len(cleaned)} findings")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--sanitize-only", action="store_true", help="Re-sanitize existing fixtures without calling AWS")
    args = ap.parse_args()
    if args.sanitize_only:
        for industry in INDUSTRIES:
            sanitize_fixture(FIXTURE_DIR / f"aws_{industry}.json")
        return 0

    session = _session(args.region)
    account = session.client("sts").get_caller_identity()["Account"]
    credentials = _frozen_credentials(session, args.region)
    print(f"Account {account} region {args.region}")

    tagged = _tag_index(session)
    print(f"Tagged demo resources: {len(tagged)}")

    findings = asyncio.run(_sync_findings(credentials))
    print(f"Security Hub findings synced: {len(findings)}")

    inventory = _inventory(session, args.region, credentials)
    print(f"Inventory resources: {len(inventory['resources'])} status={inventory['status']} denied={inventory['denied_apis']}")

    users = _credential_report(session)
    print(f"IAM users in credential report: {len(users)}")

    captured_at = datetime.now(timezone.utc).isoformat()
    for industry in INDUSTRIES:
        slug = DEMO_STACK_SLUG[industry]
        ind_findings = []
        for f in findings:
            payload = f.get("payload", {})
            rids = payload.get("resources") or payload.get("resource_ids") or []
            if isinstance(rids, str):
                rids = [rids]
            ind = _industry_of([str(r) for r in rids], tagged)
            # Account-wide controls (Config, CloudTrail, root MFA, GuardDuty samples) apply to both demos
            if ind == industry or ind is None:
                ind_findings.append(f)
        ind_resources = [
            r for r in inventory["resources"]
            if tagged.get(str(r.get("instance_id") or r.get("identifier") or r.get("id") or ""), None) == industry
            or slug in json.dumps(r).lower()
        ]
        ind_users = [u for u in users if f"resilai-{slug}-" in (u.get("user_name") or "") or u.get("user_name") == "<root_account>"]
        fixture = {
            "industry": industry,
            "org_slug": slug,
            "captured_at": captured_at,
            "source": {"account_id": account, "region": args.region, "method": "AWSSecurityHubConnector.sync + AWSDiscoveryService.fetch_aws_resources + IAM credential report"},
            "securityhub_findings": ind_findings,
            "resources": ind_resources,
            "iam_users": ind_users,
            "counts": {"findings": len(ind_findings), "resources": len(ind_resources), "iam_users": len(ind_users)},
        }
        out = FIXTURE_DIR / f"aws_{industry}.json"
        out.write_text(json.dumps(fixture, indent=2, default=str), encoding="utf-8")
        print(f"wrote {out} findings={len(ind_findings)} resources={len(ind_resources)} users={len(ind_users)}")
        sanitize_fixture(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
