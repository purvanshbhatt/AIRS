"""
Version parsing and comparison (deterministic, dependency-free).

``compare_versions`` is a tolerant generic comparator good enough for semver,
PEP 440, Maven, RubyGems, Go and upstream release numbers. ``dpkg_compare``
implements the Debian policy algorithm for Debian/Ubuntu package versions.
"""
from __future__ import annotations

import re
from typing import List, Optional, Tuple

# Tags that sort BEFORE the plain release ("1.0rc1" < "1.0").
_PRE_RELEASE = {
    "dev": -5, "snapshot": -5, "nightly": -5,
    "alpha": -4, "a": -4,
    "beta": -3, "b": -3,
    "m": -2, "milestone": -2, "pre": -2, "preview": -2,
    "rc": -1, "c": -1, "cr": -1,
}

_TOKEN_RE = re.compile(r"\d+|[a-z]+")
_UPSTREAM_RE = re.compile(r"^(?:\d+:)?v?(\d+(?:\.\d+)*(?:[a-z]\d*)?)", re.IGNORECASE)


def _tokens(version: str) -> List[Tuple[int, object]]:
    text = str(version or "").strip().lower()
    if ":" in text and text.split(":", 1)[0].isdigit():  # epoch
        text = text.split(":", 1)[1]
    text = text.split("+", 1)[0]  # build metadata never orders
    if text.startswith("v") and len(text) > 1 and text[1].isdigit():
        text = text[1:]
    out: List[Tuple[int, object]] = []
    for tok in _TOKEN_RE.findall(text):
        if tok.isdigit():
            out.append((1, int(tok)))
        elif tok in _PRE_RELEASE:
            out.append((0, _PRE_RELEASE[tok]))
        else:
            out.append((2, tok))  # post-release / patch letter ("1.0.2k", "-r7", "p1")
    return out


_END = (1, 0)  # a missing component equals numeric zero: 1.0 == 1.0.0


def compare_versions(a: str, b: str) -> int:
    """Return -1, 0 or 1. Unknown / empty versions compare as equal to themselves only."""
    ta, tb = _tokens(a), _tokens(b)
    for i in range(max(len(ta), len(tb))):
        xa = ta[i] if i < len(ta) else _END
        xb = tb[i] if i < len(tb) else _END
        if xa == xb:
            continue
        if xa[0] != xb[0]:
            return -1 if xa[0] < xb[0] else 1
        return -1 if xa[1] < xb[1] else 1  # type: ignore[operator]
    return 0


def is_parseable(version: Optional[str]) -> bool:
    return bool(version) and any(t[0] == 1 for t in _tokens(str(version)))


def clean_upstream_version(version: Optional[str]) -> Optional[str]:
    """Upstream release number without epoch / distro revision.

    "1:2.4.52-1ubuntu4.7" -> "2.4.52", "3.0.8-1.amzn2023.0.14" -> "3.0.8",
    "v18.19.0" -> "18.19.0", "1.1.1k-1+deb11u1" -> "1.1.1k".
    """
    if not version:
        return None
    match = _UPSTREAM_RE.match(str(version).strip())
    return match.group(1).lower() if match else None


def newer_than(candidate: Optional[str], installed: Optional[str]) -> bool:
    if not is_parseable(candidate) or not is_parseable(installed):
        return False
    return compare_versions(str(candidate), str(installed)) > 0


def max_version(versions: List[Optional[str]]) -> Optional[str]:
    best: Optional[str] = None
    for v in versions:
        if not is_parseable(v):
            continue
        if best is None or compare_versions(str(v), best) > 0:
            best = str(v)
    return best


# ---------------------------------------------------------------------------
# Debian / Ubuntu (dpkg) ordering
# ---------------------------------------------------------------------------

def _dpkg_split(version: str) -> Tuple[int, str, str]:
    text = str(version or "").strip()
    epoch = 0
    if ":" in text:
        head, rest = text.split(":", 1)
        if head.isdigit():
            epoch, text = int(head), rest
    if "-" in text:
        upstream, revision = text.rsplit("-", 1)
    else:
        upstream, revision = text, ""
    return epoch, upstream, revision


def _dpkg_order(ch: str) -> int:
    if ch == "~":
        return -1
    if not ch:
        return 0
    if ch.isalpha():
        return ord(ch)
    return ord(ch) + 256


def _dpkg_cmp_part(a: str, b: str) -> int:
    ia = ib = 0
    while ia < len(a) or ib < len(b):
        # non-digit run
        while (ia < len(a) and not a[ia].isdigit()) or (ib < len(b) and not b[ib].isdigit()):
            ca = a[ia] if ia < len(a) and not a[ia].isdigit() else ""
            cb = b[ib] if ib < len(b) and not b[ib].isdigit() else ""
            oa, ob = _dpkg_order(ca), _dpkg_order(cb)
            if oa != ob:
                return -1 if oa < ob else 1
            if ca:
                ia += 1
            if cb:
                ib += 1
        # digit run
        sa = ia
        while ia < len(a) and a[ia].isdigit():
            ia += 1
        sb = ib
        while ib < len(b) and b[ib].isdigit():
            ib += 1
        na = int(a[sa:ia] or 0)
        nb = int(b[sb:ib] or 0)
        if na != nb:
            return -1 if na < nb else 1
    return 0


def dpkg_compare(a: str, b: str) -> int:
    ea, ua, ra = _dpkg_split(a)
    eb, ub, rb = _dpkg_split(b)
    if ea != eb:
        return -1 if ea < eb else 1
    result = _dpkg_cmp_part(ua, ub)
    if result:
        return result
    return _dpkg_cmp_part(ra, rb)


def comparator_for(ecosystem: Optional[str]):
    """Version comparator for an OSV ecosystem name."""
    eco = (ecosystem or "").split(":", 1)[0].lower()
    if eco in ("debian", "ubuntu"):
        return dpkg_compare
    return compare_versions
