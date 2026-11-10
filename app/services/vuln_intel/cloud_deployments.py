"""
What is deployed in the organization's AWS account, and what looks risky.

Read-only ``List*`` / ``Describe*`` / ``Get*`` calls through the org's AWS
connector (same credentials and session builder as discovery). Each API is
guarded on its own: an AccessDenied on one service is recorded in
``sources`` and the others still run. No connector means an empty list and
``sources == {"aws": "not_connected"}``. Nothing is ever invented.

Scope: the connector's region, plus the global services (CloudFront, S3).
"""
from __future__ import annotations

import logging
import time
from datetime import date, datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from app.services.discovery.aws_discovery import (
    AWSDiscoveryService,
    _client_error_code,
    _is_access_denied,
    build_boto3_session,
)

logger = logging.getLogger("airs.vuln_intel.cloud")

LAMBDA_EOL_SLUG = "aws-lambda"
MAX_PAGES = 20
MAX_BUCKETS = 50
S3_BUDGET_SECONDS = 6.0

# Runtimes AWS has already deprecated (used only when endoflife.date is unreachable).
_DEPRECATED_RUNTIMES_FALLBACK = {
    "python2.7", "python3.6", "python3.7", "python3.8",
    "nodejs", "nodejs4.3", "nodejs4.3-edge", "nodejs6.10", "nodejs8.10", "nodejs10.x",
    "nodejs12.x", "nodejs14.x", "nodejs16.x",
    "ruby2.5", "ruby2.7", "dotnetcore1.0", "dotnetcore2.0", "dotnetcore2.1", "dotnetcore3.1",
    "dotnet5.0", "dotnet6", "go1.x", "java8",
}
_WEAK_TLS_POLICIES = ("ELBSecurityPolicy-2015-05", "ELBSecurityPolicy-2016-08", "ELBSecurityPolicy-TLS-1-0",
                      "ELBSecurityPolicy-TLS-1-1", "ELBSecurityPolicy-FS-2018-06")
_WEAK_CLOUDFRONT_TLS = ("SSLv3", "TLSv1", "TLSv1_2016", "TLSv1.1_2016")


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _pages(call: Callable[..., Dict[str, Any]], result_key: str, in_token: str, out_token: str,
           **kwargs: Any) -> List[Any]:
    items: List[Any] = []
    token: Optional[str] = None
    for _ in range(MAX_PAGES):
        params = dict(kwargs)
        if token:
            params[in_token] = token
        response = call(**params) or {}
        items.extend(response.get(result_key) or [])
        token = response.get(out_token)
        if not token:
            break
    return items


def lambda_runtime_issue(runtime: Optional[str], cycles: Optional[List[Dict[str, Any]]],
                         today: date) -> Optional[Dict[str, str]]:
    """Issue for a deprecated Lambda runtime, from endoflife.date ``aws-lambda`` cycles."""
    if not runtime:
        return None
    fix = ("Change the function to a supported runtime (Lambda console > Configuration > Runtime settings > "
           "Edit), then redeploy and test. Who: the developer or your IT provider.")
    if cycles:
        cycle = next((c for c in cycles if str(c.get("cycle", "")).lower() == runtime.lower()), None)
        if cycle is None:
            return None

        def _passed(value: Any) -> Optional[str]:
            if value is True:
                return "already"
            if isinstance(value, str):
                try:
                    return value if date.fromisoformat(value[:10]) <= today else None
                except ValueError:
                    return None
            return None

        blocked = _passed(cycle.get("eol"))
        deprecated = _passed(cycle.get("support"))
        if blocked:
            return {"title": f"Runtime {runtime} is retired: AWS no longer allows updates to this function"
                             + (f" (since {blocked})" if blocked != "already" else ""),
                    "severity": "high", "fix": fix}
        if deprecated:
            return {"title": f"Runtime {runtime} is deprecated and no longer receives security patches"
                             + (f" (since {deprecated})" if deprecated != "already" else ""),
                    "severity": "medium", "fix": fix}
        return None
    if runtime.lower() in _DEPRECATED_RUNTIMES_FALLBACK:
        return {"title": f"Runtime {runtime} is deprecated and no longer receives security patches",
                "severity": "medium", "fix": fix}
    return None


