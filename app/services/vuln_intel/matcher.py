"""
Deterministic vulnerability matching.

A vulnerability is reported only when the installed version falls inside an
affected range published by the source (OSV ``affected[].ranges`` /
``versions``; NVD ``cpeMatch`` with ``versionStart*`` / ``versionEnd*``).
Anything we cannot evaluate is dropped, never assumed.
"""
from __future__ import annotations

import math
import re
from typing import Any, Callable, Dict, List, Optional

from app.services.vuln_intel.versions import (
    comparator_for,
    compare_versions,
    is_parseable,
    max_version,
)

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "unknown": 0}
MAX_SUMMARY = 320
MAX_REFERENCES = 6

_LABELS = {
    "critical": "critical", "high": "high", "important": "high",
    "moderate": "medium", "medium": "medium", "low": "low",
    "negligible": "low", "untriaged": "unknown", "none": "unknown",
}


def severity_from_score(score: Optional[float]) -> str:
    if score is None:
        return "unknown"
    if score >= 9.0:
        return "critical"
    if score >= 7.0:
        return "high"
    if score >= 4.0:
        return "medium"
    if score > 0:
        return "low"
    return "unknown"


def normalize_severity(label: Optional[str]) -> str:
    return _LABELS.get(str(label or "").strip().lower(), "unknown")


# ---------------------------------------------------------------------------
# CVSS v3.x base score from a vector string (OSV only ships the vector)
# ---------------------------------------------------------------------------

_CVSS3 = {
    "AV": {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2},
    "AC": {"L": 0.77, "H": 0.44},
    "UI": {"N": 0.85, "R": 0.62},
    "C": {"H": 0.56, "L": 0.22, "N": 0.0},
    "I": {"H": 0.56, "L": 0.22, "N": 0.0},
    "A": {"H": 0.56, "L": 0.22, "N": 0.0},
}


def _roundup(value: float) -> float:
    scaled = int(round(value * 100000))
    if scaled % 10000 == 0:
        return scaled / 100000.0
    return (math.floor(scaled / 10000) + 1) / 10.0


def cvss3_base_score(vector: Optional[str]) -> Optional[float]:
    if not vector or not str(vector).upper().startswith("CVSS:3"):
        return None
    try:
        parts = dict(p.split(":", 1) for p in str(vector).upper().split("/")[1:])
        scope_changed = parts["S"] == "C"
        pr_table = ({"N": 0.85, "L": 0.68, "H": 0.5} if scope_changed
                    else {"N": 0.85, "L": 0.62, "H": 0.27})
        iss = 1 - (1 - _CVSS3["C"][parts["C"]]) * (1 - _CVSS3["I"][parts["I"]]) * (1 - _CVSS3["A"][parts["A"]])
        impact = (7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15) if scope_changed else 6.42 * iss
        exploitability = (8.22 * _CVSS3["AV"][parts["AV"]] * _CVSS3["AC"][parts["AC"]]
                          * pr_table[parts["PR"]] * _CVSS3["UI"][parts["UI"]])
        if impact <= 0:
            return 0.0
        total = impact + exploitability
        if scope_changed:
            total *= 1.08
        return _roundup(min(total, 10.0))
    except (KeyError, ValueError):
        return None


def _clip(text: Optional[str]) -> str:
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text if len(text) <= MAX_SUMMARY else text[: MAX_SUMMARY - 1].rstrip() + "…"


