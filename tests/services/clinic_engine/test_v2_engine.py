"""
Comprehensive tests for V2 Clinic Engine.

Tests the full pipeline: Evidence → Capability Evaluation → Moments → Morning Check.
Every capability, every provider, every edge case.
"""
import pytest
from datetime import datetime, timezone, timedelta

from app.services.clinic_engine.v2.schema import (
    Evidence, EvidenceKind, Verdict, EvaluationResult, ClinicMoment, RawEvent
)
from app.services.clinic_engine.v2.capability import CapabilityRegistry
from app.services.clinic_engine.v2.engine import ClinicEvaluationEngine
from app.services.clinic_engine.v2.morning_check import MorningCheckGeneratorV2
from app.services.clinic_engine.v2.providers import (
    MicrosoftProvider, WazuhProvider, ProviderRegistry,
)
from app.services.clinic_engine.v2.capabilities.unauthorized_access import UnauthorizedAccessCapability
from app.services.clinic_engine.v2.capabilities.recovery_readiness import RecoveryReadinessCapability
from app.services.clinic_engine.v2.capabilities.device_compromise import DeviceCompromiseCapability


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


# ============================================================================
# PROVIDER TESTS
# ============================================================================

class TestMicrosoftProvider:
    """Tests for Microsoft evidence provider — pure data transformation."""

    def test_extracts_users_from_telemetry(self):
        event = RawEvent(
            event_type="microsoft.telemetry",
            source_system="microsoft",
            source_event_id="sync-123",
            organization_id="org-123",
            payload={
                "entra_users": [
                    {"user_id": "u1", "user_principal_name": "sarah@clinic.com", "mfa_enforced": True, "conditional_access_status": "enforced"},
                    {"user_id": "u2", "user_principal_name": "admin@clinic.com", "mfa_enforced": False, "conditional_access_status": "unknown"},
                ],
                "intune_devices": [],
                "defender_alerts": [],
            },
        )
        evidence = MicrosoftProvider.extract([event])
        users = [e for e in evidence if e.kind == EvidenceKind.USER_ACCOUNT_STATUS]
        assert len(users) == 2
        assert users[0].source_connector == "microsoft"
        assert users[0].source_id == "u1"
        assert users[0].payload["display_name"] == "sarah@clinic.com"
        assert users[0].payload["account_enabled"] is True

    def test_extracts_devices_from_telemetry(self):
        event = RawEvent(
            event_type="microsoft.telemetry",
            source_system="microsoft",
            source_event_id="sync-123",
            organization_id="org-123",
            payload={
                "entra_users": [],
                "intune_devices": [
                    {"device_id": "d1", "device_name": "FRONT-DESK", "compliance_state": "noncompliant", "bitlocker_status": "encrypted", "os_version": "10.0.19045"},
                ],
                "defender_alerts": [],
            },
        )
        evidence = MicrosoftProvider.extract([event])
        devices = [e for e in evidence if e.kind == EvidenceKind.DEVICE_SECURITY_STATUS]
        assert len(devices) == 1
        assert devices[0].payload["device_name"] == "FRONT-DESK"
        assert devices[0].payload["compliance_state"] == "noncompliant"
        assert devices[0].payload["is_encrypted"] is True

    def test_extracts_alerts_from_telemetry(self):
        event = RawEvent(
            event_type="microsoft.telemetry",
            source_system="microsoft",
            source_event_id="sync-123",
            organization_id="org-123",
            payload={
                "entra_users": [],
                "intune_devices": [],
                "defender_alerts": [
                    {"alert_id": "a1", "title": "Suspicious login", "severity": "high", "status": "active", "device_id": "d1"},
                ],
            },
        )
        evidence = MicrosoftProvider.extract([event])
        alerts = [e for e in evidence if e.kind == EvidenceKind.SECURITY_ALERT]
        assert len(alerts) == 1
        assert alerts[0].payload["severity"] == "high"

    def test_ignores_non_microsoft_events(self):
        event = RawEvent(
            event_type="wazuh.agent_status",
            source_system="wazuh",
            source_event_id="agent-1",
            organization_id="org-123",
            payload={"agent_id": "001"},
        )
        evidence = MicrosoftProvider.extract([event])
        assert len(evidence) == 0

    def test_handles_empty_payload(self):
        event = RawEvent(
            event_type="microsoft.telemetry",
            source_system="microsoft",
            source_event_id="sync-123",
            organization_id="org-123",
            payload={},
        )
        evidence = MicrosoftProvider.extract([event])
        assert len(evidence) == 0


