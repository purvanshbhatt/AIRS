"""
Question bank: generic small-business cyber-insurance application.

A static, versioned list of the questions most cyber-insurance applications
for small businesses ask. The wording is ResilAI's own; it is not copied from
any carrier's form. Each question says whether connected systems can answer
it (``telemetry``) or only a person can (``human``), which connected sources
are read for it, and what those sources can never see (``blind_spots``).

Change the bank by editing this file and bumping ``QUESTION_BANK_VERSION``.
The answer engine (``insurance_answers.py``) refuses to start if a telemetry
question has no rule, so a new question cannot ship half-wired.

PRODUCT_MOAT: deterministic. No LLM writes, rewrites or answers a question.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

QUESTION_BANK_ID = "cyber_insurance_small_business"
QUESTION_BANK_VERSION = "2026.11.1"
QUESTION_BANK_TITLE = "Cyber insurance application (small business, generic)"

TELEMETRY = "telemetry"
HUMAN = "human"

# Display order of topics.
TOPICS: List[Tuple[str, str]] = [
    ("identity", "Email, accounts and sign-in"),
    ("email", "Email security"),
    ("backups", "Backups and recovery"),
    ("endpoints", "Computers and endpoint protection"),
    ("patching", "Patching and outdated software"),
    ("encryption", "Encryption"),
    ("network", "Network and remote access"),
    ("monitoring", "Security monitoring"),
    ("incident_response", "Incident response"),
    ("training", "Staff training and payments"),
    ("vendors", "Vendors and data"),
]
TOPIC_LABELS: Dict[str, str] = dict(TOPICS)


@dataclass(frozen=True)
class Question:
    id: str
    topic: str
    text: str
    mode: str  # TELEMETRY or HUMAN
    # Connected sources read for this question (keys of insurance_answers.SOURCES).
    sources: Tuple[str, ...] = ()
    # What no connected source can see, shown under coverage on every answer.
    blind_spots: Tuple[str, ...] = ()
    # Why a person has to answer (HUMAN questions only).
    human_reason: str = ""
    help: str = ""
    tags: Tuple[str, ...] = field(default_factory=tuple)


def _t(qid: str, topic: str, text: str, sources: Tuple[str, ...], blind_spots: Tuple[str, ...] = (),
       help: str = "") -> Question:
    return Question(id=qid, topic=topic, text=text, mode=TELEMETRY, sources=sources,
                    blind_spots=blind_spots, help=help)


def _h(qid: str, topic: str, text: str, reason: str, help: str = "") -> Question:
    return Question(id=qid, topic=topic, text=text, mode=HUMAN, human_reason=reason, help=help)


QUESTIONS: Tuple[Question, ...] = (
    # ── Email, accounts and sign-in ──────────────────────────────────────
    _t("EMAIL_MFA", "identity",
       "Does every person who signs in to company email have to use a second sign-in step "
       "(multi-factor authentication)?",
       ("microsoft",),
       ("Email accounts that are not in Microsoft 365 (for example Google Workspace or a hosting provider)",)),
    _t("ADMIN_MFA", "identity",
       "Do all administrator and other high-privilege accounts require multi-factor authentication?",
       ("aws",),
       ("Microsoft 365 administrator roles (the Microsoft connector does not report who is an administrator)",
        "Administrator logins for other systems (firewall, practice-management or document software)")),
    _t("REMOTE_ACCESS_MFA", "identity",
       "Is multi-factor authentication required whenever someone connects to your systems from outside "
       "the office (VPN, remote desktop, remote-access tools)?",
       ("duo",),
       ("Remote access that is not protected by Duo",)),
    _t("DORMANT_ACCOUNTS", "identity",
       "When someone leaves, is their account disabled or removed promptly, with no unused accounts left "
       "switched on?",
       ("microsoft", "aws"),
       ("Accounts in systems that are not connected (for example practice-management or billing software)",),
       help="Flags any switched-on account with no sign-in for more than 30 days."),
    _t("ACCESS_KEYS_ROTATED", "identity",
       "Are long-lived cloud access keys replaced (rotated) at least every 90 days?",
       ("aws",),
       ("Keys and tokens for cloud services other than AWS",)),
    _h("ADMIN_SEPARATE_ACCOUNTS", "identity",
       "Do administrators use a separate account for admin work, distinct from the one they use for "
       "everyday email and browsing?",
       "No connected system records which accounts belong to the same person."),

    # ── Email security ───────────────────────────────────────────────────
    _h("EMAIL_FILTERING", "email",
       "Is incoming email scanned for malicious attachments and links before it reaches staff?",
       "The connected systems do not report email-filtering settings."),
    _h("EMAIL_SENDER_AUTH", "email",
       "Have you published sender-authentication records for your email domain (SPF, DKIM and DMARC)?",
       "ResilAI does not yet read your domain's DNS records."),

    # ── Backups and recovery ─────────────────────────────────────────────
    _t("BACKUP_DAILY", "backups",
       "Are business-critical systems and data backed up at least once every 24 hours?",
       ("veeam", "aws"),
       ("Systems that are not in a connected backup product",)),
    _t("BACKUP_LAST_RUN", "backups",
       "Did the most recent run of every backup job finish successfully?",
       ("veeam",),
       ("Backup jobs in products that are not connected",)),
    _h("BACKUP_OFFLINE_COPY", "backups",
       "Do you keep at least one backup copy that is offline, separated from your network, or immutable "
       "(cannot be changed or deleted, even by an administrator)?",
       "The connected backup systems do not report whether a copy is offline or immutable."),
    _h("BACKUP_ENCRYPTED", "backups",
       "Are your backups encrypted?",
       "The connected backup systems do not report backup encryption settings."),
    _h("RESTORE_TESTED", "backups",
       "Have you successfully restored data from backup as a test within the last 12 months?",
       "No connected system records restore tests."),

    # ── Computers and endpoint protection ────────────────────────────────
    _t("ENDPOINT_PROTECTION", "endpoints",
       "Is endpoint protection (antivirus or EDR) installed, running and reporting on company computers "
       "and servers?",
       ("wazuh",),
       ("Computers and servers with no Wazuh agent installed cannot be seen by this check",)),
    _t("DEVICES_MANAGED", "endpoints",
       "Are company computers centrally managed, with a security baseline that each device meets?",
       ("microsoft",),
       ("Computers that are not enrolled in Microsoft Intune",)),

    # ── Patching and outdated software ───────────────────────────────────
    _t("CRITICAL_VULNS_PATCHED", "patching",
       "Are known critical-severity vulnerabilities on your computers and servers patched, with none "
       "currently outstanding?",
       ("wazuh", "aws"),
       ("Computers and servers with no vulnerability scanner reporting",)),
    _h("SUPPORTED_SOFTWARE", "patching",
       "Is all operating-system and business software still supported by its vendor (no end-of-life "
       "versions in use)?",
       "Software Watch lists end-of-life software it can see, but it is not yet linked to this answer, and "
       "it cannot see software on machines that are not connected."),
    _h("PATCH_PROCESS", "patching",
       "Do you have a routine for applying security updates, with critical updates applied within a set "
       "number of days?",
       "A patching routine is a process; connected systems show results, not the routine."),

    # ── Encryption ───────────────────────────────────────────────────────
    _t("DEVICE_ENCRYPTION", "encryption",
       "Are the hard drives of company laptops and desktops encrypted?",
       ("microsoft",),
       ("Computers that are not enrolled in Microsoft Intune", "Phones and tablets")),
    _t("CLOUD_ENCRYPTION", "encryption",
       "Is business data stored in your cloud hosting encrypted at rest?",
       ("aws",),
       ("Cloud services other than AWS (for example file-sharing or practice-management software)",)),

    # ── Network and remote access ────────────────────────────────────────
    _t("REMOTE_PORTS_CLOSED", "network",
       "Are remote-administration services such as Remote Desktop (RDP) and SSH closed to the open "
       "internet?",
       ("aws",),
       ("The office firewall and router", "Servers outside AWS")),
    _t("PUBLIC_STORAGE_BLOCKED", "network",
       "Is cloud storage that holds business data blocked from public access?",
       ("aws",),
       ("Cloud storage outside AWS (for example shared links in file-sharing services)",)),
    _h("REMOTE_ACCESS_VPN", "network",
       "Is remote access to internal systems only possible through a VPN or a secure access gateway?",
       "ResilAI can see some VPN links on the network map, but cannot prove there is no other way in."),
    _h("FIREWALL", "network",
       "Is a firewall in place between your office network and the internet?",
       "The office firewall is not a connected system."),

    # ── Security monitoring ──────────────────────────────────────────────
    _t("SECURITY_MONITORING", "monitoring",
       "Is security activity on your systems watched by a tool that raises alerts?",
       ("wazuh", "splunk", "microsoft"),
       ("Systems that no connected monitoring tool covers",)),
    _t("CLOUD_AUDIT_LOGGING", "monitoring",
       "Is activity logging (an audit trail of who did what) turned on for your cloud hosting accounts?",
       ("aws",),
       ("Cloud services other than AWS",)),
    _t("CLOUD_THREAT_DETECTION", "monitoring",
       "Is automated threat detection turned on for your cloud hosting accounts?",
       ("aws",),
       ("Cloud services other than AWS",)),
    _h("MONITORING_24X7", "monitoring",
       "Are security alerts watched around the clock, by your own staff or an outside provider?",
       "Who watches the alerts, and when, is not recorded by any connected system."),

    # ── Incident response ────────────────────────────────────────────────
    _h("IR_PLAN", "incident_response",
       "Do you have a written plan for responding to a cyber incident such as ransomware or a data breach?",
       "A plan is a document; no connected system can confirm it exists or is current."),
    _h("IR_TESTED", "incident_response",
       "Has that plan been rehearsed (for example a tabletop exercise) within the last 12 months?",
       "Rehearsals are not recorded by any connected system."),
    _h("IR_CONTACTS", "incident_response",
       "Do you know who you would call first in an incident (breach counsel, incident-response firm, "
       "your insurer's hotline)?",
       "Contacts and retainers are not recorded by any connected system."),
    _h("PRIOR_INCIDENTS", "incident_response",
       "In the last three years, have you had a cyber incident, data breach, ransomware attack or loss "
       "from fraudulent payment instructions?",
       "Claims and incident history must come from you; ResilAI only sees the period it has been connected."),

    # ── Staff training and payments ──────────────────────────────────────
    _h("SECURITY_TRAINING", "training",
       "Does every member of staff complete security-awareness training at least once a year?",
       "Training records are not held by any connected system."),
    _h("PHISHING_SIMULATION", "training",
       "Do you send staff simulated phishing emails to test and reinforce that training?",
       "Phishing simulations are not reported by any connected system."),
    _h("PAYMENT_VERIFICATION", "training",
       "Before sending money or changing a supplier's or client's bank details, do you confirm the request "
       "through a second, known channel (for example a phone call to a number you already have)?",
       "Payment procedures are a process; no connected system records them."),

    # ── Vendors and data ─────────────────────────────────────────────────
    _h("VENDOR_REVIEW", "vendors",
       "Do you check the security of vendors that store or can reach your sensitive records?",
       "Vendor reviews are not recorded by any connected system."),
    _h("VENDOR_REMOTE_ACCESS", "vendors",
       "Do outside IT providers have to use multi-factor authentication when they connect to your systems?",
       "Provider access paths are not all visible to connected systems."),
    _h("SENSITIVE_DATA_INVENTORY", "vendors",
       "Do you know which systems hold sensitive records (patient, client, payment or employee data) and "
       "roughly how many records there are?",
       "Record counts and data locations must come from you."),
)

QUESTIONS_BY_ID: Dict[str, Question] = {q.id: q for q in QUESTIONS}


def validate_bank() -> None:
    """Fail fast on a malformed bank (duplicate ids, unknown topics, missing reasons)."""
    if len(QUESTIONS_BY_ID) != len(QUESTIONS):
        raise ValueError("Duplicate question id in the insurance question bank")
    for q in QUESTIONS:
        if q.topic not in TOPIC_LABELS:
            raise ValueError(f"Question {q.id} has unknown topic {q.topic}")
        if q.mode == TELEMETRY and not q.sources:
            raise ValueError(f"Telemetry question {q.id} names no source")
        if q.mode == HUMAN and not q.human_reason:
            raise ValueError(f"Human-only question {q.id} gives no reason")


validate_bank()
