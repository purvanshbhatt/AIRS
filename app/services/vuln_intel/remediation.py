"""
Deterministic remediation text. Templates only: no LLM, nothing invented.

``build_steps`` answers, in order: how urgent, what to upgrade to, how to do
it on the platform the software runs on, who should do it, and how to
confirm it worked.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.services.vuln_intel.versions import newer_than

KEV_URGENCY = "Being exploited in the wild: patch within 48 hours."
_URGENCY = {
    "critical": "Critical severity: patch within 7 days.",
    "high": "High severity: patch within 14 days.",
    "medium": "Medium severity: patch within 30 days.",
    "low": "Low severity: patch in the next regular maintenance window.",
    "unknown": "Severity not rated yet: read the advisory and schedule the update.",
}

_ECOSYSTEM_COMMANDS = {
    "pypi": 'pip install --upgrade "{pkg}{pin}"',
    "npm": "npm install {pkg}{at}",
    "packagist": "composer update {pkg} --with-dependencies",
    "rubygems": "bundle update {pkg}",
}


@dataclass
class RemediationContext:
    """Where one affected copy of the software runs."""
    name: str
    version: Optional[str]
    asset: Optional[str] = None
    platform: Optional[str] = None        # apt | dnf | yum | apk | windows_update | macos_update | rds | lambda | web
    package: Optional[str] = None         # OS package name when known
    ecosystem: Optional[str] = None       # OSV ecosystem for libraries
    product_key: Optional[str] = None
    os_name: Optional[str] = None
    latest_version: Optional[str] = None  # latest supported release when known
    fixed_version: Optional[str] = None   # first release that fixes it for THIS copy


def urgency_line(severity: Optional[str], known_exploited: bool) -> str:
    if known_exploited:
        return KEV_URGENCY
    return _URGENCY.get((severity or "unknown").lower(), _URGENCY["unknown"])


def target_line(ctx: RemediationContext, fixed: Optional[str]) -> str:
    installed = f" from {ctx.version}" if ctx.version else ""
    if fixed:
        line = f"Upgrade {ctx.name}{installed} to {fixed} or later."
        if ctx.latest_version and newer_than(ctx.latest_version, fixed):
            line += f" The latest supported release is {ctx.latest_version}."
        return line
    if ctx.latest_version and newer_than(ctx.latest_version, ctx.version):
        return (f"The advisory does not name a fixed version. Upgrade {ctx.name}{installed} "
                f"to the latest supported release ({ctx.latest_version}).")
    return (f"The advisory does not name a fixed version yet. Check the vendor advisory linked below "
            f"for a patch or a workaround for {ctx.name}.")


def _where(ctx: RemediationContext) -> str:
    return f"On {ctx.asset}" if ctx.asset else "On each affected machine"


def how_line(ctx: RemediationContext, fixed: Optional[str]) -> str:
    """Platform-specific 'how to apply it' sentence."""
    pkg = ctx.package or (ctx.name or "").lower().replace(" ", "-")
    target = fixed or ctx.latest_version
    platform = (ctx.platform or "").lower()
    eco = (ctx.ecosystem or "").split(":", 1)[0].lower()

    if platform == "rds":
        version_part = f"engine version {target} or later" if target else "the newest minor engine version"
        return (f"Amazon RDS: in the AWS console open RDS > Databases > {ctx.asset or 'the instance'} > Modify, "
                f"choose {version_part} and apply it in the next maintenance window (or tick 'Apply immediately'). "
                f"Turn on 'Auto minor version upgrade' so minor fixes install by themselves.")
    if platform == "lambda":
        return (f"AWS Lambda: open the function {ctx.asset or ''} > Configuration > Runtime settings > Edit, "
                f"select a supported runtime, then redeploy and test the function.").replace("  ", " ")
    if platform == "web":
        site = ctx.asset or "your website"
        if ctx.product_key == "wordpress":
            return (f"Seen on your public website ({site}). In the WordPress admin open Dashboard > Updates, "
                    f"install the latest version and update plugins and themes at the same time.")
        return (f"Seen on your public website ({site}). Ask whoever hosts or maintains the site to update "
                f"{ctx.name} on the web server, then hide the version banner.")
    if eco in _ECOSYSTEM_COMMANDS:
        command = _ECOSYSTEM_COMMANDS[eco].format(
            pkg=pkg, pin=f">={target}" if target else "", at=f"@{target}" if target else "@latest",
        )
        return (f"In the application that uses it run `{command}`, rebuild and redeploy.")
    if eco in ("maven", "go", "nuget", "crates.io"):
        return (f"Raise the {ctx.name} version in the application's dependency file"
                f"{' to ' + target if target else ''}, rebuild and redeploy.")
    if platform == "apt":
        return (f"{_where(ctx)} ({ctx.os_name or 'Debian/Ubuntu'}): run "
                f"`sudo apt update && sudo apt install --only-upgrade {pkg}`, then restart the service.")
    if platform == "dnf":
        flag = " --releasever=latest" if (ctx.os_name or "").lower().startswith("amazon linux") else ""
        return (f"{_where(ctx)} ({ctx.os_name or 'RHEL-family Linux'}): run "
                f"`sudo dnf upgrade{flag} {pkg}`, then restart the service.")
    if platform == "yum":
        return (f"{_where(ctx)} ({ctx.os_name or 'Amazon Linux 2'}): run `sudo yum update {pkg}`, "
                f"then restart the service.")
    if platform == "apk":
        return f"{_where(ctx)} (Alpine): run `apk update && apk upgrade {pkg}` and rebuild any container image."
    if platform == "windows_update":
        return (f"{_where(ctx)} (Windows): install the update through Windows Update, or push it from "
                f"Microsoft Intune (Devices > Windows > Windows updates, or Apps for third-party software) "
                f"so every managed PC receives it.")
    if platform == "macos_update":
        return (f"{_where(ctx)} (macOS): install it from System Settings > General > Software Update, "
                f"or push it from Microsoft Intune / your MDM.")
    return f"{_where(ctx)}: install the vendor's update for {ctx.name} and restart it."


def who_line(contexts: List[RemediationContext]) -> str:
    if any((c.ecosystem or "").split(":", 1)[0].lower() in
           ("pypi", "npm", "packagist", "maven", "rubygems", "go", "nuget", "crates.io") for c in contexts):
        return ("Who: the developer or vendor who maintains the application, coordinated by your IT provider "
                "or MSP. Forward them this advisory.")
    return ("Who: your IT provider or MSP (administrator access is needed). Forward them this advisory.")


VERIFY_LINE = "Afterwards refresh this page: the item should show the new version and no open vulnerability."


def build_steps(
    severity: Optional[str],
    known_exploited: bool,
    contexts: List[RemediationContext],
) -> List[str]:
    """Ordered fix steps for one vulnerability across the places it was found."""
    steps: List[str] = [urgency_line(severity, known_exploited)]
    if not contexts:
        return steps

    # What to upgrade to: one line per distinct product + installed version.
    seen_targets: List[str] = []
    for ctx in contexts:
        line = target_line(ctx, ctx.fixed_version)
        if line not in seen_targets:
            seen_targets.append(line)
    steps.extend(seen_targets[:4])

    # How, once per distinct platform + asset.
    seen_how: List[str] = []
    for ctx in contexts:
        line = how_line(ctx, ctx.fixed_version)
        if line not in seen_how:
            seen_how.append(line)
    steps.extend(seen_how[:6])
    if len(seen_how) > 6:
        steps.append(f"Repeat on the other {len(seen_how) - 6} affected systems.")

    steps.append(who_line(contexts))
    steps.append(VERIFY_LINE)
    return steps


def remediation_text(steps: List[str]) -> str:
    return " ".join(steps)