class TestWazuhProvider:
    """Tests for Wazuh evidence provider — pure data transformation."""

    def test_extracts_device_status_from_agent(self):
        event = RawEvent(
            event_type="wazuh.agent_status",
            source_system="wazuh",
            source_event_id="agent-status-001",
            organization_id="org-123",
            payload={"agent_id": "001", "name": "billing-pc", "status": "active", "ip": "192.168.1.10", "os": "Windows 10", "version": "4.7.0"},
        )
        evidence = WazuhProvider.extract([event])
        assert len(evidence) == 1
        assert evidence[0].kind == EvidenceKind.DEVICE_SECURITY_STATUS
        assert evidence[0].payload["device_name"] == "billing-pc"

    def test_extracts_vulnerability_from_scan(self):
        event = RawEvent(
            event_type="wazuh.vulnerability",
            source_system="wazuh",
            source_event_id="vuln-001-CVE-2024-1234",
            organization_id="org-123",
            payload={"agent_id": "001", "cve": "CVE-2024-1234", "name": "Critical RCE", "severity": "critical", "version": "1.0"},
        )
        evidence = WazuhProvider.extract([event])
        assert len(evidence) == 1
        assert evidence[0].kind == EvidenceKind.VULNERABILITY_SCAN
        assert evidence[0].payload["cve"] == "CVE-2024-1234"

    def test_extracts_alert(self):
        event = RawEvent(
            event_type="wazuh.alert",
            source_system="wazuh",
            source_event_id="alert-99",
            organization_id="org-123",
            payload={"alert_id": "99", "title": "Brute force detected", "severity": "high", "rule_id": "5712", "agent_id": "001"},
        )
        evidence = WazuhProvider.extract([event])
        assert len(evidence) == 1
        assert evidence[0].kind == EvidenceKind.SECURITY_ALERT

    def test_handles_empty_list(self):
        evidence = WazuhProvider.extract([])
        assert len(evidence) == 0


class TestProviderRegistry:
    """Tests for the provider registry."""

    def test_microsoft_registered(self):
        provider = ProviderRegistry.get_provider("microsoft")
        assert provider is MicrosoftProvider

    def test_wazuh_registered(self):
        provider = ProviderRegistry.get_provider("wazuh")
        assert provider is WazuhProvider

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="No provider registered"):
            ProviderRegistry.get_provider("crowdstrike")


# ============================================================================
# CAPABILITY TESTS — Q1: Unauthorized Access
# ============================================================================