def lambda_runtime_cycles(db: Session, clients: Any = None) -> Optional[List[Dict[str, Any]]]:
    """endoflife.date cycles for AWS Lambda runtimes (cached 24 h, stale copy on failure)."""
    from app.services.vuln_intel.cache import IntelCache
    from app.services.vuln_intel.clients import Deadline
    from app.services.vuln_intel.service import IntelClients

    cache = IntelCache(db)
    key = f"eol:{LAMBDA_EOL_SLUG}"
    now = datetime.now(timezone.utc)
    entry = cache.get(key)
    if entry is not None and entry.is_fresh(now):
        return entry.payload or None
    try:
        clients = clients or IntelClients.default()
        payload = clients.eol.fetch(LAMBDA_EOL_SLUG, deadline=Deadline(4.0))
        cache.set(key, "endoflife", payload, now=now)
        return payload or None
    except Exception as exc:
        logger.info("Lambda runtime lifecycle unavailable: %s", exc)
        return (entry.payload or None) if entry is not None else None


class CloudDeploymentCollector:
    def __init__(
        self,
        db: Session,
        org_id: str,
        session_factory: Optional[Callable[[Dict[str, Any], Dict[str, Any], str], Any]] = None,
        lambda_cycles: Any = None,
        today: Optional[date] = None,
    ):
        """``lambda_cycles``: endoflife.date ``aws-lambda`` cycles, or a callable returning
        them (called only when a Lambda function is actually found)."""
        self.db = db
        self.org_id = org_id
        self._session_factory = session_factory or build_boto3_session
        self._lambda_cycles_source = lambda_cycles
        self._lambda_cycles_loaded = not callable(lambda_cycles)
        self._lambda_cycles_value = None if callable(lambda_cycles) else lambda_cycles
        self._today = today or datetime.now(timezone.utc).date()

    @property
    def _lambda_cycles(self) -> Optional[List[Dict[str, Any]]]:
        if not self._lambda_cycles_loaded:
            self._lambda_cycles_loaded = True
            try:
                self._lambda_cycles_value = self._lambda_cycles_source()
            except Exception as exc:
                logger.info("Lambda runtime lifecycle lookup failed: %s", exc)
                self._lambda_cycles_value = None
        return self._lambda_cycles_value

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _client(session: Any, name: str, region: Optional[str] = None) -> Any:
        kwargs: Dict[str, Any] = {}
        if region:
            kwargs["region_name"] = region
        try:
            from botocore.config import Config
            kwargs["config"] = Config(connect_timeout=4, read_timeout=8, retries={"max_attempts": 2})
        except Exception:  # botocore missing: stub sessions in tests
            pass
        try:
            return session.client(name, **kwargs)
        except TypeError:
            return session.client(name)

    def _guard(self, api: str, sources: Dict[str, str], fn: Callable[[], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        try:
            found = fn()
            sources[api] = "ok"
            return found
        except Exception as exc:
            if _is_access_denied(exc):
                sources[api] = "permission_missing"
            else:
                code = _client_error_code(exc) or type(exc).__name__
                sources[api] = f"error: {code}"
                logger.warning("%s failed for org %s: %s", api, self.org_id, exc)
            return []

    @staticmethod
    def _dep(dtype: str, name: str, region: Optional[str], runtime: Optional[str] = None,
             version: Optional[str] = None, public: Optional[bool] = None,
             issues: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        return {
            "id": f"{dtype}:{region or 'global'}:{name}",
            "type": dtype,
            "name": name,
            "provider": "aws",
            "region": region or "global",
            "runtime": runtime,
            "version": version,
            "public": public,
            "issues": issues or [],
        }

    # -- per service -----------------------------------------------------------

    def _lambda(self, session: Any, region: str) -> List[Dict[str, Any]]:
        client = self._client(session, "lambda")
        out = []
        for fn in _pages(client.list_functions, "Functions", "Marker", "NextMarker"):
            runtime = fn.get("Runtime")
            issue = lambda_runtime_issue(runtime, self._lambda_cycles, self._today)
            out.append(self._dep("lambda", fn.get("FunctionName") or "unknown", region, runtime=runtime,
                                 version=fn.get("Version"), public=None, issues=[issue] if issue else []))
        return out

    def _rds(self, session: Any, region: str) -> List[Dict[str, Any]]:
        client = self._client(session, "rds")
        out = []
        for dbi in _pages(client.describe_db_instances, "DBInstances", "Marker", "Marker"):
            issues: List[Dict[str, str]] = []
            public = bool(dbi.get("PubliclyAccessible"))
            if public:
                issues.append({
                    "title": "Database is reachable from the internet", "severity": "high",
                    "fix": "RDS console > Modify > Connectivity > set 'Public access' to No, and restrict the "
                           "security group to the application servers.",
                })
            if dbi.get("StorageEncrypted") is False:
                issues.append({
                    "title": "Database storage is not encrypted", "severity": "medium",
                    "fix": "Take a snapshot, copy it with encryption enabled and restore from the encrypted copy.",
                })
            if dbi.get("AutoMinorVersionUpgrade") is False:
                issues.append({
                    "title": "Automatic minor version upgrades are off", "severity": "low",
                    "fix": "RDS console > Modify > enable 'Auto minor version upgrade' so security patches "
                           "install in the maintenance window.",
                })
            out.append(self._dep("rds", dbi.get("DBInstanceIdentifier") or "unknown", region,
                                 runtime=dbi.get("Engine"), version=dbi.get("EngineVersion"),
                                 public=public, issues=issues))
        return out

    def _ec2(self, session: Any, region: str) -> List[Dict[str, Any]]:
        client = self._client(session, "ec2")
        out = []
        for reservation in _pages(client.describe_instances, "Reservations", "NextToken", "NextToken"):
            for inst in reservation.get("Instances") or []:
                state = (inst.get("State") or {}).get("Name")
                if state not in ("running", "stopped"):
                    continue
                name = next((t.get("Value") for t in inst.get("Tags") or [] if t.get("Key") == "Name"), None)
                issues: List[Dict[str, str]] = []
                if (inst.get("MetadataOptions") or {}).get("HttpTokens") == "optional":
                    issues.append({
                        "title": "Instance metadata service v1 is still allowed", "severity": "medium",
                        "fix": "Require IMDSv2: EC2 console > Instance > Actions > Instance settings > "
                               "Modify instance metadata options > IMDSv2 'Required'.",
                    })
                out.append(self._dep("ec2", name or inst.get("InstanceId") or "unknown", region,
                                     runtime=inst.get("PlatformDetails") or inst.get("Platform"),
                                     version=inst.get("InstanceType"),
                                     public=bool(inst.get("PublicIpAddress")), issues=issues))
        return out

    def _load_balancers(self, session: Any, region: str) -> List[Dict[str, Any]]:
        client = self._client(session, "elbv2")
        out = []
        balancers = _pages(client.describe_load_balancers, "LoadBalancers", "Marker", "NextMarker")
        for index, lb in enumerate(balancers):
            public = lb.get("Scheme") == "internet-facing"
            issues: List[Dict[str, str]] = []
            if public and index < 20 and lb.get("LoadBalancerArn"):
                try:
                    listeners = _pages(client.describe_listeners, "Listeners", "Marker", "NextMarker",
                                       LoadBalancerArn=lb["LoadBalancerArn"])
                except Exception as exc:
                    listeners = []
                    logger.debug("describe_listeners failed: %s", exc)
                for listener in listeners:
                    protocol = listener.get("Protocol")
                    actions = [a.get("Type") for a in listener.get("DefaultActions") or []]
                    if protocol == "HTTP" and "redirect" not in actions:
                        issues.append({
                            "title": f"Port {listener.get('Port')} serves plain HTTP without redirecting to HTTPS",
                            "severity": "medium",
                            "fix": "Change the HTTP listener's default action to 'Redirect to HTTPS 443'.",
                        })
                    if protocol in ("HTTPS", "TLS") and listener.get("SslPolicy") in _WEAK_TLS_POLICIES:
                        issues.append({
                            "title": f"Listener allows outdated TLS versions ({listener.get('SslPolicy')})",
                            "severity": "medium",
                            "fix": "Switch the listener's security policy to ELBSecurityPolicy-TLS13-1-2-2021-06.",
                        })
            out.append(self._dep("load_balancer", lb.get("LoadBalancerName") or "unknown", region,
                                 runtime=lb.get("Type"), version=None, public=public, issues=issues))
        return out

    def _cloudfront(self, session: Any, region: str) -> List[Dict[str, Any]]:
        client = self._client(session, "cloudfront")
        out = []
        marker: Optional[str] = None
        for _ in range(MAX_PAGES):
            response = client.list_distributions(**({"Marker": marker} if marker else {})) or {}
            dist_list = response.get("DistributionList") or {}
            for dist in dist_list.get("Items") or []:
                issues: List[Dict[str, str]] = []
                policy = (dist.get("DefaultCacheBehavior") or {}).get("ViewerProtocolPolicy")
                if policy == "allow-all":
                    issues.append({
                        "title": "Visitors can load the site over plain HTTP", "severity": "medium",
                        "fix": "CloudFront > Behaviors > Edit > Viewer protocol policy: 'Redirect HTTP to HTTPS'.",
                    })
                min_tls = (dist.get("ViewerCertificate") or {}).get("MinimumProtocolVersion")
                if min_tls in _WEAK_CLOUDFRONT_TLS:
                    issues.append({
                        "title": f"Distribution allows outdated TLS versions ({min_tls})", "severity": "medium",
                        "fix": "CloudFront > Settings > Security policy: choose TLSv1.2_2021 or newer.",
                    })
                aliases = (dist.get("Aliases") or {}).get("Items") or []
                name = aliases[0] if aliases else (dist.get("DomainName") or dist.get("Id") or "unknown")
                out.append(self._dep("cloudfront", name, None, runtime=None, version=dist.get("HttpVersion"),
                                     public=bool(dist.get("Enabled", True)), issues=issues))
            marker = dist_list.get("NextMarker") if dist_list.get("IsTruncated") else None
            if not marker:
                break
        return out

    def _api_gateway_rest(self, session: Any, region: str) -> List[Dict[str, Any]]:
        client = self._client(session, "apigateway")
        out = []
        for api in _pages(client.get_rest_apis, "items", "position", "position"):
            types = (api.get("endpointConfiguration") or {}).get("types") or []
            out.append(self._dep("api_gateway", api.get("name") or api.get("id") or "unknown", region,
                                 runtime="REST", version=api.get("version"),
                                 public=("PRIVATE" not in types) if types else None))
        return out

    def _api_gateway_http(self, session: Any, region: str) -> List[Dict[str, Any]]:
        client = self._client(session, "apigatewayv2")
        out = []
        for api in _pages(client.get_apis, "Items", "NextToken", "NextToken"):
            out.append(self._dep("api_gateway", api.get("Name") or api.get("ApiId") or "unknown", region,
                                 runtime=api.get("ProtocolType"), version=api.get("Version"), public=True))
        return out

    def _s3_websites(self, session: Any, region: str) -> List[Dict[str, Any]]:
        client = self._client(session, "s3")
        buckets = (client.list_buckets() or {}).get("Buckets") or []
        out = []
        started = time.monotonic()
        denied: Optional[BaseException] = None
        checked = 0
        for bucket in buckets[:MAX_BUCKETS]:
            if time.monotonic() - started > S3_BUDGET_SECONDS:
                break
            name = bucket.get("Name")
            if not name:
                continue
            checked += 1
            try:
                website = client.get_bucket_website(Bucket=name) or {}
            except Exception as exc:
                if _is_access_denied(exc):
                    denied = exc
                continue  # NoSuchWebsiteConfiguration, cross-region redirect, deleted bucket
            if not (website.get("IndexDocument") or website.get("RedirectAllRequestsTo")):
                continue
            out.append(self._dep("s3_website", name, bucket.get("BucketRegion"), runtime="static website",
                                 public=None, issues=[{
                                     "title": "S3 website endpoints serve plain HTTP only",
                                     "severity": "medium",
                                     "fix": "Put CloudFront in front of the bucket with an HTTPS certificate and "
                                            "block direct public access to the bucket.",
                                 }]))
        if denied is not None and not out:
            raise denied  # s3:GetBucketWebsite is not granted: report it instead of "no websites"
        return out

    def _ecs(self, session: Any, region: str) -> List[Dict[str, Any]]:
        client = self._client(session, "ecs")
        out = []
        for cluster in _pages(client.list_clusters, "clusterArns", "nextToken", "nextToken")[:20]:
            arns = _pages(client.list_services, "serviceArns", "nextToken", "nextToken", cluster=cluster)
            for start in range(0, min(len(arns), 100), 10):
                described = client.describe_services(cluster=cluster, services=arns[start:start + 10]) or {}
                for svc in described.get("services") or []:
                    vpc = (svc.get("networkConfiguration") or {}).get("awsvpcConfiguration") or {}
                    assign = vpc.get("assignPublicIp")
                    out.append(self._dep("ecs_service", svc.get("serviceName") or "unknown", region,
                                         runtime=svc.get("launchType") or "capacity provider",
                                         version=svc.get("platformVersion"),
                                         public=(assign == "ENABLED") if assign else None))
        return out

    def _app_runner(self, session: Any, region: str) -> List[Dict[str, Any]]:
        client = self._client(session, "apprunner")
        out = []
        for svc in _pages(client.list_services, "ServiceSummaryList", "NextToken", "NextToken"):
            out.append(self._dep("app_runner", svc.get("ServiceName") or "unknown", region,
                                 runtime=None, version=None, public=None))
        return out

    def _beanstalk(self, session: Any, region: str) -> List[Dict[str, Any]]:
        client = self._client(session, "elasticbeanstalk")
        out = []
        for env in _pages(client.describe_environments, "Environments", "NextToken", "NextToken"):
            if env.get("Status") == "Terminated":
                continue
            tier = (env.get("Tier") or {}).get("Name")
            out.append(self._dep("elastic_beanstalk", env.get("EnvironmentName") or "unknown", region,
                                 runtime=env.get("SolutionStackName"), version=env.get("VersionLabel"),
                                 public=bool(env.get("CNAME")) if tier != "Worker" else False))
        return out

    # -- entry point -------------------------------------------------------------

    def collect(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        sources: Dict[str, str] = {}
        deployments: List[Dict[str, Any]] = []

        try:
            connectors = AWSDiscoveryService(self.db, self.org_id, is_demo=False)._load_aws_connectors()
        except Exception as exc:
            logger.error("Loading AWS connectors failed for org %s: %s", self.org_id, exc)
            return {"deployments": [], "sources": {"aws": "error"}, "collected_at": _iso(now)}
        if not connectors:
            return {"deployments": [], "sources": {"aws": "not_connected"}, "collected_at": _iso(now)}

        auth_failed = False
        seen_ids = set()
        for connector in connectors:
            try:
                session = self._session_factory(connector["credentials"], connector["config"], connector["id"])
            except ImportError:
                sources["aws"] = "error"
                continue
            except Exception as exc:
                auth_failed = True
                logger.warning("AWS session build failed for connector %s: %s", connector["id"], exc)
                continue
            region = getattr(session, "region_name", None) or (connector["credentials"] or {}).get("aws_region") \
                or (connector["config"] or {}).get("aws_region") or "us-east-1"
            steps = [
                ("lambda:ListFunctions", self._lambda),
                ("rds:DescribeDBInstances", self._rds),
                ("ec2:DescribeInstances", self._ec2),
                ("elasticloadbalancing:DescribeLoadBalancers", self._load_balancers),
                ("cloudfront:ListDistributions", self._cloudfront),
                ("apigateway:GET /restapis", self._api_gateway_rest),
                ("apigateway:GET /apis", self._api_gateway_http),
                ("s3:GetBucketWebsite", self._s3_websites),
                ("ecs:DescribeServices", self._ecs),
                ("apprunner:ListServices", self._app_runner),
                ("elasticbeanstalk:DescribeEnvironments", self._beanstalk),
            ]
            for api, fn in steps:
                for dep in self._guard(api, sources, lambda fn=fn: fn(session, region)):
                    if dep["id"] not in seen_ids:
                        seen_ids.add(dep["id"])
                        deployments.append(dep)

        api_states = [v for k, v in sources.items() if k != "aws"]
        if "aws" not in sources:
            if not api_states:
                sources["aws"] = "auth_failed" if auth_failed else "error"
            elif all(v == "ok" for v in api_states):
                sources["aws"] = "ok"
            elif all(v == "permission_missing" for v in api_states):
                sources["aws"] = "permission_missing"
            else:
                sources["aws"] = "partial"
        deployments.sort(key=lambda d: (-len(d["issues"]), d["type"], d["name"]))
        return {"deployments": deployments, "sources": sources, "collected_at": _iso(now)}


def demo_deployments(org_id: str, lambda_cycles: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Deployments of the recorded AWS demo environment (EC2 servers from the capture),
    plus two clearly labelled sample resources so the view shows every column."""
    from app.services.demo.demo_stack import demo_profile
    from app.services.demo.aws_demo_telemetry import load_recorded_fixture

    now = datetime.now(timezone.utc)
    profile = demo_profile(org_id)
    fixture = load_recorded_fixture(profile["industry"]) or {}
    region = (fixture.get("source") or {}).get("region") or "us-east-1"
    dep = CloudDeploymentCollector._dep
    deployments: List[Dict[str, Any]] = []
    for res in fixture.get("resources") or []:
        if res.get("kind") != "ec2_instance":
            continue
        issues = []
        if res.get("imdsv2") == "optional":
            issues.append({"title": "Instance metadata service v1 is still allowed", "severity": "medium",
                           "fix": "Require IMDSv2 in the instance metadata options."})
        deployments.append(dep("ec2", res.get("name") or res.get("instance_id"), region,
                               runtime=res.get("platform"), version=res.get("instance_type"),
                               public=bool(res.get("public_ip")), issues=issues))
    slug = profile["slug"]
    runtime = "python3.8"
    issue = lambda_runtime_issue(runtime, lambda_cycles, now.date())
    deployments.append(dep("lambda", f"{slug}-appointment-reminders (sample)" if profile["industry"] == "healthcare"
                           else f"{slug}-document-intake (sample)", region, runtime=runtime, version="$LATEST",
                           public=None, issues=[issue] if issue else []))
    deployments.append(dep("load_balancer", f"{slug}-portal-alb (sample)", region, runtime="application",
                           public=True, issues=[{
                               "title": "Port 80 serves plain HTTP without redirecting to HTTPS",
                               "severity": "medium",
                               "fix": "Change the HTTP listener's default action to 'Redirect to HTTPS 443'.",
                           }]))
    deployments.sort(key=lambda d: (-len(d["issues"]), d["type"], d["name"]))
    return {"deployments": deployments, "sources": {"aws": "demo"}, "collected_at": _iso(now)}
