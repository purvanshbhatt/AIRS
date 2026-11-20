"""
Evidence collection: one piece of evidence per entity, one moment per finding.

Telemetry is stored as it arrives. A connector that reports its full state on
every sync (a Microsoft 365 snapshot, an AWS credential report) therefore
leaves many stored copies of the same user, device or alert inside the
24-hour window the readiness pipeline reads. Read naively, every copy is new
evidence: the same finding is listed once per sync, alert counts multiply and
the readiness score is charged for each copy.

This module is the single place the readiness endpoint and the report builder
turn stored events into evidence and moments. It guarantees:

  * an event stored more than once is read once;
  * an entity (evidence kind + connector + the source system's own id) is
    described by its newest observation only;
  * a moment (capability + the evidence it rests on) is reported once.

Nothing is invented and nothing is scored here. Identities come from the
source system; what was collapsed is counted and returned to the caller.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.services.clinic_engine.v2.engine import ClinicEvaluationEngine
from app.services.clinic_engine.v2.providers import ProviderRegistry
from app.services.clinic_engine.v2.schema import ClinicMoment, Evidence

logger = logging.getLogger("airs.clinic_engine.v2.evidence_collection")

EvidenceKey = Tuple[str, str, str, str]


def new_stats() -> Dict[str, int]:
    """Counters describing what a collection pass read and collapsed."""
    return {
        "events": 0,
        "duplicate_events_skipped": 0,
        "evidence_items": 0,
        "repeat_observations_collapsed": 0,
        "duplicate_checks_collapsed": 0,
    }


def _bump(stats: Optional[Dict[str, int]], key: str, amount: int = 1) -> None:
    if stats is not None:
        stats[key] = stats.get(key, 0) + amount


def evidence_key(evidence: Evidence) -> EvidenceKey:
    """Stable identity of the thing a piece of evidence describes.

    The source system's own id (user id, device id, alert id, finding ARN)
    scoped by evidence kind and connector. Evidence that carries no id cannot
    be told apart from its neighbours by identity, so it is only ever merged
    with a byte-identical copy of itself.
    """
    kind = getattr(evidence.kind, "value", str(evidence.kind))
    if evidence.source_id not in (None, ""):
        return (kind, evidence.source_connector, "id", str(evidence.source_id))
    return (kind, evidence.source_connector, "content", evidence.payload_hash)


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _newest_first(events: List[Any]) -> List[Any]:
    """Order events newest first.

    Events loaded from storage carry the time they were stored. When every
    event is timestamped that time decides; otherwise the caller's order is
    kept (the telemetry loader already returns newest first).
    """
    stamps = [_parse_timestamp(getattr(e, "timestamp", None)) for e in events]
    if not events or any(s is None for s in stamps):
        return list(events)
    order = sorted(range(len(events)), key=lambda i: stamps[i], reverse=True)  # stable
    return [events[i] for i in order]


def _unique_events(events: List[Any], stats: Optional[Dict[str, int]]) -> List[Any]:
    """Drop stored copies of the same source event (same system, same native id)."""
    seen = set()
    unique = []
    for event in events:
        native_id = getattr(event, "source_event_id", None)
        if native_id:
            key = (getattr(event, "source_system", None), getattr(event, "event_type", None), native_id)
            if key in seen:
                _bump(stats, "duplicate_events_skipped")
                continue
            seen.add(key)
        unique.append(event)
    return unique


def collect_evidence(events: List[Any], stats: Optional[Dict[str, int]] = None) -> List[Evidence]:
    """Extract evidence from ``events``, one item per entity, newest wins.

    Each provider is first shown every event at once, so its own rules apply
    (for example "only the newest credential report counts"). Each event is
    then read on its own, newest first, and an item is kept only when no
    newer event already described the same entity and the provider reported
    it in the full pass.
    """
    ordered = _unique_events(_newest_first(events), stats)
    _bump(stats, "events", len(ordered))
    providers = list(ProviderRegistry.list_all().values())

    reported = set()
    for provider in providers:
        for item in provider.extract(ordered):
            reported.add(evidence_key(item))

    evidence: List[Evidence] = []
    described = set()
    for event in ordered:
        from_this_event = set()
        observed_at = _parse_timestamp(getattr(event, "timestamp", None))
        for provider in providers:
            for item in provider.extract([event]):
                key = evidence_key(item)
                if key not in reported:
                    continue  # the provider's own rules excluded it
                if key in described:
                    _bump(stats, "repeat_observations_collapsed")
                    continue  # a newer event already describes this entity
                if key in from_this_event and key[2] == "content":
                    _bump(stats, "repeat_observations_collapsed")
                    continue  # byte-identical item listed twice in one event
                from_this_event.add(key)
                if observed_at is not None:
                    item.observed_at = observed_at
                evidence.append(item)
        described |= from_this_event

    _bump(stats, "evidence_items", len(evidence))
    return evidence


def dedupe_moments(moments: List[ClinicMoment], stats: Optional[Dict[str, int]] = None) -> List[ClinicMoment]:
    """One moment per id. The id is a hash of the capability and the evidence
    the verdict rests on, so equal ids are the same finding. Order is kept."""
    seen = set()
    unique: List[ClinicMoment] = []
    for moment in moments:
        if moment.id in seen:
            _bump(stats, "duplicate_checks_collapsed")
            continue
        seen.add(moment.id)
        unique.append(moment)
    return unique


def evaluate_events(
    events: List[Any],
    engine: Optional[ClinicEvaluationEngine] = None,
) -> Tuple[List[ClinicMoment], Dict[str, int]]:
    """Stored events -> de-duplicated evidence -> moments, plus what was collapsed.

    ``engine`` lets a caller supply its own evaluation engine; by default a
    ``ClinicEvaluationEngine`` is used.
    """
    stats = new_stats()
    evidence = collect_evidence(events, stats)
    moments = dedupe_moments((engine or ClinicEvaluationEngine()).evaluate(evidence), stats)
    collapsed = (
        stats["duplicate_events_skipped"]
        + stats["repeat_observations_collapsed"]
        + stats["duplicate_checks_collapsed"]
    )
    if collapsed:
        logger.info(
            "Evidence collection: %d events, %d evidence items, %d moments; collapsed %d repeat "
            "observation(s), %d duplicate event(s), %d duplicate check(s)",
            stats["events"], stats["evidence_items"], len(moments),
            stats["repeat_observations_collapsed"], stats["duplicate_events_skipped"],
            stats["duplicate_checks_collapsed"],
        )
    return moments, stats