class TestUnauthorizedAccess:
    """Deterministic evaluation: Does someone who shouldn't have access still have access?"""

    def test_stale_user_30_days_critical(self):
        """User last signed in 45 days ago → CRITICAL."""
        evidence = [Evidence(
            kind=EvidenceKind.USER_ACCOUNT_STATUS,
            source_connector="microsoft",
            source_id="u1",
            organization_id="org-123",
            payload={
                "user_id": "u1",
                "display_name": "Sarah Johnson",
                "account_enabled": True,
                "last_sign_in": _iso(_now() - timedelta(days=45)),
            },
        )]
        results = UnauthorizedAccessCapability.evaluate(evidence)
        assert len(results) == 1
        assert results[0].verdict == Verdict.CRITICAL
        assert results[0].details["days_inactive"] == 45
        assert results[0].details["display_name"] == "Sarah Johnson"

    def test_active_user_safe(self):
        """User signed in yesterday → SAFE (no result)."""
        evidence = [Evidence(
            kind=EvidenceKind.USER_ACCOUNT_STATUS,
            source_connector="microsoft",
            source_id="u1",
            organization_id="org-123",
            payload={
                "user_id": "u1",
                "display_name": "Dr. Smith",
                "account_enabled": True,
                "last_sign_in": _iso(_now() - timedelta(hours=18)),
            },
        )]
        results = UnauthorizedAccessCapability.evaluate(evidence)
        assert len(results) == 0

    def test_disabled_account_safe(self):
        """Disabled account → SAFE regardless of last login."""
        evidence = [Evidence(
            kind=EvidenceKind.USER_ACCOUNT_STATUS,
            source_connector="microsoft",
            source_id="u1",
            organization_id="org-123",
            payload={
                "user_id": "u1",
                "display_name": "Former Employee",
                "account_enabled": False,
                "last_sign_in": _iso(_now() - timedelta(days=200)),
            },
        )]
        results = UnauthorizedAccessCapability.evaluate(evidence)
        assert len(results) == 0

    def test_null_last_sign_in_old_account_critical(self):
        """No last login, created 120 days ago → CRITICAL."""
        evidence = [Evidence(
            kind=EvidenceKind.USER_ACCOUNT_STATUS,
            source_connector="microsoft",
            source_id="u1",
            organization_id="org-123",
            payload={
                "user_id": "u1",
                "display_name": "Ghost Account",
                "account_enabled": True,
                "last_sign_in": None,
                "created_at": _iso(_now() - timedelta(days=120)),
            },
        )]
        results = UnauthorizedAccessCapability.evaluate(evidence)
        assert len(results) == 1
        assert results[0].verdict == Verdict.CRITICAL

    def test_null_last_sign_in_new_account_safe(self):
        """No last login, created 5 days ago → SAFE (new account)."""
        evidence = [Evidence(
            kind=EvidenceKind.USER_ACCOUNT_STATUS,
            source_connector="microsoft",
            source_id="u1",
            organization_id="org-123",
            payload={
                "user_id": "u1",
                "display_name": "New Hire",
                "account_enabled": True,
                "last_sign_in": None,
                "created_at": _iso(_now() - timedelta(days=5)),
            },
        )]
        results = UnauthorizedAccessCapability.evaluate(evidence)
        assert len(results) == 0

    def test_null_everything_concern(self):
        """No last login, no created_at → CONCERN."""
        evidence = [Evidence(
            kind=EvidenceKind.USER_ACCOUNT_STATUS,
            source_connector="microsoft",
            source_id="u1",
            organization_id="org-123",
            payload={
                "user_id": "u1",
                "display_name": "Mystery Account",
                "account_enabled": True,
                "last_sign_in": None,
            },
        )]
        results = UnauthorizedAccessCapability.evaluate(evidence)
        assert len(results) == 1
        assert results[0].verdict == Verdict.CONCERN

    def test_empty_evidence_safe(self):
        """No evidence → no results."""
        results = UnauthorizedAccessCapability.evaluate([])
        assert len(results) == 0

    def test_translation_plain_english(self):
        """Translation output is plain English, no jargon."""
        result = EvaluationResult(
            verdict=Verdict.CRITICAL,
            evidence_used=["u1"],
            details={
                "display_name": "Sarah Johnson",
                "user_id": "u1",
                "last_sign_in": "2026-06-01",
                "days_inactive": 60,
            },
        )
        translation = UnauthorizedAccessCapability.translate(result)
        assert "Sarah Johnson" in translation.what_happened
        assert "60 days" in translation.what_happened
        assert "HIPAA" in translation.ignore_impact
        # Must not contain jargon
        for term in ["evidence", "telemetry", "finding", "control", "NIST", "CIS"]:
            assert term not in translation.what_happened.lower()
            assert term not in translation.why_care.lower()

    def test_actions_include_suspend(self):
        result = EvaluationResult(
            verdict=Verdict.CRITICAL,
            evidence_used=["u1"],
            details={"user_id": "u1", "display_name": "Sarah"},
        )
        actions = UnauthorizedAccessCapability.get_actions(result)
        assert len(actions) == 1
        assert actions[0].action_id == "disable_account"
        assert actions[0].can_automate is True
        assert actions[0].automation_params["user_id"] == "u1"


# ============================================================================
# CAPABILITY TESTS — Q2: Recovery Readiness
# ============================================================================

