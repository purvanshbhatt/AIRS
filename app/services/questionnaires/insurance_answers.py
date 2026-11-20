"""
Insurance questionnaire answer pack: deterministic answers from live evidence.

For every question in ``insurance_bank.QUESTIONS`` this module produces one
answer with:

  value          yes | no | partial | not_verified | human_only
  basis          one plain-English sentence (or two) saying what the evidence shows
  evidence_*     which connected source the answer rests on, and when it was observed
  coverage       what was looked at, and what was not (and why)

Rules (the guard-rails the pack is built around):

  * No evidence for a question, a connector in error / waiting for sign-in /
    switched off, or evidence older than ``MAX_EVIDENCE_AGE`` gives
    ``not_verified``. The last good value is never shown as the answer.
  * Questions no connected system can answer are ``human_only``.
  * Security Hub only delivers *failed* control findings, so for checks that
    rely on those findings alone a missing failure is never read as a pass.
  * Nothing is scored, estimated or written by a language model. Every answer
    is a pure function of stored telemetry, connector state and the clock.
  * ResilAI never submits the application: the customer reviews, corrects
    and signs it ("You attest. ResilAI shows the evidence it has").

Signals reused from the readiness pipeline: the same persisted telemetry
(``TelemetryEvent``) and demo telemetry generator, the evidence providers
(``collect_evidence``), ``UnauthorizedAccessCapability`` for unused accounts,
the AWS sample-finding rule, and connector status from ``ConnectorManager``.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from app.services.questionnaires.insurance_bank import (
    HUMAN,
    QUESTION_BANK_ID,
    QUESTION_BANK_TITLE,
    QUESTION_BANK_VERSION,
    QUESTIONS,
    TELEMETRY,
    TOPIC_LABELS,
    TOPICS,
    Question,
)

logger = logging.getLogger("airs.questionnaires.insurance")

# ──────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────

YES = "yes"
NO = "no"
PARTIAL = "partial"
NOT_VERIFIED = "not_verified"
HUMAN_ONLY = "human_only"
ANSWER_VALUES: Tuple[str, ...] = (YES, NO, PARTIAL, NOT_VERIFIED, HUMAN_ONLY)
ANSWER_LABELS: Dict[str, str] = {
    YES: "Yes",
    NO: "No",
    PARTIAL: "Partly",
    NOT_VERIFIED: "Not verified: answer manually",
    HUMAN_ONLY: "You answer this",
}

# Evidence (and a connector's last sync) older than this is not used.
MAX_EVIDENCE_AGE = timedelta(hours=48)
# How far back stored telemetry is read, so stale evidence can be named.
LOOKBACK = timedelta(days=14)
MAX_EVENTS = 3000

STALE_ACCOUNT_DAYS = 30
KEY_ROTATION_DAYS = 90
BACKUP_MAX_AGE = timedelta(hours=24)

NOTICE_TEMPLATE = "You attest. ResilAI shows the evidence it has, as of {time}."
ATTESTATION_STATEMENT = (
    "I have reviewed every answer in this pack, corrected any that are wrong, and answered the questions "
    "marked \"You answer this\" or \"Not verified\" myself. ResilAI does not submit this application."
)

# Connector states that mean the data cannot be trusted right now.
FAILED_STATUSES = {"error", "pending_auth", "inactive"}

# State of one source for one question.
FRESH = "fresh"
STALE = "stale"
FAILED = "failed"
NO_DATA = "no_data"
NOT_CONNECTED = "not_connected"
BLOCKING_STATES = {STALE, FAILED}


@dataclass(frozen=True)
class SourceDef:
    key: str
    label: str
    connector_types: Tuple[str, ...]
    event_prefix: str


SOURCES: Dict[str, SourceDef] = {
    "microsoft": SourceDef("microsoft", "Microsoft 365", ("microsoft",), "microsoft."),
    "aws": SourceDef("aws", "Amazon Web Services", ("aws", "aws_security_hub"), "aws."),
    "veeam": SourceDef("veeam", "Veeam Backup", ("veeam",), "veeam."),
    "wazuh": SourceDef("wazuh", "Wazuh", ("wazuh",), "wazuh."),
    "duo": SourceDef("duo", "Duo", ("duo",), "duo."),
    "splunk": SourceDef("splunk", "Splunk", ("splunk",), "splunk."),
}

MS_TYPES = ("microsoft.telemetry",)
IAM_TYPES = ("aws.iam.credential_report", "aws.iam_users")
FINDING_TYPES = ("aws.securityhub.finding", "aws.guardduty.finding")
AWS_BACKUP_TYPES = ("aws.backup.job", "aws.backup_recovery_point")
INVENTORY_TYPES = ("aws.inventory.snapshot",)
NETWORK_TYPES = ("aws.network.snapshot",)


# ──────────────────────────────────────────────────────────────────────────
# Small helpers
# ──────────────────────────────────────────────────────────────────────────

def parse_time(value: Any) -> Optional[datetime]:
    """ISO string or datetime -> aware UTC datetime; None when unreadable."""
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip() and value.strip().upper() not in ("N/A", "NO_INFORMATION"):
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def format_time(value: Optional[datetime]) -> str:
    if value is None:
        return "an unknown time"
    return value.astimezone(timezone.utc).strftime("%d %b %Y, %H:%M UTC")


def describe_age(then: datetime, now: datetime) -> str:
    seconds = max(0, int((now - then).total_seconds()))
    hours = seconds // 3600
    if hours < 1:
        return "less than an hour ago"
    if hours < 48:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = hours // 24
    return f"{days} days ago"


def _plural(n: int, word: str, plural: Optional[str] = None) -> str:
    return f"{n} {word if n == 1 else (plural or word + 's')}"


def _names(items: Sequence[str], limit: int = 3) -> str:
    items = [str(i) for i in items if i]
    if not items:
        return ""
    shown = ", ".join(items[:limit])
    if len(items) > limit:
        shown += f" and {len(items) - limit} more"
    return shown


def _short(text: Optional[str], limit: int = 120) -> str:
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _all(n: int, singular: str, plural: str) -> str:
    """``the only device`` / ``all 3 devices``."""
    return f"the only {singular}" if n == 1 else f"all {n} {plural}"


def _any(n: int, singular: str, plural: str) -> str:
    """``the only device`` / ``any of the 3 devices``."""
    return f"the only {singular}" if n == 1 else f"any of the {n} {plural}"


def three_level(ok: int, total: int) -> str:
    """All -> yes, none -> no, some -> partial."""
    if total <= 0:
        raise ValueError("three_level needs at least one item")
    if ok == total:
        return YES
    if ok == 0:
        return NO
    return PARTIAL


_CONTROL_RE = re.compile(r"([A-Za-z][A-Za-z0-9]*\.\d+)$")


def control_id(generator_id: Any) -> Optional[str]:
    """``security-control/EC2.13`` or ``aws-foundational-.../v/1.0.0/EC2.13`` -> ``EC2.13``."""
    last = str(generator_id or "").rstrip("/").rsplit("/", 1)[-1]
    match = _CONTROL_RE.search(last)
    return match.group(1) if match else None


# ──────────────────────────────────────────────────────────────────────────
# Evidence snapshot and source reads
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class ConnectorState:
    connector_type: str
    name: str
    status: str
    last_sync_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class EvidenceSnapshot:
    """Everything an answer may rest on. Built once per pack."""
    org_id: str
    events: List[Any]                 # RawEvent-like: event_type, source_system, source_event_id, payload, timestamp
    connectors: List[ConnectorState]
    demo: bool
    now: datetime


@dataclass
class SourceRead:
    key: str
    label: str
    state: str
    reason: str
    as_of: Optional[datetime] = None
    events: List[Any] = field(default_factory=list)

    @property
    def fresh(self) -> bool:
        return self.state == FRESH

    def of_type(self, *types: str) -> List[Any]:
        return [e for e in self.events if e.event_type in types]


@dataclass
class Finding:
    """What one source says about one question. ``value`` None = inconclusive."""
    value: Optional[str]
    basis: str
    source: SourceRead
    scope: str = ""


def event_time(event: Any) -> Optional[datetime]:
    return parse_time(getattr(event, "timestamp", None))


def read_source(snapshot: EvidenceSnapshot, key: str, types: Optional[Sequence[str]] = None) -> SourceRead:
    """State of ``key`` for the event ``types`` a question needs.

    Real organisations: the connector must exist, must not be failing, must
    have synced within ``MAX_EVIDENCE_AGE``, and the newest event of the
    requested types must be within ``MAX_EVIDENCE_AGE``. Demo workspaces have
    no real connectors; their sample telemetry is generated on request, so
    only the event checks apply.
    """
    sdef = SOURCES[key]
    label = sdef.label
    now = snapshot.now
    max_hours = int(MAX_EVIDENCE_AGE.total_seconds() // 3600)
    from_source = [e for e in snapshot.events if str(getattr(e, "event_type", "")).startswith(sdef.event_prefix)]
    wanted = [e for e in from_source if types is None or e.event_type in types]

    if snapshot.demo:
        if not from_source:
            return SourceRead(key, label, NOT_CONNECTED, f"{label} is not connected in this sample workspace.")
    else:
        rows = [c for c in snapshot.connectors if c.connector_type in sdef.connector_types]
        if not rows:
            return SourceRead(key, label, NOT_CONNECTED, f"{label} is not connected.")
        bad = [c for c in rows if c.status in FAILED_STATUSES]
        if bad:
            c = bad[0]
            if c.status == "error":
                detail = f" ({_short(c.error_message)})" if c.error_message else ""
                reason = f"The {c.name} connection is failing{detail}, so its data was not used."
            elif c.status == "pending_auth":
                reason = f"The {c.name} connection is waiting for sign-in approval, so its data was not used."
            else:
                reason = f"The {c.name} connection is switched off, so its data was not used."
            return SourceRead(key, label, FAILED, reason)
        synced = [c.last_sync_at for c in rows if c.last_sync_at is not None]
        if not synced:
            return SourceRead(key, label, NO_DATA, f"{label} is connected but has not finished a sync yet.")
        last_sync = max(synced)
        if now - last_sync > MAX_EVIDENCE_AGE:
            return SourceRead(
                key, label, STALE,
                f"{label} last synced {describe_age(last_sync, now)} ({format_time(last_sync)}), "
                f"outside the {max_hours}-hour freshness limit.",
                as_of=last_sync,
            )

    timed = [(event_time(e), e) for e in wanted]
    timed = [(t, e) for t, e in timed if t is not None]
    if not timed:
        return SourceRead(key, label, NO_DATA, f"{label} is connected but sent no data that answers this question.")
    newest = max(t for t, _ in timed)
    if now - newest > MAX_EVIDENCE_AGE:
        return SourceRead(
            key, label, STALE,
            f"The newest {label} data for this question is from {format_time(newest)} "
            f"({describe_age(newest, now)}), outside the {max_hours}-hour freshness limit.",
            as_of=newest,
        )
    fresh = [e for t, e in sorted(timed, key=lambda pair: pair[0], reverse=True) if now - t <= MAX_EVIDENCE_AGE]
    return SourceRead(key, label, FRESH, "", as_of=newest, events=fresh)


class RuleContext:
    """Per-pack access to sources; remembers which sources each question read."""

    def __init__(self, snapshot: EvidenceSnapshot):
        self.snapshot = snapshot
        self.now = snapshot.now
        self._cache: Dict[Tuple[str, Optional[Tuple[str, ...]]], SourceRead] = {}
        self.reads: List[SourceRead] = []

    def begin(self) -> None:
        self.reads = []

    def read(self, key: str, types: Optional[Sequence[str]] = None) -> SourceRead:
        cache_key = (key, tuple(types) if types else None)
        if cache_key not in self._cache:
            self._cache[cache_key] = read_source(self.snapshot, key, types)
        result = self._cache[cache_key]
        self.reads.append(result)
        return result


# ──────────────────────────────────────────────────────────────────────────
# Payload accessors
# ──────────────────────────────────────────────────────────────────────────

def _newest(events: Iterable[Any]) -> Optional[Any]:
    events = list(events)
    # Source reads return events newest first.
    return events[0] if events else None


def _newest_per(events: Iterable[Any], key: Callable[[Any], Any]) -> List[Any]:
    seen = set()
    out = []
    for e in events:  # newest first
        k = key(e)
        if k in seen:
            continue
        seen.add(k)
        out.append(e)
    return out


def ms_payload(read: SourceRead) -> Optional[Dict[str, Any]]:
    event = _newest(read.of_type(*MS_TYPES))
    return (event.payload or {}) if event is not None else None


def iam_users(read: SourceRead) -> Optional[List[Dict[str, Any]]]:
    """Users from the newest credential report of each AWS account; None when no report."""
    reports = _newest_per(read.of_type(*IAM_TYPES), lambda e: str((e.payload or {}).get("account_id") or ""))
    if not reports:
        return None
    users: List[Dict[str, Any]] = []
    seen = set()
    for report in reports:
        for user in (report.payload or {}).get("iam_users") or []:
            uid = user.get("user_id") or user.get("user_name")
            if not uid or uid in seen:
                continue
            seen.add(uid)
            users.append(user)
    return users


def _is_root(user: Dict[str, Any]) -> bool:
    return str(user.get("user_name") or "").lower() == "<root_account>"


def _user_label(user: Dict[str, Any]) -> str:
    if _is_root(user):
        return "AWS root account"
    return str(user.get("display_name") or user.get("user_name") or user.get("user_principal_name") or user.get("user_id"))


def aws_findings(read: SourceRead) -> List[Dict[str, Any]]:
    """Active, real (not sample) AWS findings, one per finding id, newest copy."""
    from app.services.clinic_engine.v2.providers.aws_provider import is_sample_finding

    out = []
    for e in _newest_per(read.of_type(*FINDING_TYPES), lambda e: e.source_event_id):
        payload = e.payload or {}
        if str(payload.get("record_state") or "").upper() == "ARCHIVED":
            continue
        if is_sample_finding(payload):
            continue
        out.append(payload)
    return out


def failed_controls(read: SourceRead, ids: Iterable[str]) -> Dict[str, List[Dict[str, Any]]]:
    """Security Hub controls in ``ids`` with at least one FAILED finding."""
    wanted = set(ids)
    found: Dict[str, List[Dict[str, Any]]] = {}
    for payload in aws_findings(read):
        if str(payload.get("compliance_status") or "").upper() != "FAILED":
            continue
        cid = control_id(payload.get("generator_id"))
        if cid in wanted:
            found.setdefault(cid, []).append(payload)
    return found


def describe_failed(found: Dict[str, List[Dict[str, Any]]]) -> str:
    parts = []
    for cid in sorted(found):
        rows = found[cid]
        title = _short(rows[0].get("title") or cid, 110)
        parts.append(f"\"{title}\" ({cid}, {_plural(len(rows), 'resource')})")
    return "; ".join(parts)


FAILURES_ONLY_NOTE = (
    "AWS Security Hub raised no failed check for this, but ResilAI only receives failed checks, "
    "so a pass cannot be confirmed."
)


# ──────────────────────────────────────────────────────────────────────────
# Rules: one function per telemetry question
# ──────────────────────────────────────────────────────────────────────────

Rule = Callable[[RuleContext], List[Finding]]


def rule_email_mfa(ctx: RuleContext) -> List[Finding]:
    r = ctx.read("microsoft", MS_TYPES)
    if not r.fresh:
        return []
    payload = ms_payload(r) or {}
    users = [u for u in payload.get("entra_users") or [] if u.get("account_enabled", True) is not False]
    scope = f"Microsoft 365: {_plural(len(users), 'switched-on user account')}"
    if not users:
        return [Finding(None, "Microsoft 365 reported no switched-on user accounts.", r, scope)]
    known = [u for u in users if isinstance(u.get("mfa_enforced"), bool)]
    without = [u for u in known if not u["mfa_enforced"]]
    unknown = len(users) - len(known)
    names = _names([_user_label(u) for u in without])
    if without:
        value = three_level(len(known) - len(without), len(users))
        if value == NO:
            basis = (f"Microsoft 365 reports that multi-factor sign-in is not enforced for "
                     f"{_any(len(users), 'switched-on account', 'switched-on accounts')}.")
        else:
            basis = (f"Microsoft 365 reports multi-factor sign-in enforced for {len(known) - len(without)} of "
                     f"{len(users)} switched-on accounts; not for {names}.")
        return [Finding(value, basis, r, scope)]
    if unknown:
        return [Finding(None, f"{len(known)} of {len(users)} Microsoft 365 accounts have multi-factor sign-in "
                              f"enforced; the other {unknown} did not report a setting.", r, scope)]
    return [Finding(YES, f"Microsoft 365 reports multi-factor sign-in enforced for "
                         f"{_all(len(users), 'switched-on account', 'switched-on accounts')}.",
                    r, scope)]


def rule_admin_mfa(ctx: RuleContext) -> List[Finding]:
    r = ctx.read("aws", IAM_TYPES + FINDING_TYPES)
    if not r.fresh:
        return []
    users = iam_users(r)
    if users:
        privileged = [
            u for u in users
            if _is_root(u) or u.get("password_enabled") is True
            or (u.get("password_enabled") is None and u.get("account_enabled", True) is not False)
        ]
        scope = (f"AWS: root account and {_plural(len([u for u in privileged if not _is_root(u)]), 'IAM user')} "
                 f"who can sign in to the console")
        if privileged:
            without = [u for u in privileged if u.get("mfa_enforced") is not True]
            if not without:
                return [Finding(YES, f"In AWS, the root account and every IAM user who can sign in to the console "
                                     f"({len(privileged)} in total) have multi-factor sign-in turned on.", r, scope)]
            value = three_level(len(privileged) - len(without), len(privileged))
            return [Finding(value, f"In AWS, {_plural(len(without), 'account')} that can sign in to the console "
                                   f"{'has' if len(without) == 1 else 'have'} no multi-factor sign-in: "
                                   f"{_names([_user_label(u) for u in without])}.", r, scope)]
    found = failed_controls(r, ("IAM.5", "IAM.9", "IAM.19"))
    if found:
        return [Finding(NO, f"AWS Security Hub reports: {describe_failed(found)}.", r, "AWS Security Hub checks")]
    return [Finding(None, "AWS sent no IAM credential report, so administrator sign-in settings could not be read.",
                    r, "AWS")]


NO_SECOND_FACTOR_REASONS = {"allow_unenrolled_user", "bypass_user", "allowed_by_policy", "trusted_network"}
NO_SECOND_FACTOR_FACTORS = {"not_available", "none", "bypass"}


def rule_remote_access_mfa(ctx: RuleContext) -> List[Finding]:
    r = ctx.read("duo", ("duo.auth_log",))
    if not r.fresh:
        return []
    logs = [e.payload or {} for e in _newest_per(r.events, lambda e: e.source_event_id)]
    success = [p for p in logs if str(p.get("result") or "").upper() == "SUCCESS"]
    scope = f"Duo: {_plural(len(success), 'successful sign-in')} in the last {int(MAX_EVIDENCE_AGE.total_seconds() // 3600)} hours"
    if not success:
        return [Finding(None, "Duo recorded no successful sign-ins in the freshness window.", r, scope)]
    without = [
        p for p in success
        if str(p.get("reason") or "").lower() in NO_SECOND_FACTOR_REASONS
        or str(p.get("factor") or "").lower() in NO_SECOND_FACTOR_FACTORS
    ]
    if not without:
        return [Finding(YES, f"All {len(success)} successful sign-ins Duo recorded used a second factor.", r, scope)]
    value = three_level(len(success) - len(without), len(success))
    users = _names(sorted({str(p.get("user") or "unknown") for p in without}))
    return [Finding(value, f"{len(without)} of {len(success)} successful Duo sign-ins went through without a second "
                           f"factor (users: {users}).", r, scope)]


def rule_dormant_accounts(ctx: RuleContext) -> List[Finding]:
    from app.services.clinic_engine.v2.capabilities.unauthorized_access import UnauthorizedAccessCapability
    from app.services.clinic_engine.v2.evidence_collection import collect_evidence
    from app.services.clinic_engine.v2.schema import EvidenceKind, Verdict

    findings: List[Finding] = []
    for key, types in (("microsoft", MS_TYPES), ("aws", IAM_TYPES)):
        r = ctx.read(key, types)
        if not r.fresh:
            continue
        if key == "aws":
            # Only the newest credential report per account describes today's users.
            events = _newest_per(r.of_type(*types), lambda e: str((e.payload or {}).get("account_id") or ""))
        else:
            events = [_newest(r.of_type(*types))]
        evidence = [e for e in collect_evidence([e for e in events if e is not None])
                    if e.kind == EvidenceKind.USER_ACCOUNT_STATUS]
        enabled = [e for e in evidence if e.payload.get("account_enabled")]
        scope = f"{r.label}: {_plural(len(enabled), 'switched-on account')}"
        if not enabled:
            findings.append(Finding(None, f"{r.label} reported no switched-on accounts.", r, scope))
            continue
        results = UnauthorizedAccessCapability.evaluate(evidence)
        unused = [x for x in results if x.verdict == Verdict.CRITICAL]
        unclear = [x for x in results if x.verdict == Verdict.CONCERN]
        if unused:
            names = _names([str(x.details.get("display_name")) for x in unused])
            findings.append(Finding(NO, f"{r.label} has {_plural(len(unused), 'switched-on account')} with no sign-in "
                                        f"for more than {STALE_ACCOUNT_DAYS} days: {names}.", r, scope))
        elif unclear:
            findings.append(Finding(None, f"{r.label}: {_plural(len(unclear), 'account')} {'has' if len(unclear) == 1 else 'have'} "
                                          f"no sign-in or creation date on record, so unused accounts cannot be ruled out.",
                                    r, scope))
        else:
            findings.append(Finding(YES, f"In {r.label}, {_all(len(enabled), 'switched-on account', 'switched-on accounts')} "
                                         f"signed in within the last {STALE_ACCOUNT_DAYS} days.", r, scope))
    return findings


def rule_access_keys(ctx: RuleContext) -> List[Finding]:
    r = ctx.read("aws", IAM_TYPES)
    if not r.fresh:
        return []
    users = iam_users(r)
    if users is None:
        return [Finding(None, "AWS sent no IAM credential report.", r, "AWS")]
    active = [u for u in users if u.get("access_key_active") or u.get("access_key_1_active") or u.get("access_key_2_active")]
    scope = f"AWS: {_plural(len(users), 'IAM identity', 'IAM identities')}, {_plural(len(active), 'active access key')}"
    if not active:
        return [Finding(YES, "No AWS IAM user has an active long-lived access key.", r, scope)]
    old, unknown = [], []
    for u in active:
        rotated = parse_time(u.get("access_key_1_last_rotated") or u.get("access_key_last_rotated"))
        if rotated is None:
            unknown.append(u)
        elif ctx.now - rotated > timedelta(days=KEY_ROTATION_DAYS):
            old.append(u)
    if old:
        value = three_level(len(active) - len(old) - len(unknown), len(active)) if not unknown else (
            NO if len(old) == len(active) else PARTIAL)
        return [Finding(value, f"{_plural(len(old), 'active AWS access key')} {'was' if len(old) == 1 else 'were'} last "
                               f"replaced more than {KEY_ROTATION_DAYS} days ago: "
                               f"{_names([_user_label(u) for u in old])}.", r, scope)]
    if unknown:
        return [Finding(None, f"AWS did not report when {_plural(len(unknown), 'active access key')} "
                              f"{'was' if len(unknown) == 1 else 'were'} last replaced.", r, scope)]
    return [Finding(YES, f"In AWS, {_all(len(active), 'active access key was', 'active access keys were')} replaced "
                         f"within the last {KEY_ROTATION_DAYS} days.",
                    r, scope)]


def _backup_jobs(read: SourceRead, types: Sequence[str]) -> List[Dict[str, Any]]:
    events = _newest_per(
        read.of_type(*types),
        lambda e: str((e.payload or {}).get("job_id") or (e.payload or {}).get("system_name") or e.source_event_id),
    )
    return [e.payload or {} for e in events]


def rule_backup_daily(ctx: RuleContext) -> List[Finding]:
    findings: List[Finding] = []
    for key, types in (("veeam", ("veeam.backup_job",)), ("aws", AWS_BACKUP_TYPES)):
        r = ctx.read(key, types)
        if not r.fresh:
            continue
        jobs = _backup_jobs(r, types)
        scope = f"{r.label}: {_plural(len(jobs), 'backup job')}"
        if not jobs:
            continue
        last_ok = [(j, parse_time(j.get("last_successful_backup"))) for j in jobs]
        on_time = [j for j, t in last_ok if t is not None and ctx.now - t <= BACKUP_MAX_AGE]
        late = [(j, t) for j, t in last_ok if not (t is not None and ctx.now - t <= BACKUP_MAX_AGE)]
        newest_ok = max((t for _, t in last_ok if t is not None), default=None)
        newest_text = (f" The most recent successful backup finished {format_time(newest_ok)} "
                       f"({describe_age(newest_ok, ctx.now)})." if newest_ok else " No successful backup is on record.")
        value = three_level(len(on_time), len(jobs))
        if value == YES:
            basis = (f"In {r.label}, {_all(len(jobs), 'backup job', 'backup jobs')} completed successfully in the last "
                     f"24 hours.{newest_text}")
        elif value == NO:
            basis = (f"In {r.label}, {_any(len(jobs), 'backup job', 'backup jobs')} has not completed successfully "
                     f"in the last 24 hours.{newest_text}") if len(jobs) == 1 else (
                f"None of the {len(jobs)} backup jobs in {r.label} has completed successfully in the last 24 hours.{newest_text}")
        else:
            names = _names([str(j.get("system_name") or j.get("job_id") or "backup job") for j, _ in late])
            basis = (f"{len(on_time)} of {len(jobs)} backup jobs in {r.label} completed in the last 24 hours; "
                     f"overdue: {names}.{newest_text}")
        findings.append(Finding(value, basis, r, scope))
    return findings


BACKUP_OK = {"success", "succeeded", "ok", "completed"}
BACKUP_FAILED = {"failed", "error", "failure"}
BACKUP_WARNING = {"warning", "partial"}


def rule_backup_last_run(ctx: RuleContext) -> List[Finding]:
    r = ctx.read("veeam", ("veeam.backup_job",))
    if not r.fresh:
        return []
    jobs = _backup_jobs(r, ("veeam.backup_job",))
    scope = f"Veeam Backup: {_plural(len(jobs), 'backup job')}"
    if not jobs:
        return []
    statuses = [str(j.get("status") or "").lower() for j in jobs]
    ok = sum(1 for s in statuses if s in BACKUP_OK)
    failed = [j for j, s in zip(jobs, statuses) if s in BACKUP_FAILED]
    warned = [j for j, s in zip(jobs, statuses) if s in BACKUP_WARNING]
    unknown = len(jobs) - ok - len(failed) - len(warned)
    if failed or warned:
        bad = failed + warned
        value = NO if ok == 0 and not unknown and not warned else PARTIAL
        return [Finding(value, f"The most recent run of {_plural(len(bad), 'backup job')} did not finish cleanly: "
                               f"{_names([str(j.get('system_name') or j.get('job_id')) for j in bad])}.", r, scope)]
    if unknown:
        return [Finding(None, f"Veeam did not report the result of the most recent run for "
                              f"{_plural(unknown, 'backup job')}.", r, scope)]
    return [Finding(YES, f"The most recent run of {_all(len(jobs), 'Veeam backup job', 'Veeam backup jobs')} "
                         f"finished successfully.", r, scope)]


def rule_endpoint_protection(ctx: RuleContext) -> List[Finding]:
    r = ctx.read("wazuh", ("wazuh.agent_status",))
    if not r.fresh:
        return []
    agents = [e.payload or {} for e in _newest_per(r.events, lambda e: str((e.payload or {}).get("agent_id")))]
    agents = [a for a in agents if str(a.get("agent_id")) != "000"]  # 000 is the Wazuh manager itself
    scope = f"Wazuh: {_plural(len(agents), 'computer or server', 'computers and servers')} with the agent"
    if not agents:
        return [Finding(None, "Wazuh reported no agents.", r, scope)]
    active = [a for a in agents if str(a.get("status") or "").lower() == "active"]
    value = three_level(len(active), len(agents))
    if value == YES:
        basis = (f"Wazuh reports that {_all(len(agents), 'computer or server', 'computers and servers')} with its agent "
                 f"{'is' if len(agents) == 1 else 'are'} running and reporting.")
    else:
        quiet = _names([str(a.get("name") or a.get("agent_id")) for a in agents if a not in active])
        basis = f"{len(active)} of {len(agents)} computers and servers with the Wazuh agent are reporting; not reporting: {quiet}."
    return [Finding(value, basis, r, scope)]


def _intune_devices(read: SourceRead) -> List[Dict[str, Any]]:
    payload = ms_payload(read) or {}
    return [d for d in payload.get("intune_devices") or [] if isinstance(d, dict)]


def rule_devices_managed(ctx: RuleContext) -> List[Finding]:
    r = ctx.read("microsoft", MS_TYPES)
    if not r.fresh:
        return []
    devices = _intune_devices(r)
    scope = f"Microsoft Intune: {_plural(len(devices), 'enrolled device')}"
    if not devices:
        return [Finding(None, "Microsoft Intune reported no enrolled devices.", r, scope)]
    known = [d for d in devices if d.get("compliance_state")]
    if not known:
        return [Finding(None, "Microsoft Intune did not report a compliance state for any device.", r, scope)]
    compliant = [d for d in known if str(d.get("compliance_state")).lower() == "compliant"]
    value = three_level(len(compliant), len(devices))
    if value == YES:
        basis = (f"Microsoft Intune reports {_all(len(devices), 'enrolled device', 'enrolled devices')} as meeting "
                 f"the security baseline (compliant).")
    elif value == NO:
        bad = _names([str(d.get("device_name") or d.get("device_id")) for d in devices])
        basis = (f"Microsoft Intune reports that {_any(len(devices), 'enrolled device', 'enrolled devices')} "
                 f"({bad}) does not meet the security baseline." if len(devices) == 1 else
                 f"Microsoft Intune reports that none of the {len(devices)} enrolled devices meets the security baseline.")
    else:
        bad = _names([str(d.get("device_name") or d.get("device_id")) for d in devices if d not in compliant])
        basis = (f"{len(compliant)} of {len(devices)} devices enrolled in Microsoft Intune meet the security baseline; "
                 f"not compliant or not reported: {bad}.")
    return [Finding(value, basis, r, scope)]


def rule_critical_vulns(ctx: RuleContext) -> List[Finding]:
    findings: List[Finding] = []
    r = ctx.read("wazuh", ("wazuh.vulnerability",))
    if r.fresh:
        vulns = [e.payload or {} for e in _newest_per(
            r.events, lambda e: (str((e.payload or {}).get("agent_id")), str((e.payload or {}).get("cve"))))]
        hosts = {str(v.get("agent_id")) for v in vulns}
        scope = f"Wazuh vulnerability scan: {_plural(len(vulns), 'result')} on {_plural(len(hosts), 'computer')}"
        open_critical = [
            v for v in vulns
            if str(v.get("severity") or "").lower() == "critical"
            and str(v.get("status") or "").lower() not in ("fixed", "solved", "resolved")
        ]
        if open_critical:
            cves = _names(sorted({str(v.get("cve")) for v in open_critical}))
            on = len({str(v.get("agent_id")) for v in open_critical})
            findings.append(Finding(NO, f"Wazuh reports {_plural(len(open_critical), 'open critical vulnerability', 'open critical vulnerabilities')} "
                                        f"on {_plural(on, 'computer')} ({cves}).", r, scope))
        else:
            findings.append(Finding(YES, f"Wazuh's latest scan results ({_plural(len(vulns), 'finding')} on "
                                         f"{_plural(len(hosts), 'computer')}) include no open critical vulnerability.", r, scope))

    a = ctx.read("aws", FINDING_TYPES)
    if a.fresh:
        inspector = [p for p in aws_findings(a) if "inspector" in str(p.get("product_name") or "").lower()]
        critical = [p for p in inspector if str(p.get("severity") or p.get("severity_label") or "").lower() == "critical"]
        off = failed_controls(a, ("Inspector.1",))
        if critical:
            findings.append(Finding(NO, f"Amazon Inspector reports {_plural(len(critical), 'critical vulnerability', 'critical vulnerabilities')} "
                                        f"on AWS resources.", a, "Amazon Inspector findings"))
        elif off:
            findings.append(Finding(None, "Amazon Inspector scanning of AWS servers is turned off, so AWS cannot "
                                          "report server vulnerabilities.", a, "AWS Security Hub checks"))
        elif inspector:
            findings.append(Finding(YES, f"Amazon Inspector reports {_plural(len(inspector), 'finding')} on AWS resources, "
                                         f"none of them critical.", a, "Amazon Inspector findings"))
        else:
            findings.append(Finding(None, "AWS sent no vulnerability scan results.", a, "AWS"))
    return findings


def rule_device_encryption(ctx: RuleContext) -> List[Finding]:
    r = ctx.read("microsoft", MS_TYPES)
    if not r.fresh:
        return []
    devices = _intune_devices(r)
    scope = f"Microsoft Intune: {_plural(len(devices), 'enrolled device')}"
    if not devices:
        return [Finding(None, "Microsoft Intune reported no enrolled devices.", r, scope)]

    def encrypted(d: Dict[str, Any]) -> Optional[bool]:
        if isinstance(d.get("is_encrypted"), bool):
            return d["is_encrypted"]
        status = str(d.get("bitlocker_status") or "").lower()
        if status == "encrypted":
            return True
        if status in ("not_encrypted", "notencrypted", "off", "disabled"):
            return False
        return None

    states = [(d, encrypted(d)) for d in devices]
    unknown = [d for d, s in states if s is None]
    plain = [d for d, s in states if s is False]
    on = [d for d, s in states if s is True]
    if plain:
        value = NO if not on else PARTIAL
        return [Finding(value, f"Microsoft Intune reports {_plural(len(plain), 'device')} without disk encryption: "
                               f"{_names([str(d.get('device_name') or d.get('device_id')) for d in plain])}.", r, scope)]
    if unknown:
        return [Finding(None, f"Microsoft Intune did not report disk encryption for {_plural(len(unknown), 'device')}.",
                        r, scope)]
    return [Finding(YES, f"Microsoft Intune reports encrypted disks on {_all(len(devices), 'enrolled device', 'enrolled devices')}.",
                    r, scope)]


ENCRYPTION_CONTROLS = ("EC2.3", "EC2.7", "RDS.3", "RDS.4", "EFS.1")


def rule_cloud_encryption(ctx: RuleContext) -> List[Finding]:
    r = ctx.read("aws", FINDING_TYPES + INVENTORY_TYPES)
    if not r.fresh:
        return []
    found = failed_controls(r, ENCRYPTION_CONTROLS)
    inventory = _newest(r.of_type(*INVENTORY_TYPES))
    flags: List[Tuple[str, bool]] = []
    for res in ((inventory.payload or {}).get("resources") or []) if inventory is not None else []:
        if not isinstance(res, dict):
            continue
        name = str(res.get("name") or res.get("instance_id") or res.get("identifier") or "resource")
        for flag in ("ebs_encrypted", "storage_encrypted"):
            if isinstance(res.get(flag), bool):
                flags.append((name, res[flag]))
    if found:
        return [Finding(NO, f"AWS Security Hub reports: {describe_failed(found)}.", r, "AWS Security Hub encryption checks")]
    if flags:
        ok = [n for n, f in flags if f]
        value = three_level(len(ok), len(flags))
        if value == YES:
            basis = (f"AWS reports encryption at rest on "
                     f"{_all(len(flags), 'storage volume or database', 'storage volumes and databases')} it listed.")
        else:
            basis = (f"AWS reports encryption at rest on {len(ok)} of {len(flags)} storage volumes and databases; "
                     f"not encrypted: {_names([n for n, f in flags if not f])}.")
        return [Finding(value, basis, r, f"AWS inventory: {_plural(len(flags), 'volume or database', 'volumes and databases')}")]
    return [Finding(None, FAILURES_ONLY_NOTE, r, "AWS Security Hub encryption checks")]


REMOTE_PORTS = {22: "SSH", 3389: "Remote Desktop (RDP)"}
REMOTE_PORT_CONTROLS = ("EC2.13", "EC2.14", "EC2.19", "EC2.21")


def port_open(entry: str, port: int) -> bool:
    """Does an ``open_ports`` entry (``tcp/22``, ``tcp/0-1024``, ``tcp/all``, ``all``) include ``port``?"""
    text = str(entry or "").lower().strip()
    if text in ("all", "-1"):
        return True
    protocol, _, ports = text.partition("/")
    if protocol not in ("tcp", "6", ""):
        return False
    if ports == "all":
        return True
    if not ports:
        return False
    low, _, high = ports.partition("-")
    try:
        lo = int(low)
        hi = int(high) if high else lo
    except ValueError:
        return False
    return lo <= port <= hi


def rule_remote_ports(ctx: RuleContext) -> List[Finding]:
    findings: List[Finding] = []
    n = ctx.read("aws", NETWORK_TYPES)
    if n.fresh:
        snap = _newest(n.of_type(*NETWORK_TYPES))
        groups = [g for g in ((snap.payload or {}).get("security_groups") or []) if isinstance(g, dict)]
        exposed = []
        for g in groups:
            ports = [REMOTE_PORTS[p] for p in REMOTE_PORTS if any(port_open(e, p) for e in g.get("open_ports") or [])]
            if ports:
                exposed.append((g, ports))
        scope = f"AWS network: {_plural(len(groups), 'security group')}"
        if exposed:
            desc = _names([f"{g.get('name') or g.get('id')} ({' and '.join(p)})" for g, p in exposed])
            findings.append(Finding(NO, f"{_plural(len(exposed), 'AWS security group')} let anyone on the internet "
                                        f"reach a remote-administration port: {desc}.", n, scope))
        elif groups:
            which = "The only AWS security group does" if len(groups) == 1 else f"None of the {len(groups)} AWS security groups"
            verb = " not let" if len(groups) == 1 else " lets"
            findings.append(Finding(YES, f"{which}{verb} the whole internet reach port 22 (SSH) or 3389 (RDP).",
                                    n, scope))
    f = ctx.read("aws", FINDING_TYPES)
    if f.fresh:
        found = failed_controls(f, REMOTE_PORT_CONTROLS)
        if found:
            findings.append(Finding(NO, f"AWS Security Hub reports: {describe_failed(found)}.", f, "AWS Security Hub network checks"))
        elif not any(x.value for x in findings):
            findings.append(Finding(None, FAILURES_ONLY_NOTE, f, "AWS Security Hub network checks"))
    return findings


PUBLIC_STORAGE_CONTROLS = ("S3.1", "S3.2", "S3.3", "S3.8", "S3.19", "EC2.1", "EC2.182", "RDS.1", "RDS.2")


def rule_public_storage(ctx: RuleContext) -> List[Finding]:
    r = ctx.read("aws", FINDING_TYPES)
    if not r.fresh:
        return []
    found = failed_controls(r, PUBLIC_STORAGE_CONTROLS)
    if found:
        return [Finding(NO, f"AWS Security Hub reports: {describe_failed(found)}.", r, "AWS Security Hub public-access checks")]
    return [Finding(None, FAILURES_ONLY_NOTE, r, "AWS Security Hub public-access checks")]


def rule_security_monitoring(ctx: RuleContext) -> List[Finding]:
    findings: List[Finding] = []
    w = ctx.read("wazuh", ("wazuh.agent_status", "wazuh.alert"))
    if w.fresh:
        agents = [e.payload or {} for e in _newest_per(w.of_type("wazuh.agent_status"),
                                                       lambda e: str((e.payload or {}).get("agent_id")))]
        agents = [a for a in agents if str(a.get("agent_id")) != "000"]
        alerts = w.of_type("wazuh.alert")
        active = [a for a in agents if str(a.get("status") or "").lower() == "active"]
        scope = f"Wazuh: {_plural(len(agents), 'agent')}, {_plural(len(alerts), 'alert')}"
        if active:
            findings.append(Finding(YES, f"Wazuh is running and reporting on {_plural(len(active), 'computer or server', 'computers and servers')}.",
                                    w, scope))
        elif agents:
            findings.append(Finding(NO, f"None of the {len(agents)} Wazuh agents is reporting.", w, scope))
        elif alerts:
            findings.append(Finding(YES, f"Wazuh sent {_plural(len(alerts), 'security alert')} in the freshness window.", w, scope))
    s = ctx.read("splunk")
    if s.fresh:
        findings.append(Finding(YES, f"Splunk sent {_plural(len(s.events), 'security record')} in the freshness window.",
                                s, f"Splunk: {_plural(len(s.events), 'record')}"))
    m = ctx.read("microsoft", MS_TYPES)
    if m.fresh:
        alerts = (ms_payload(m) or {}).get("defender_alerts")
        if alerts:
            findings.append(Finding(YES, f"Microsoft Defender is raising alerts ({_plural(len(alerts), 'alert')} in the latest sync).",
                                    m, "Microsoft Defender alert feed"))
        else:
            findings.append(Finding(None, "Microsoft Defender reported no alerts, which does not show whether Defender "
                                          "is switched on.", m, "Microsoft Defender alert feed"))
    return findings


AUDIT_LOG_CORE = ("CloudTrail.1", "CloudTrail.3")
AUDIT_LOG_SECONDARY = ("EC2.6", "Config.1", "S3.9", "ELB.5", "CloudTrail.5")


def rule_cloud_audit_logging(ctx: RuleContext) -> List[Finding]:
    r = ctx.read("aws", FINDING_TYPES)
    if not r.fresh:
        return []
    core = failed_controls(r, AUDIT_LOG_CORE)
    if core:
        return [Finding(NO, f"AWS Security Hub reports: {describe_failed(core)}.", r, "AWS Security Hub logging checks")]
    secondary = failed_controls(r, AUDIT_LOG_SECONDARY)
    if secondary:
        return [Finding(PARTIAL, f"AWS Security Hub reports: {describe_failed(secondary)}. Whether the main audit trail "
                                 f"(CloudTrail) is on was not confirmed.", r, "AWS Security Hub logging checks")]
    return [Finding(None, FAILURES_ONLY_NOTE, r, "AWS Security Hub logging checks")]


def rule_cloud_threat_detection(ctx: RuleContext) -> List[Finding]:
    r = ctx.read("aws", FINDING_TYPES)
    if not r.fresh:
        return []
    off = failed_controls(r, ("GuardDuty.1",))
    if off:
        return [Finding(NO, f"AWS Security Hub reports: {describe_failed(off)}.", r, "AWS Security Hub checks")]
    guardduty = [p for p in aws_findings(r) if "guardduty" in str(p.get("product_name") or "").lower()]
    if guardduty:
        return [Finding(YES, f"Amazon GuardDuty is on: it raised {_plural(len(guardduty), 'finding')} in the freshness window.",
                        r, f"Amazon GuardDuty: {_plural(len(guardduty), 'finding')}")]
    return [Finding(None, "AWS sent no GuardDuty findings (test findings are not counted), so ResilAI cannot confirm "
                          "GuardDuty is watching.", r, "Amazon GuardDuty")]


RULES: Dict[str, Rule] = {
    "EMAIL_MFA": rule_email_mfa,
    "ADMIN_MFA": rule_admin_mfa,
    "REMOTE_ACCESS_MFA": rule_remote_access_mfa,
    "DORMANT_ACCOUNTS": rule_dormant_accounts,
    "ACCESS_KEYS_ROTATED": rule_access_keys,
    "BACKUP_DAILY": rule_backup_daily,
    "BACKUP_LAST_RUN": rule_backup_last_run,
    "ENDPOINT_PROTECTION": rule_endpoint_protection,
    "DEVICES_MANAGED": rule_devices_managed,
    "CRITICAL_VULNS_PATCHED": rule_critical_vulns,
    "DEVICE_ENCRYPTION": rule_device_encryption,
    "CLOUD_ENCRYPTION": rule_cloud_encryption,
    "REMOTE_PORTS_CLOSED": rule_remote_ports,
    "PUBLIC_STORAGE_BLOCKED": rule_public_storage,
    "SECURITY_MONITORING": rule_security_monitoring,
    "CLOUD_AUDIT_LOGGING": rule_cloud_audit_logging,
    "CLOUD_THREAT_DETECTION": rule_cloud_threat_detection,
}

# Questions where one source showing the control is enough ("is there any
# monitoring?"). Everywhere else every source must agree ("does ALL email
# use MFA?").
ANY_SOURCE_QUESTIONS = {"SECURITY_MONITORING"}


def _check_rules() -> None:
    telemetry = {q.id for q in QUESTIONS if q.mode == TELEMETRY}
    missing = telemetry - set(RULES)
    extra = set(RULES) - telemetry
    if missing or extra:
        raise RuntimeError(f"Insurance question rules out of step with the bank: missing={sorted(missing)} extra={sorted(extra)}")


_check_rules()


# ──────────────────────────────────────────────────────────────────────────
# Answer assembly
# ──────────────────────────────────────────────────────────────────────────

def combine(values: Sequence[str], any_source: bool = False) -> str:
    if any_source:
        if YES in values:
            return YES
        return PARTIAL if PARTIAL in values else NO
    if all(v == YES for v in values):
        return YES
    if all(v == NO for v in values):
        return NO
    return PARTIAL


def _base_answer(q: Question) -> Dict[str, Any]:
    return {
        "id": q.id,
        "topic": q.topic,
        "topic_label": TOPIC_LABELS[q.topic],
        "question": q.text,
        "help": q.help or None,
        "mode": q.mode,
    }


def human_answer(q: Question) -> Dict[str, Any]:
    answer = _base_answer(q)
    answer.update({
        "value": HUMAN_ONLY,
        "value_label": ANSWER_LABELS[HUMAN_ONLY],
        "basis": f"{q.human_reason} You answer this question yourself.",
        "evidence_source": None,
        "evidence_time": None,
        "evidence": [],
        "coverage": {"checked": [], "not_checked": ["No connected system can answer this question."]},
    })
    return answer


def answer_question(q: Question, ctx: RuleContext) -> Dict[str, Any]:
    if q.mode == HUMAN:
        return human_answer(q)

    ctx.begin()
    findings = RULES[q.id](ctx)
    # Make sure every source the bank names for the question was looked at,
    # even when the rule bailed out early.
    for key in q.sources:
        if not any(r.key == key for r in ctx.reads):
            ctx.read(key)

    # One state per source: the worst one wins (a failed read blocks).
    order = {FAILED: 0, STALE: 1, NO_DATA: 2, NOT_CONNECTED: 3, FRESH: 4}
    by_source: Dict[str, SourceRead] = {}
    for read in ctx.reads:
        current = by_source.get(read.key)
        if current is None or order[read.state] < order[current.state]:
            by_source[read.key] = read
    blocked = [r for r in by_source.values() if r.state in BLOCKING_STATES]
    unavailable = [r for r in by_source.values() if r.state in (NO_DATA, NOT_CONNECTED)]
    concluded = [f for f in findings if f.value]

    checked = [f.scope for f in findings if f.scope]
    not_checked = [r.reason for r in blocked + unavailable]
    not_checked += list(q.blind_spots)

    answer = _base_answer(q)
    if blocked:
        value = NOT_VERIFIED
        basis = " ".join(r.reason for r in blocked) + " Answer this question yourself."
    elif not concluded:
        value = NOT_VERIFIED
        reasons = [f.basis for f in findings] + [r.reason for r in unavailable]
        basis = " ".join(dict.fromkeys(reasons)) or "No connected system sent evidence for this question."
        basis += " Answer this question yourself."
    else:
        value = combine([f.value for f in concluded], any_source=q.id in ANY_SOURCE_QUESTIONS)
        basis = " ".join(dict.fromkeys(f.basis for f in concluded))

    evidence: List[Dict[str, Any]] = []
    if value not in (NOT_VERIFIED, HUMAN_ONLY):
        seen = set()
        for f in concluded:
            if f.source.key in seen:
                continue
            seen.add(f.source.key)
            evidence.append({
                "source": f.source.key,
                "source_label": f.source.label,
                "observed_at": f.source.as_of.isoformat() if f.source.as_of else None,
            })
    times = [parse_time(e["observed_at"]) for e in evidence if e["observed_at"]]
    oldest = min(times) if times else None

    answer.update({
        "value": value,
        "value_label": ANSWER_LABELS[value],
        "basis": basis,
        "evidence_source": ", ".join(e["source_label"] for e in evidence) or None,
        # The oldest observation the answer rests on: the answer is true as of this time.
        "evidence_time": oldest.isoformat() if oldest else None,
        "evidence": evidence,
        "coverage": {"checked": checked, "not_checked": not_checked},
    })
    return answer


def sources_overview(snapshot: EvidenceSnapshot) -> List[Dict[str, Any]]:
    """One line per known source: is it usable right now, and if not, why."""
    out = []
    for key, sdef in SOURCES.items():
        read = read_source(snapshot, key)
        if read.state == NOT_CONNECTED:
            continue
        out.append({
            "source": key,
            "label": sdef.label,
            "state": read.state,
            "reason": read.reason or None,
            "as_of": read.as_of.isoformat() if read.as_of else None,
        })
    return out


def build_pack(snapshot: EvidenceSnapshot, organization: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The full answer pack for ``snapshot``. Pure: no database, no clock beyond ``snapshot.now``."""
    ctx = RuleContext(snapshot)
    answers = [answer_question(q, ctx) for q in QUESTIONS]
    counts = {v: 0 for v in ANSWER_VALUES}
    for a in answers:
        counts[a["value"]] += 1
    generated_at = snapshot.now.isoformat()
    org = dict(organization or {"id": snapshot.org_id, "name": snapshot.org_id})
    org["is_demo"] = snapshot.demo
    max_hours = int(MAX_EVIDENCE_AGE.total_seconds() // 3600)
    return {
        "questionnaire": {
            "id": QUESTION_BANK_ID,
            "title": QUESTION_BANK_TITLE,
            "version": QUESTION_BANK_VERSION,
        },
        "organization": org,
        "is_demo": snapshot.demo,
        "data_label": "Sample data" if snapshot.demo else "Live data",
        "generated_at": generated_at,
        "evidence_max_age_hours": max_hours,
        "notice": NOTICE_TEMPLATE.format(time=format_time(snapshot.now)),
        "attestation": {
            "statement": ATTESTATION_STATEMENT,
            "submitted_by_resilai": False,
        },
        "summary": {
            "total": len(answers),
            "counts": counts,
            "from_evidence": counts[YES] + counts[NO] + counts[PARTIAL],
            "generated_at": generated_at,
            "question_bank_version": QUESTION_BANK_VERSION,
        },
        "topics": [{"id": tid, "label": label} for tid, label in TOPICS],
        "sources": sources_overview(snapshot),
        "answers": answers,
    }


# ──────────────────────────────────────────────────────────────────────────
# Loading (database + demo)
# ──────────────────────────────────────────────────────────────────────────

def _enum(value: Any) -> str:
    return str(getattr(value, "value", value) or "")


def load_connector_states(db: Any, org_id: str) -> List[ConnectorState]:
    from app.services.connector_manager import ConnectorManager

    out = []
    for c in ConnectorManager(db, org_id).list_connectors():
        out.append(ConnectorState(
            connector_type=_enum(c.connector_type),
            name=c.display_name or _enum(c.connector_type),
            status=_enum(c.status),
            last_sync_at=parse_time(getattr(c, "last_sync_at", None)),
            error_message=getattr(c, "error_message", None),
        ))
    return out


def load_persisted_events(db: Any, org_id: str, now: datetime) -> List[Any]:
    """Stored telemetry from the last ``LOOKBACK`` (newest first), as RawEvents.

    Reads further back than the readiness endpoint (24 hours) so stale
    evidence can be named as stale instead of looking absent.
    """
    from sqlalchemy import or_

    from app.models.telemetry_event import TelemetryEvent
    from app.services.clinic_engine.v2.schema import RawEvent

    cutoff = now - LOOKBACK
    prefixes = [s.event_prefix for s in SOURCES.values()]
    rows = (
        db.query(TelemetryEvent)
        .filter(
            TelemetryEvent.org_id == org_id,
            TelemetryEvent.seen_at_column() >= cutoff.replace(tzinfo=None),
            or_(*[TelemetryEvent.event_type.like(f"{p}%") for p in prefixes]),
        )
        .order_by(TelemetryEvent.seen_at_column().desc())
        .limit(MAX_EVENTS)
        .all()
    )
    events = []
    for row in rows:
        payload = row.payload
        if isinstance(payload, str):
            import json
            try:
                payload = json.loads(payload)
            except ValueError:
                continue
        # The time the source last reported it, so evidence a connector still
        # reports on every sync is not called stale.
        stored = parse_time(row.seen_at)
        events.append(RawEvent(
            event_type=row.event_type,
            source_system=row.source_system,
            source_event_id=row.source_event_id,
            organization_id=org_id,
            payload=payload or {},
            timestamp=stored.isoformat() if stored else None,
        ))
    return events


def load_demo_events(org_id: str, now: datetime) -> List[Any]:
    """The same sample telemetry the demo readiness view uses. Events the
    generator leaves unstamped were generated now, so they are stamped now."""
    from app.api.clinic.router import get_demo_telemetry

    events = get_demo_telemetry(org_id)
    for e in events:
        if not getattr(e, "timestamp", None):
            e.timestamp = now.isoformat()
    return events


def build_insurance_pack(db: Any, org_id: str, demo: Optional[bool] = None, org: Any = None,
                         now: Optional[datetime] = None) -> Dict[str, Any]:
    """Load evidence for ``org_id`` and build its answer pack."""
    from app.reports.readiness_source import is_demo_org

    now = now or datetime.now(timezone.utc)
    if demo is None:
        demo = is_demo_org(db, org_id)
    if demo:
        events = load_demo_events(org_id, now)
        connectors: List[ConnectorState] = []
    else:
        try:
            events = load_persisted_events(db, org_id, now)
        except Exception as exc:
            logger.warning("Telemetry load failed for %s: %s", org_id, exc)
            events = []
        try:
            connectors = load_connector_states(db, org_id)
        except Exception as exc:
            logger.warning("Connector load failed for %s: %s", org_id, exc)
            connectors = []

    if org is not None:
        organization = {"id": org.id, "name": getattr(org, "clinic_name", None) or org.name}
    else:
        label = org_id.replace("demo-", "").replace("-", " ").title() if demo else org_id
        organization = {"id": org_id, "name": f"{label} (Demo)" if demo else org_id}
    snapshot = EvidenceSnapshot(org_id=org_id, events=events, connectors=connectors, demo=demo, now=now)
    return build_pack(snapshot, organization)