def _iso(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        return text
    if re.match(r"^\d{4}-\d{2}-\d{2}T[\d:.]+$", text):
        return text + "Z"  # NVD timestamps are UTC without a suffix
    return text


# ---------------------------------------------------------------------------
# OSV
# ---------------------------------------------------------------------------

def _same_package(affected: Dict[str, Any], ecosystem: str, package: str) -> bool:
    pkg = affected.get("package") or {}
    name = str(pkg.get("name") or "").lower()
    eco = str(pkg.get("ecosystem") or "")
    if name != package.lower():
        return False
    # "Debian:12" queried, "Debian:12" stored; "PyPI" vs "PyPI". Compare the family
    # and, when both carry a release, the release too.
    a, b = eco.lower().split(":"), ecosystem.lower().split(":")
    if a[0] != b[0]:
        return False
    if len(a) > 1 and len(b) > 1 and a[1] != b[1]:
        return False
    return True


def osv_range_match(events: List[Dict[str, Any]], version: str,
                    cmp: Callable[[str, str], int] = compare_versions) -> Optional[Dict[str, Any]]:
    """Evaluate one OSV range. Returns {"fixed": str|None} when affected, else None."""
    affected = False
    fixed: Optional[str] = None
    for event in events or []:
        if "introduced" in event:
            intro = str(event["introduced"])
            if intro == "0" or cmp(version, intro) >= 0:
                affected, fixed = True, None
        elif "fixed" in event:
            if affected and cmp(version, str(event["fixed"])) >= 0:
                affected = False
            elif affected and fixed is None:
                fixed = str(event["fixed"])
        elif "last_affected" in event:
            if affected and cmp(version, str(event["last_affected"])) > 0:
                affected = False
        elif "limit" in event:
            if affected and cmp(version, str(event["limit"])) >= 0:
                affected = False
    return {"fixed": fixed} if affected else None


def reduce_osv_vuln(raw: Dict[str, Any], ecosystem: str, package: str, version: str) -> Dict[str, Any]:
    """Keep what matching needs from an OSV record (the cache stores this)."""
    ranges: List[Dict[str, Any]] = []
    listed = False
    for affected in raw.get("affected") or []:
        if not _same_package(affected, ecosystem, package):
            continue
        if version in (affected.get("versions") or []):
            listed = True
        for rng in affected.get("ranges") or []:
            if rng.get("type") in ("SEMVER", "ECOSYSTEM"):
                ranges.append({"type": rng.get("type"), "events": rng.get("events") or []})

    vector = None
    label = None
    for sev in raw.get("severity") or []:
        if str(sev.get("type", "")).upper().startswith("CVSS_V3"):
            vector = sev.get("score")
        elif sev.get("type") and not str(sev.get("type")).upper().startswith("CVSS"):
            label = sev.get("score")  # distro priority, e.g. Ubuntu "medium"
    dbs = raw.get("database_specific") or {}
    label = dbs.get("severity") or label

    aliases = [a for a in (raw.get("aliases") or []) if isinstance(a, str)]
    upstream = [a for a in (raw.get("upstream") or []) if isinstance(a, str)]
    refs = [r.get("url") for r in (raw.get("references") or []) if r.get("url")]
    return {
        "id": raw.get("id"),
        "aliases": aliases + upstream,
        "summary": _clip(raw.get("summary") or raw.get("details")),
        "published": raw.get("published"),
        "cvss_vector": vector,
        "severity_label": label,
        "references": refs[:MAX_REFERENCES],
        "ranges": ranges,
        "listed": listed,
    }


def _display_id(record: Dict[str, Any]) -> str:
    vid = str(record.get("id") or "")
    if vid.startswith("CVE-"):
        return vid
    for alias in record.get("aliases") or []:
        if alias.startswith("CVE-"):
            return alias
    return vid


def match_osv(records: List[Dict[str, Any]], version: str, ecosystem: str) -> List[Dict[str, Any]]:
    """Vulnerabilities from reduced OSV records that affect ``version``."""
    cmp = comparator_for(ecosystem)
    by_id: Dict[str, Dict[str, Any]] = {}
    for rec in records or []:
        fixes: List[Optional[str]] = []
        hit = bool(rec.get("listed"))
        for rng in rec.get("ranges") or []:
            try:
                result = osv_range_match(rng.get("events") or [], version, cmp)
            except Exception:
                result = None
            if result is not None:
                hit = True
                fixes.append(result.get("fixed"))
        if not hit:
            continue
        cvss = cvss3_base_score(rec.get("cvss_vector"))
        severity = severity_from_score(cvss) if cvss is not None else normalize_severity(rec.get("severity_label"))
        # Lowest fixed release that is still newer than the installed one.
        candidates = [f for f in fixes if f and cmp(f, version) > 0]
        fixed = None
        for cand in candidates:
            if fixed is None or cmp(cand, fixed) < 0:
                fixed = cand
        vuln = {
            "id": _display_id(rec),
            "severity": severity,
            "cvss": cvss,
            "summary": rec.get("summary") or "",
            "fixed_version": fixed,
            "published": _iso(rec.get("published")),
            "known_exploited": False,
            "references": list(rec.get("references") or []),
            "aliases": [rec.get("id")] + list(rec.get("aliases") or []),
        }
        existing = by_id.get(vuln["id"])
        if existing is None:
            by_id[vuln["id"]] = vuln
            continue
        # Same CVE reported by two databases (GHSA + PYSEC): keep the richer one.
        if SEVERITY_RANK[vuln["severity"]] > SEVERITY_RANK[existing["severity"]]:
            existing["severity"], existing["cvss"] = vuln["severity"], vuln["cvss"] or existing["cvss"]
        existing["cvss"] = existing["cvss"] if existing["cvss"] is not None else vuln["cvss"]
        existing["fixed_version"] = existing["fixed_version"] or vuln["fixed_version"]
        existing["summary"] = existing["summary"] or vuln["summary"]
        existing["published"] = existing["published"] or vuln["published"]
        for ref in vuln["references"]:
            if ref not in existing["references"] and len(existing["references"]) < MAX_REFERENCES:
                existing["references"].append(ref)
        existing["aliases"] = list(dict.fromkeys(existing["aliases"] + vuln["aliases"]))
    return list(by_id.values())


# ---------------------------------------------------------------------------
# NVD
# ---------------------------------------------------------------------------

def _cpe_parts(criteria: str) -> List[str]:
    parts = str(criteria or "").split(":")
    return parts + ["*"] * (13 - len(parts))


def _nvd_metric(metrics: Dict[str, Any]) -> (Optional[float], str):
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV40", "cvssMetricV2"):
        entries = metrics.get(key) or []
        if not entries:
            continue
        entry = next((e for e in entries if e.get("type") == "Primary"), entries[0])
        data = entry.get("cvssData") or {}
        score = data.get("baseScore")
        label = data.get("baseSeverity") or entry.get("baseSeverity")
        try:
            score = float(score) if score is not None else None
        except (TypeError, ValueError):
            score = None
        severity = normalize_severity(label)
        if severity == "unknown":
            severity = severity_from_score(score)
        return score, severity
    return None, "unknown"


def reduce_nvd_cve(raw: Dict[str, Any], vendor: str, product: str) -> Optional[Dict[str, Any]]:
    """Keep what matching needs from an NVD CVE item (``vulnerabilities[].cve``)."""
    cve = raw.get("cve") if "cve" in raw else raw
    if not cve or not cve.get("id"):
        return None
    if str(cve.get("vulnStatus") or "").lower() == "rejected":
        return None
    matches: List[Dict[str, Any]] = []
    requires_os: List[str] = []
    for config in cve.get("configurations") or []:
        config_matches: List[Dict[str, Any]] = []
        config_os: List[str] = []
        for node in config.get("nodes") or []:
            for m in node.get("cpeMatch") or []:
                parts = _cpe_parts(m.get("criteria"))
                if m.get("vulnerable") and parts[3] == vendor and parts[4] == product:
                    config_matches.append({
                        "version": parts[5], "update": parts[6],
                        "si": m.get("versionStartIncluding"), "se": m.get("versionStartExcluding"),
                        "ei": m.get("versionEndIncluding"), "ee": m.get("versionEndExcluding"),
                    })
                elif not m.get("vulnerable") and parts[2] == "o":
                    config_os.append(f"{parts[3]}:{parts[4]}")
        if config_matches:
            matches.extend(config_matches)
            if str(config.get("operator") or "").upper() == "AND":
                requires_os.extend(config_os)
    if not matches:
        return None
    description = ""
    for d in cve.get("descriptions") or []:
        if d.get("lang") == "en":
            description = d.get("value") or ""
            break
    score, severity = _nvd_metric(cve.get("metrics") or {})
    refs = [r.get("url") for r in (cve.get("references") or []) if r.get("url")]
    return {
        "id": cve["id"],
        "summary": _clip(description),
        "published": cve.get("published"),
        "cvss": score,
        "severity": severity,
        "references": [f"https://nvd.nist.gov/vuln/detail/{cve['id']}"] + refs[: MAX_REFERENCES - 1],
        "matches": matches,
        "requires_os": sorted(set(requires_os)),
    }


def nvd_cpe_match(match: Dict[str, Any], version: str) -> Optional[Dict[str, Any]]:
    """Evaluate one reduced cpeMatch. Returns {"fixed": str|None} when affected, else None."""
    crit_version = str(match.get("version") or "*")
    si, se, ei, ee = match.get("si"), match.get("se"), match.get("ei"), match.get("ee")
    if crit_version in ("*", "-"):
        if si and compare_versions(version, si) < 0:
            return None
        if se and compare_versions(version, se) <= 0:
            return None
        if ei and compare_versions(version, ei) > 0:
            return None
        if ee and compare_versions(version, ee) >= 0:
            return None
        if crit_version == "-" and not any((si, se, ei, ee)):
            return None  # "version not applicable": nothing to compare against
        return {"fixed": ee}
    update = str(match.get("update") or "*")
    if update not in ("*", "-", "") and update.lower() not in version.lower():
        return None  # e.g. 8.5.0:rc1 does not describe the 8.5.0 release
    if compare_versions(version, crit_version) == 0:
        return {"fixed": None}
    return None


_OS_FAMILY_HINTS = {
    "windows": ("microsoft:windows",),
    "macos": ("apple:mac", "apple:macos"),
    "ubuntu": ("canonical:ubuntu", "linux:linux_kernel", "debian:debian"),
    "debian": ("debian:debian", "linux:linux_kernel"),
    "amazon": ("amazon:linux", "linux:linux_kernel", "redhat:", "fedoraproject:"),
    "rhel": ("redhat:", "fedoraproject:", "centos:", "linux:linux_kernel", "oracle:linux", "rocky"),
    "alpine": ("alpinelinux:", "linux:linux_kernel"),
}


def _os_applies(requires_os: List[str], os_family: Optional[str]) -> bool:
    if not requires_os or not os_family:
        return True  # no platform condition, or we do not know the host OS
    hints = _OS_FAMILY_HINTS.get(os_family)
    if not hints:
        return True
    return any(req.startswith(h) for req in requires_os for h in hints)


def match_nvd(records: List[Dict[str, Any]], version: str, os_family: Optional[str] = None) -> List[Dict[str, Any]]:
    """Vulnerabilities from reduced NVD records whose CPE range contains ``version``."""
    out: List[Dict[str, Any]] = []
    if not is_parseable(version):
        return out
    for rec in records or []:
        if not _os_applies(rec.get("requires_os") or [], os_family):
            continue
        fixes: List[Optional[str]] = []
        hit = False
        for m in rec.get("matches") or []:
            result = nvd_cpe_match(m, version)
            if result is not None:
                hit = True
                fixes.append(result.get("fixed"))
        if not hit:
            continue
        newer = [f for f in fixes if f and compare_versions(f, version) > 0]
        fixed = None
        for cand in newer:
            if fixed is None or compare_versions(cand, fixed) < 0:
                fixed = cand
        out.append({
            "id": rec["id"],
            "severity": rec.get("severity") or "unknown",
            "cvss": rec.get("cvss"),
            "summary": rec.get("summary") or "",
            "fixed_version": fixed,
            "published": _iso(rec.get("published")),
            "known_exploited": False,
            "references": list(rec.get("references") or []),
            "aliases": [rec["id"]],
        })
    return out


def sort_vulnerabilities(vulns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Known-exploited first, then severity, then newest."""
    return sorted(
        vulns,
        key=lambda v: (
            0 if v.get("known_exploited") else 1,
            -SEVERITY_RANK.get(v.get("severity") or "unknown", 0),
            _neg_date(v.get("published")),
            v.get("id") or "",
        ),
    )


def _neg_date(value: Optional[str]) -> str:
    # Sort newest first with a plain string key: invert each digit.
    text = (value or "0000-00-00")[:19]
    return "".join(str(9 - int(c)) if c.isdigit() else c for c in text)


def highest_fixed(vulns: List[Dict[str, Any]]) -> Optional[str]:
    """The release that clears every listed vulnerability with a known fix."""
    return max_version([v.get("fixed_version") for v in vulns])