class TestRecoveryReadiness:
    """Deterministic evaluation: Can I recover my clinic today if systems fail?"""

    def test_backup_failed_26_hours_critical(self):
        """Last backup 26 hours ago → CRITICAL."""
        evidence = [Evidence(
            kind=EvidenceKind.BACKUP_STATUS,
            source_connector="veeam",
            source_id="b1",
            organization_id="org-123",
            payload={
                "system_name": "Patient Database",
                "last_successful_backup": _iso(_now() - timedelta(hours=26)),
                "backup_type": "full",
            },
        )]
        results = RecoveryReadinessCapability.evaluate(evidence)
        assert len(results) == 1
        assert results[0].verdict == Verdict.CRITICAL
        assert results[0].details["system_name"] == "Patient Database"

    def test_backup_ok_4_hours_safe(self):
        """Last backup 4 hours ago → SAFE."""
        evidence = [Evidence(
            kind=EvidenceKind.BACKUP_STATUS,
            source_connector="veeam",
            source_id="b1",
            organization_id="org-123",
            payload={
                "system_name": "Patient Database",
                "last_successful_backup": _iso(_now() - timedelta(hours=4)),
                "backup_type": "full",
            },
        )]
        results = RecoveryReadinessCapability.evaluate(evidence)
        assert len(results) == 0

    def test_incremental_16_hours_concern(self):
        """Incremental backup 16 hours ago → CONCERN."""
        evidence = [Evidence(
            kind=EvidenceKind.BACKUP_STATUS,
            source_connector="datto",
            source_id="b1",
            organization_id="org-123",
            payload={
                "system_name": "Email Server",
                "last_successful_backup": _iso(_now() - timedelta(hours=16)),
                "backup_type": "incremental",
            },
        )]
        results = RecoveryReadinessCapability.evaluate(evidence)
        assert len(results) == 1
        assert results[0].verdict == Verdict.CONCERN

    def test_no_backup_ever_critical(self):
        """No backup ever recorded → CRITICAL."""
        evidence = [Evidence(
            kind=EvidenceKind.BACKUP_STATUS,
            source_connector="veeam",
            source_id="b1",
            organization_id="org-123",
            payload={
                "system_name": "File Server",
                "last_successful_backup": None,
            },
        )]
        results = RecoveryReadinessCapability.evaluate(evidence)
        assert len(results) == 1
        assert results[0].verdict == Verdict.CRITICAL

    def test_empty_evidence_safe(self):
        results = RecoveryReadinessCapability.evaluate([])
        assert len(results) == 0

    def test_translation_plain_english(self):
        result = EvaluationResult(
            verdict=Verdict.CRITICAL,
            evidence_used=["b1"],
            details={
                "system_name": "Patient Database",
                "last_backup_date": "2026-07-29T08:00:00+00:00",
                "hours_since_backup": 52,
            },
        )
        translation = RecoveryReadinessCapability.translate(result)
        assert "Patient Database" in translation.what_happened
        assert "52 hours" in translation.what_happened
        assert "gone forever" in translation.why_care


# ============================================================================
# CAPABILITY TESTS — Q3: Device Compromise
# ============================================================================

class TestDeviceCompromise:
    """Deterministic evaluation: Is one of my devices likely to be compromised?"""

    def test_active_high_alert_critical(self):
        """Device with active high-severity alert → CRITICAL."""
        evidence = [
            Evidence(
                kind=EvidenceKind.SECURITY_ALERT,
                source_connector="microsoft",
                source_id="a1",
                organization_id="org-123",
                payload={
                    "alert_id": "a1",
                    "title": "Ransomware detected",
                    "severity": "high",
                    "status": "active",
                    "device_id": "d1",
                },
            ),
            Evidence(
                kind=EvidenceKind.DEVICE_SECURITY_STATUS,
                source_connector="microsoft",
                source_id="d1",
                organization_id="org-123",
                payload={
                    "device_id": "d1",
                    "device_name": "FRONT-DESK",
                    "compliance_state": "compliant",
                },
            ),
        ]
        results = DeviceCompromiseCapability.evaluate(evidence)
        assert len(results) == 1
        assert results[0].verdict == Verdict.CRITICAL
        assert results[0].details["device_name"] == "FRONT-DESK"

    def test_critical_vulnerability_critical(self):
        """Device with unpatched critical CVE → CRITICAL."""
        evidence = [Evidence(
            kind=EvidenceKind.VULNERABILITY_SCAN,
            source_connector="wazuh",
            source_id="v1",
            organization_id="org-123",
            payload={
                "device_id": "d1",
                "device_name": "billing-pc",
                "cve": "CVE-2024-9999",
                "severity": "critical",
                "patched": False,
            },
        )]
        results = DeviceCompromiseCapability.evaluate(evidence)
        assert len(results) == 1
        assert results[0].verdict == Verdict.CRITICAL

    def test_noncompliant_device_concern(self):
        """Non-compliant device → CONCERN."""
        evidence = [Evidence(
            kind=EvidenceKind.DEVICE_SECURITY_STATUS,
            source_connector="microsoft",
            source_id="d1",
            organization_id="org-123",
            payload={
                "device_id": "d1",
                "device_name": "LAB-PC",
                "compliance_state": "noncompliant",
            },
        )]
        results = DeviceCompromiseCapability.evaluate(evidence)
        assert len(results) == 1
        assert results[0].verdict == Verdict.CONCERN

    def test_compliant_no_alerts_safe(self):
        """Compliant device, no alerts → SAFE (no results)."""
        evidence = [Evidence(
            kind=EvidenceKind.DEVICE_SECURITY_STATUS,
            source_connector="microsoft",
            source_id="d1",
            organization_id="org-123",
            payload={
                "device_id": "d1",
                "device_name": "DR-SMITH-PC",
                "compliance_state": "compliant",
            },
        )]
        results = DeviceCompromiseCapability.evaluate(evidence)
        assert len(results) == 0

    def test_mixed_evidence_aggregation(self):
        """Multiple evidence types for same device → aggregated correctly."""
        evidence = [
            Evidence(
                kind=EvidenceKind.DEVICE_SECURITY_STATUS,
                source_connector="microsoft",
                source_id="d1",
                organization_id="org-123",
                payload={"device_id": "d1", "device_name": "FRONT-DESK", "compliance_state": "noncompliant"},
            ),
            Evidence(
                kind=EvidenceKind.SECURITY_ALERT,
                source_connector="wazuh",
                source_id="a1",
                organization_id="org-123",
                payload={"alert_id": "a1", "severity": "critical", "status": "active", "device_id": "d1"},
            ),
            Evidence(
                kind=EvidenceKind.VULNERABILITY_SCAN,
                source_connector="wazuh",
                source_id="v1",
                organization_id="org-123",
                payload={"device_id": "d1", "cve": "CVE-2024-0001", "severity": "high", "patched": False},
            ),
        ]
        results = DeviceCompromiseCapability.evaluate(evidence)
        assert len(results) == 1  # One result per device
        assert results[0].verdict == Verdict.CRITICAL
        assert results[0].details["alert_count"] == 1
        assert results[0].details["vulnerability_count"] == 1

    def test_empty_evidence_safe(self):
        results = DeviceCompromiseCapability.evaluate([])
        assert len(results) == 0

    def test_translation_for_alerts(self):
        result = EvaluationResult(
            verdict=Verdict.CRITICAL,
            evidence_used=["a1"],
            details={
                "device_name": "FRONT-DESK",
                "alert_count": 2,
                "vulnerability_count": 0,
                "issues": ["active_alert"],
            },
        )
        t = DeviceCompromiseCapability.translate(result)
        assert "FRONT-DESK" in t.what_happened
        assert "2 active security warnings" in t.what_happened


# ============================================================================
# ENGINE INTEGRATION TESTS
# ============================================================================

class TestClinicEvaluationEngine:
    """Full pipeline: evidence → engine → moments."""

    def test_stale_user_produces_moment(self):
        engine = ClinicEvaluationEngine()
        evidence = [Evidence(
            kind=EvidenceKind.USER_ACCOUNT_STATUS,
            source_connector="microsoft",
            source_id="u1",
            organization_id="org-123",
            payload={
                "user_id": "u1",
                "display_name": "Sarah Johnson",
                "account_enabled": True,
                "last_sign_in": _iso(_now() - timedelta(days=60)),
            },
        )]
        moments = engine.evaluate(evidence)
        assert len(moments) == 1
        assert moments[0].question_id == "Q1"
        assert moments[0].capability_id == "unauthorized_access"
        assert moments[0].verdict == Verdict.CRITICAL
        assert "Sarah Johnson" in moments[0].translation.what_happened

    def test_no_evidence_empty(self):
        engine = ClinicEvaluationEngine()
        moments = engine.evaluate([])
        assert len(moments) == 0

    def test_all_safe_empty(self):
        """All evidence safe → no moments."""
        engine = ClinicEvaluationEngine()
        evidence = [
            Evidence(
                kind=EvidenceKind.USER_ACCOUNT_STATUS,
                source_connector="microsoft",
                source_id="u1",
                organization_id="org-123",
                payload={"user_id": "u1", "display_name": "Dr. Smith", "account_enabled": True, "last_sign_in": _iso(_now() - timedelta(hours=2))},
            ),
            Evidence(
                kind=EvidenceKind.BACKUP_STATUS,
                source_connector="veeam",
                source_id="b1",
                organization_id="org-123",
                payload={"system_name": "DB", "last_successful_backup": _iso(_now() - timedelta(hours=3))},
            ),
            Evidence(
                kind=EvidenceKind.DEVICE_SECURITY_STATUS,
                source_connector="microsoft",
                source_id="d1",
                organization_id="org-123",
                payload={"device_id": "d1", "device_name": "PC", "compliance_state": "compliant"},
            ),
        ]
        moments = engine.evaluate(evidence)
        assert len(moments) == 0

    def test_mixed_evidence_multiple_moments(self):
        """Multiple issues → multiple moments, sorted by severity."""
        engine = ClinicEvaluationEngine()
        evidence = [
            # Q1: Stale user (CRITICAL)
            Evidence(
                kind=EvidenceKind.USER_ACCOUNT_STATUS,
                source_connector="microsoft",
                source_id="u1",
                organization_id="org-123",
                payload={"user_id": "u1", "display_name": "Sarah", "account_enabled": True, "last_sign_in": _iso(_now() - timedelta(days=45))},
            ),
            # Q2: Backup failed (CRITICAL)
            Evidence(
                kind=EvidenceKind.BACKUP_STATUS,
                source_connector="veeam",
                source_id="b1",
                organization_id="org-123",
                payload={"system_name": "Patient DB", "last_successful_backup": _iso(_now() - timedelta(hours=30))},
            ),
            # Q3: Non-compliant device (CONCERN)
            Evidence(
                kind=EvidenceKind.DEVICE_SECURITY_STATUS,
                source_connector="microsoft",
                source_id="d1",
                organization_id="org-123",
                payload={"device_id": "d1", "device_name": "LAB-PC", "compliance_state": "noncompliant"},
            ),
        ]
        moments = engine.evaluate(evidence)
        assert len(moments) == 3
        # Critical moments first
        critical = [m for m in moments if m.severity == "high"]
        medium = [m for m in moments if m.severity == "medium"]
        assert len(critical) == 2
        assert len(medium) == 1

    def test_full_pipeline_microsoft_provider_to_engine(self):
        """End-to-end: NormalizedEvent → MicrosoftProvider → Engine → Moments."""
        event = RawEvent(
            event_type="microsoft.telemetry",
            source_system="microsoft",
            source_event_id="sync-456",
            organization_id="org-123",
            payload={
                "entra_users": [
                    {"user_id": "u-stale", "user_principal_name": "former.employee@clinic.com", "mfa_enforced": False, "conditional_access_status": "unknown"},
                ],
                "intune_devices": [
                    {"device_id": "d-bad", "device_name": "RECEPTION-PC", "compliance_state": "noncompliant", "bitlocker_status": "not_encrypted", "os_version": "10.0.18362"},
                ],
                "defender_alerts": [
                    {"alert_id": "a-crit", "title": "Suspicious PowerShell", "severity": "high", "status": "active", "device_id": "d-bad"},
                ],
            },
        )
        # Provider extracts evidence
        evidence = MicrosoftProvider.extract([event])
        assert len(evidence) == 3

        # Engine evaluates
        engine = ClinicEvaluationEngine()
        moments = engine.evaluate(evidence)

        # We expect: Q1 (user with no last_sign_in → CONCERN), Q3 (alert + noncompliant → CRITICAL)
        assert len(moments) >= 2
        q_ids = {m.question_id for m in moments}
        assert "Q1" in q_ids  # Stale user
        assert "Q3" in q_ids  # Compromised device


# ============================================================================
# MORNING CHECK TESTS
# ============================================================================

class TestMorningCheckV2:
    """Tests for the Morning Safety Check generator."""

    def test_all_clear(self):
        gen = MorningCheckGeneratorV2()
        check = gen.generate([])
        assert check.status == "ALL_CLEAR"
        assert "ready for patients" in check.headline
        assert len(check.questions_answered) == 3
        assert all(q.status == "safe" for q in check.questions_answered)

    def test_needs_attention_critical(self):
        gen = MorningCheckGeneratorV2()
        moment = ClinicMoment(
            id="test-1",
            question_id="Q1",
            capability_id="unauthorized_access",
            verdict=Verdict.CRITICAL,
            confidence=1.0,
            translation={"what_happened": "test", "why_care": "test", "ignore_impact": "test"},
            severity="high",
        )
        check = gen.generate([moment])
        assert check.status == "NEEDS_ATTENTION"
        assert "1 urgent issue" in check.headline
        q1 = next(q for q in check.questions_answered if q.question_id == "Q1")
        assert q1.status == "critical"
        assert q1.moment_count == 1

    def test_multiple_critical(self):
        gen = MorningCheckGeneratorV2()
        moments = [
            ClinicMoment(
                id="m1", question_id="Q1", capability_id="unauthorized_access",
                verdict=Verdict.CRITICAL, confidence=1.0,
                translation={"what_happened": "x", "why_care": "x", "ignore_impact": "x"},
                severity="high",
            ),
            ClinicMoment(
                id="m2", question_id="Q2", capability_id="recovery_readiness",
                verdict=Verdict.CRITICAL, confidence=1.0,
                translation={"what_happened": "y", "why_care": "y", "ignore_impact": "y"},
                severity="high",
            ),
        ]
        check = gen.generate(moments)
        assert check.status == "NEEDS_ATTENTION"
        assert "2 urgent issues" in check.headline

    def test_concern_only(self):
        gen = MorningCheckGeneratorV2()
        moment = ClinicMoment(
            id="m1", question_id="Q3", capability_id="device_compromise",
            verdict=Verdict.CONCERN, confidence=1.0,
            translation={"what_happened": "x", "why_care": "x", "ignore_impact": "x"},
            severity="medium",
        )
        check = gen.generate([moment])
        assert check.status == "NEEDS_ATTENTION"
        assert "nothing blocking your day" in check.headline


# ============================================================================
# CONNECTOR CERTIFICATION MATRIX TEST
# ============================================================================

class TestCertificationMatrix:
    """Verify the certification matrix — which providers produce which evidence."""

    def test_microsoft_provides_correct_evidence(self):
        assert EvidenceKind.USER_ACCOUNT_STATUS in MicrosoftProvider.provides()
        assert EvidenceKind.DEVICE_SECURITY_STATUS in MicrosoftProvider.provides()
        assert EvidenceKind.SECURITY_ALERT in MicrosoftProvider.provides()
        assert EvidenceKind.BACKUP_STATUS not in MicrosoftProvider.provides()

    def test_wazuh_provides_correct_evidence(self):
        assert EvidenceKind.DEVICE_SECURITY_STATUS in WazuhProvider.provides()
        assert EvidenceKind.VULNERABILITY_SCAN in WazuhProvider.provides()
        assert EvidenceKind.SECURITY_ALERT in WazuhProvider.provides()
        assert EvidenceKind.USER_ACCOUNT_STATUS not in WazuhProvider.provides()

    def test_providers_for_q1_unauthorized_access(self):
        """Q1 needs USER_ACCOUNT_STATUS → Microsoft provides it, Wazuh does not."""
        providers = ProviderRegistry.get_providers_for_evidence(EvidenceKind.USER_ACCOUNT_STATUS)
        types = [p.connector_type() for p in providers]
        assert "microsoft" in types
        assert "wazuh" not in types

    def test_providers_for_q3_device_compromise(self):
        """Q3 needs DEVICE_SECURITY_STATUS → both Microsoft and Wazuh provide it."""
        providers = ProviderRegistry.get_providers_for_evidence(EvidenceKind.DEVICE_SECURITY_STATUS)
        types = [p.connector_type() for p in providers]
        assert "microsoft" in types
        assert "wazuh" in types
