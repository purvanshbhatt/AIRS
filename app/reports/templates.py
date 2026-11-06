"""
Server-side PDF/CSV/JSON renderers for every report template.

Every renderer takes the snapshot produced by
``app.reports.readiness_source.build_template_snapshot`` and turns it into
bytes. No renderer computes a score; every number printed here is read from
the snapshot (which was produced by the deterministic readiness pipeline).
When data is missing the renderer prints "Not yet verified" and the reason.

Templates:
  board_story         Boardroom briefing (narrative, deterministic text)
  monthly_ops         30-day operations health review
  hipaa_audit         HIPAA Security Rule safeguard mapping
  technical_telemetry Evidence ledger export (hash, connectors, verification)
  executive_pdf       Executive summary (readiness-based when no assessment)
  boss_report         ONE page, plain English, for a clinic director
  cyber_insurance     Underwriter binder (Coalition / Chubb / Travelers)
  msp_summary         1-2 page hand-off the MSP gives the clinic
"""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Sequence
from xml.sax.saxutils import escape as _xml_escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    KeepInFrame,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.reports.pdf import Colors

TEMPLATE_IDS: Sequence[str] = (
    "board_story",
    "monthly_ops",
    "hipaa_audit",
    "technical_telemetry",
    "executive_pdf",
    "boss_report",
    "cyber_insurance",
    "msp_summary",
)

TEMPLATE_TITLES: Dict[str, str] = {
    "board_story": "Boardroom Cyber Resilience Briefing",
    "monthly_ops": "Monthly Operations Health Review",
    "hipaa_audit": "HIPAA Safeguards Verification Dossier",
    "technical_telemetry": "Cryptographic Telemetry Ledger Export",
    "executive_pdf": "Executive Readiness Report",
    "boss_report": "Monday Morning 1-Page Boss Report",
    "cyber_insurance": "Cyber Insurance Underwriter Verification Binder",
    "msp_summary": "MSP Readiness Summary",
}

NOT_VERIFIED = "Not yet verified"

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

PASS_GREEN = Colors.MEDIUM_BLUE          # emerald brand green
FAIL_RED = Colors.HIGH
WARN_ORANGE = Colors.MEDIUM
UNKNOWN_GRAY = Colors.GRAY
INK = Colors.DARK_BLUE
MUTED = Colors.DARK_GRAY
RULE = colors.HexColor("#e2e8f0")


# ──────────────────────────────────────────────────────────────────────────
# Styles & small helpers
# ──────────────────────────────────────────────────────────────────────────

def esc(value: Any) -> str:
    """XML-escape arbitrary values for reportlab Paragraphs."""
    if value is None:
        return ""
    return _xml_escape(str(value))


def _styles() -> Dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    st = {
        "title": ParagraphStyle("TplTitle", parent=base["Title"], fontName="Helvetica-Bold",
                                fontSize=20, leading=24, alignment=TA_LEFT, textColor=INK, spaceAfter=2),
        "subtitle": ParagraphStyle("TplSubtitle", parent=base["Normal"], fontName="Helvetica",
                                   fontSize=9.5, leading=12, textColor=MUTED, spaceAfter=8),
        "h2": ParagraphStyle("TplH2", parent=base["Heading2"], fontName="Helvetica-Bold",
                             fontSize=12.5, leading=15, textColor=INK, spaceBefore=12, spaceAfter=4),
        "h3": ParagraphStyle("TplH3", parent=base["Heading3"], fontName="Helvetica-Bold",
                             fontSize=10.5, leading=13, textColor=PASS_GREEN, spaceBefore=8, spaceAfter=3),
        "body": ParagraphStyle("TplBody", parent=base["Normal"], fontName="Helvetica",
                               fontSize=9.5, leading=13.5, textColor=Colors.TEXT, spaceAfter=5),
        "small": ParagraphStyle("TplSmall", parent=base["Normal"], fontName="Helvetica",
                                fontSize=8, leading=10.5, textColor=MUTED, spaceAfter=3),
        "cell": ParagraphStyle("TplCell", parent=base["Normal"], fontName="Helvetica",
                               fontSize=8.2, leading=10.5, textColor=Colors.TEXT),
        "cellb": ParagraphStyle("TplCellB", parent=base["Normal"], fontName="Helvetica-Bold",
                                fontSize=8.2, leading=10.5, textColor=INK),
        "cellh": ParagraphStyle("TplCellH", parent=base["Normal"], fontName="Helvetica-Bold",
                                fontSize=8.2, leading=10.5, textColor=colors.white),
        "kpi": ParagraphStyle("TplKpi", parent=base["Normal"], fontName="Helvetica-Bold",
                              fontSize=22, leading=26, textColor=INK),
        "kpilabel": ParagraphStyle("TplKpiLabel", parent=base["Normal"], fontName="Helvetica",
                                   fontSize=7.5, leading=9.5, textColor=MUTED),
        "headline": ParagraphStyle("TplHeadline", parent=base["Normal"], fontName="Helvetica-Bold",
                                   fontSize=14, leading=18, textColor=INK, spaceAfter=4),
    }
    return st


def _p(text: str, style: ParagraphStyle, escape: bool = True) -> Paragraph:
    return Paragraph(esc(text) if escape else text, style)


def _fmt_ts(value: Optional[str]) -> str:
    if not value:
        return NOT_VERIFIED
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return str(value)


def _status_color(status: str) -> colors.Color:
    return {
        "pass": PASS_GREEN,
        "verified": PASS_GREEN,
        "safe_to_open": PASS_GREEN,
        "healthy": PASS_GREEN,
        "fail": FAIL_RED,
        "critical_risk": FAIL_RED,
        "unreachable": FAIL_RED,
        "warning": WARN_ORANGE,
        "action_needed": WARN_ORANGE,
        "degraded": WARN_ORANGE,
    }.get((status or "").lower(), UNKNOWN_GRAY)


STATUS_LABELS = {
    "safe_to_open": "Safe to operate",
    "action_needed": "Action needed",
    "critical_risk": "Critical risk",
    "unknown": "Not yet verified",
}

CHECK_LABELS = {"pass": "Verified OK", "fail": "Needs attention", "warning": "Watch", "unknown": NOT_VERIFIED}


_HEADER_STYLE = ParagraphStyle("TplCellHeader", fontName="Helvetica-Bold", fontSize=8.2,
                               leading=10.5, textColor=colors.white)


def _table(rows: List[List[Any]], col_widths: List[float], header: bool = True,
           zebra: bool = True, font_size: float = 8.2) -> Table:
    if header and rows:
        # Header cells are Paragraphs; TableStyle TEXTCOLOR does not reach them.
        rows[0] = [Paragraph(c.text, _HEADER_STYLE) if isinstance(c, Paragraph) else c for c in rows[0]]
    t = Table(rows, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, RULE),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), INK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), Colors.LIGHT_GRAY))
    t.setStyle(TableStyle(style))
    return t


def _kpi_row(items: List[tuple], st: Dict[str, ParagraphStyle]) -> Table:
    """items: [(value_str, label_str, color)]"""
    cells = []
    for value, label, color in items:
        # Numeric KPIs stay large; status words shrink so they never wrap.
        size = 22 if value.replace("/100", "").replace("%", "").replace("-", "").strip().isdigit() else 14
        style = ParagraphStyle("kpi-" + label, parent=st["kpi"], textColor=color, fontSize=size, leading=26)
        cells.append([Paragraph(esc(value), style), Paragraph(esc(label), st["kpilabel"])])
    data = [[c[0] for c in cells], [c[1] for c in cells]]
    w = CONTENT_W / max(1, len(items))
    t = Table(data, colWidths=[w] * len(items))
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, RULE),
        ("BACKGROUND", (0, 0), (-1, -1), Colors.LIGHT_GRAY),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 6),
    ]))
    return t


# ──────────────────────────────────────────────────────────────────────────
# Snapshot accessors (pure reads; no computation of scores)
# ──────────────────────────────────────────────────────────────────────────

OWNER_BY_CATEGORY = {
    "access_control": "IT administrator (identity platform)",
    "backup": "Backup operator / MSP",
    "device_security": "IT / endpoint owner",
    "general": "Practice manager",
}


def _owner_for(check: Dict[str, Any], msp: Optional[Dict[str, Any]]) -> str:
    action = check.get("action") or {}
    category = action.get("category") or "general"
    perms = action.get("required_permissions") or []
    if msp and category in ("backup", "device_security", "general"):
        return f"{msp.get('msp_name')} (MSP)"
    if perms:
        return ", ".join(perms)
    return OWNER_BY_CATEGORY.get(category, OWNER_BY_CATEGORY["general"])


def _verif(check: Dict[str, Any]) -> Dict[str, Any]:
    return check.get("verification") or {}


def flatten_findings(snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    """All open items (failed, warnings, unknowns) as flat rows. Used by CSV
    export and by every template's 'needs attention' table."""
    readiness = snapshot.get("readiness") or {}
    msp = snapshot.get("msp")
    rows: List[Dict[str, Any]] = []
    for severity, key in (("fail", "failed_checks"), ("warning", "warnings")):
        for c in readiness.get(key) or []:
            v = _verif(c)
            a = c.get("action") or {}
            rows.append({
                "severity": severity,
                "label": c.get("label") or "",
                "detail": c.get("detail") or "",
                "category": a.get("category") or "general",
                "owner": _owner_for(c, msp),
                "recommended_action": a.get("recommended_action") or "",
                "estimated_minutes": a.get("estimated_time_minutes"),
                "source": v.get("verification_source") or "",
                "verification_status": v.get("verification_status") or "",
                "last_verified_at": v.get("last_verified_at") or "",
            })
    for u in readiness.get("unknowns") or []:
        rows.append({
            "severity": "unknown",
            "label": u.get("label") or "",
            "detail": u.get("impact") or "",
            "category": "visibility",
            "owner": (msp or {}).get("msp_name") and f"{msp['msp_name']} (MSP)" or OWNER_BY_CATEGORY["general"],
            "recommended_action": "Restore the data feed so this item can be verified.",
            "estimated_minutes": None,
            "source": u.get("source") or "",
            "verification_status": "unverified",
            "last_verified_at": u.get("last_seen") or "",
        })
    return rows


def _passed(snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    return (snapshot.get("readiness") or {}).get("passed_checks") or []


def _coverage(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    return (snapshot.get("readiness") or {}).get("coverage") or {"coverage_pct": 0, "monitored": [], "not_monitored": []}


def _score_text(snapshot: Dict[str, Any]) -> str:
    score = snapshot.get("overall_score")
    readiness = snapshot.get("readiness") or {}
    if score is None or readiness.get("status") == "unknown" and not readiness.get("checks_performed"):
        return "--"
    return f"{round(float(score))}"


def _why_unknown(snapshot: Dict[str, Any]) -> str:
    connectors = snapshot.get("connectors") or []
    events = snapshot.get("telemetry_event_count") or 0
    if not connectors:
        return "No connectors are configured for this organization, so no telemetry has been received."
    if events == 0:
        return "Connectors exist but no telemetry was received in the last 24 hours."
    return "Telemetry was received but no readiness checks could be evaluated from it."


def _header(story: List, snapshot: Dict[str, Any], title: str, st: Dict[str, ParagraphStyle],
            audience: Optional[str] = None) -> None:
    org = snapshot.get("organization") or {}
    name = org.get("clinic_name") or org.get("name") or "Organization"
    story.append(_p(title, st["title"]))
    meta = (
        f"{esc(name)} &nbsp;|&nbsp; Generated {esc(_fmt_ts(snapshot.get('generated_at')))} "
        f"&nbsp;|&nbsp; Source: {esc(_source_label(snapshot))}"
    )
    if audience:
        meta += f" &nbsp;|&nbsp; Audience: {esc(audience)}"
    story.append(Paragraph(meta, st["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.2, color=PASS_GREEN, spaceAfter=8))


def _source_label(snapshot: Dict[str, Any]) -> str:
    src = snapshot.get("data_source")
    if src == "demo_telemetry":
        return "Demo telemetry (sandbox organization)"
    return "Deterministic readiness snapshot (connector telemetry)"


def _footer_text(snapshot: Dict[str, Any]) -> str:
    return (
        "CONFIDENTIAL | Metrics sourced from the ResilAI deterministic scoring engine | "
        f"evidence {snapshot.get('evidence_hash', '')[:16]}"
    )


def _on_page(snapshot: Dict[str, Any]) -> Callable:
    text = _footer_text(snapshot)

    def _draw(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, 10 * mm, text[:110])
        canvas.drawRightString(PAGE_W - MARGIN, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    return _draw


def _status_summary(snapshot: Dict[str, Any], st) -> List:
    readiness = snapshot.get("readiness") or {}
    status = readiness.get("status") or "unknown"
    out = [_kpi_row([
        (_score_text(snapshot) + ("" if _score_text(snapshot) == "--" else "/100"), "Readiness score", _status_color(status)),
        (STATUS_LABELS.get(status, status), "Status today", _status_color(status)),
        (f"{_coverage(snapshot).get('coverage_pct', 0)}%", "Security areas monitored", INK),
        (str(snapshot.get("findings_count", 0)), "Open items", FAIL_RED if snapshot.get("findings_count") else PASS_GREEN),
    ], st)]
    if status == "unknown":
        out.append(Spacer(1, 4))
        out.append(_p(f"{NOT_VERIFIED}: {_why_unknown(snapshot)}", st["small"]))
    return out


def _findings_table(rows: List[Dict[str, Any]], st, limit: Optional[int] = None,
                    with_owner: bool = True) -> Any:
    if not rows:
        return _p("No open items. Every evaluated check passed.", st["body"])
    data = [[_p("Status", st["cellb"]), _p("Item", st["cellb"]), _p("Why it matters", st["cellb"])]]
    widths = [22 * mm, 68 * mm, 84 * mm]
    if with_owner:
        data[0].append(_p("Owner", st["cellb"]))
        widths = [20 * mm, 58 * mm, 60 * mm, 36 * mm]
    for r in rows[:limit] if limit else rows:
        color = _status_color(r["severity"])
        status_style = ParagraphStyle("s" + r["severity"], parent=st["cellb"], textColor=color)
        row = [
            Paragraph(esc(CHECK_LABELS.get(r["severity"], r["severity"])), status_style),
            _p(r["label"], st["cell"]),
            _p(r["detail"], st["cell"]),
        ]
        if with_owner:
            row.append(_p(r["owner"], st["cell"]))
        data.append(row)
    return _table(data, widths)


def _coverage_table(snapshot: Dict[str, Any], st) -> Table:
    cov = _coverage(snapshot)
    monitored = cov.get("monitored") or []
    not_monitored = cov.get("not_monitored") or []
    rows = [[_p("Monitored", st["cellb"]), _p("Source", st["cellb"]), _p("Not monitored", st["cellb"])]]
    n = max(len(monitored), len(not_monitored), 1)
    for i in range(n):
        m = monitored[i] if i < len(monitored) else None
        nm = not_monitored[i] if i < len(not_monitored) else None
        rows.append([
            _p(m["area"] if m else "", st["cell"]),
            _p((m or {}).get("source") or ("" if not m else "Connector"), st["cell"]),
            _p(nm["area"] if nm else "", st["cell"]),
        ])
    if not monitored and not not_monitored:
        rows.append([_p(NOT_VERIFIED, st["cell"]), _p("", st["cell"]), _p("No coverage data", st["cell"])])
    return _table(rows, [62 * mm, 50 * mm, 62 * mm])


def _connectors_table(snapshot: Dict[str, Any], st) -> Any:
    conns = snapshot.get("connectors") or []
    readiness_conns = {c.get("name"): c for c in (snapshot.get("readiness") or {}).get("connectors") or []}
    if not conns and not readiness_conns:
        return _p(f"{NOT_VERIFIED}: no connectors are configured for this organization.", st["body"])
    rows = [[_p(h, st["cellb"]) for h in ("Connector", "Type", "Status", "Health", "Last sync", "Covers")]]
    seen = set()
    for c in conns:
        seen.add(c.get("name"))
        rc = readiness_conns.get(c.get("name")) or {}
        rows.append([
            _p(c.get("name"), st["cell"]),
            _p(c.get("type"), st["cell"]),
            _p(c.get("status") or NOT_VERIFIED, st["cell"]),
            _p(c.get("health_status") or rc.get("status") or NOT_VERIFIED, st["cell"]),
            _p(_fmt_ts(c.get("last_sync_at") or rc.get("last_verified_at")), st["cell"]),
            _p(", ".join(rc.get("coverage") or []) or "--", st["cell"]),
        ])
    for name, rc in readiness_conns.items():
        if name in seen:
            continue
        rows.append([
            _p(name, st["cell"]), _p("telemetry", st["cell"]),
            _p("connected" if rc.get("connected") else "disconnected", st["cell"]),
            _p(rc.get("status") or NOT_VERIFIED, st["cell"]),
            _p(_fmt_ts(rc.get("last_verified_at")), st["cell"]),
            _p(", ".join(rc.get("coverage") or []) or "--", st["cell"]),
        ])
    return _table(rows, [34 * mm, 22 * mm, 20 * mm, 20 * mm, 36 * mm, 42 * mm])


def _value_table(snapshot: Dict[str, Any], st) -> Table:
    v = (snapshot.get("readiness") or {}).get("value") or {}
    rows = [
        [_p("Metric", st["cellb"]), _p(v.get("period_label") or "Last 30 days", st["cellb"])],
        [_p("Accounts protected", st["cell"]), _p(str(v.get("accounts_protected", 0)), st["cell"])],
        [_p("Devices protected", st["cell"]), _p(str(v.get("devices_protected", 0)), st["cell"])],
        [_p("Backups verified", st["cell"]), _p(str(v.get("backups_verified", 0)), st["cell"])],
        [_p("Problems prevented", st["cell"]), _p(str(v.get("problems_prevented", 0)), st["cell"])],
        [_p("Estimated downtime avoided (hours)", st["cell"]), _p(str(v.get("estimated_downtime_avoided_hours", 0)), st["cell"])],
    ]
    return _table(rows, [100 * mm, 74 * mm])


BACKUP_LABEL_KEYS = ["backup hasn't", "backup has not", "backup job", "backup fail", "backup complet", "restore test", "not backed up"]


def _check_matches(check: Dict[str, Any], categories: List[str], label_keys: List[str]) -> bool:
    cat = (check.get("action") or {}).get("category")
    label = (check.get("label") or "").lower()
    return (bool(categories) and cat in categories) or any(k in label for k in label_keys)


def _backup_status(snapshot: Dict[str, Any]) -> Dict[str, str]:
    """Backup state read from checks + coverage. Returns label/detail/state."""
    readiness = snapshot.get("readiness") or {}
    for key, state in (("failed_checks", "fail"), ("warnings", "warning"), ("passed_checks", "pass")):
        for c in readiness.get(key) or []:
            if _check_matches(c, ["backup"], BACKUP_LABEL_KEYS):
                return {"state": state, "label": c.get("label") or "", "detail": c.get("detail") or ""}
    cov = _coverage(snapshot)
    for a in cov.get("monitored") or []:
        if "backup" in (a.get("area") or "").lower():
            return {"state": "pass", "label": "Backup system reporting; no failed backup jobs in the evaluated window.",
                    "detail": f"Source: {a.get('source') or 'connector'}"}
    return {"state": "unknown", "label": f"{NOT_VERIFIED}: no backup system is connected.",
            "detail": "Connect the backup appliance or cloud backup so restore readiness can be proven."}


# ──────────────────────────────────────────────────────────────────────────
# Template builders
# ──────────────────────────────────────────────────────────────────────────

def _build_board_story(snapshot: Dict[str, Any], st) -> List:
    story: List = []
    _header(story, snapshot, TEMPLATE_TITLES["board_story"], st, audience="Board / non-technical leadership")
    story += _status_summary(snapshot, st)
    readiness = snapshot.get("readiness") or {}
    findings = flatten_findings(snapshot)
    passed = _passed(snapshot)
    bc = ((readiness.get("business_continuity") or {}).get("operational_readiness") or {})
    cov = _coverage(snapshot)
    org = snapshot.get("organization") or {}
    name = org.get("clinic_name") or org.get("name") or "the organization"

    story.append(_p("1. Where we stand", st["h2"]))
    status = readiness.get("status") or "unknown"
    if status == "unknown":
        text = (f"ResilAI cannot yet state whether {name} can operate safely. {_why_unknown(snapshot)} "
                "Until telemetry flows, every control below is reported as not yet verified rather than assumed.")
    else:
        text = (f"{name} is rated {STATUS_LABELS.get(status, status).lower()} with a readiness score of "
                f"{_score_text(snapshot)} out of 100. {len(passed)} control(s) were verified as working, "
                f"{len(findings)} item(s) need attention. {cov.get('coverage_pct', 0)}% of defined security areas "
                "are under continuous monitoring.")
    story.append(_p(text, st["body"]))

    story.append(_p("2. Can we operate and recover?", st["h2"]))
    rows = [
        [_p("Question", st["cellb"]), _p("Answer", st["cellb"]), _p("Basis", st["cellb"])],
        [_p("Can the organization operate today?", st["cell"]),
         _p("Yes" if bc.get("can_operate_today") else ("No" if status != "unknown" else NOT_VERIFIED), st["cell"]),
         _p("; ".join(bc.get("current_blockers") or []) or "No blockers recorded", st["cell"])],
        [_p("Can we recover from an incident?", st["cell"]),
         _p("Yes" if bc.get("can_recover") else ("No" if status != "unknown" else NOT_VERIFIED), st["cell"]),
         _p(_backup_status(snapshot)["label"], st["cell"])],
        [_p("Critical systems verified", st["cell"]),
         _p(", ".join(bc.get("critical_systems_verified") or []) or "None verified", st["cell"]),
         _p("Assumed (not verified): " + (", ".join(bc.get("critical_systems_assumed") or []) or "none"), st["cell"])],
    ]
    story.append(_table(rows, [52 * mm, 30 * mm, 92 * mm]))

    story.append(_p("3. What needs the board's attention", st["h2"]))
    story.append(_findings_table(findings, st, limit=8))

    story.append(_p("4. What is protected", st["h2"]))
    if passed:
        story.append(_table([[_p("Verified control", st["cellb"]), _p("Source", st["cellb"]), _p("Last verified", st["cellb"])]] + [
            [_p(c.get("label"), st["cell"]), _p(_verif(c).get("verification_source") or "--", st["cell"]),
             _p(_fmt_ts(_verif(c).get("last_verified_at")), st["cell"])] for c in passed[:10]
        ], [96 * mm, 38 * mm, 40 * mm]))
    else:
        story.append(_p(f"{NOT_VERIFIED}: no control has passed an automated check yet.", st["body"]))

    story.append(_p("5. Security visibility", st["h2"]))
    story.append(_coverage_table(snapshot, st))

    story.append(_p("6. Value delivered", st["h2"]))
    story.append(_value_table(snapshot, st))

    story.append(_p("7. What we ask of the board", st["h2"]))
    asks = []
    if findings:
        asks.append(f"Endorse remediation of the {len(findings)} open item(s) above; each lists an accountable owner.")
    if cov.get("not_monitored"):
        areas = ", ".join(a["area"] for a in cov["not_monitored"][:4])
        asks.append(f"Approve connecting the unmonitored areas ({areas}) so they can be verified rather than assumed.")
    if _backup_status(snapshot)["state"] != "pass":
        asks.append("Require proof of a successful restore test before the next review.")
    if not asks:
        asks.append("No new asks. Maintain current monitoring and review again next month.")
    for a in asks:
        story.append(_p("- " + a, st["body"]))
    return story


def _build_monthly_ops(snapshot: Dict[str, Any], st) -> List:
    story: List = []
    _header(story, snapshot, TEMPLATE_TITLES["monthly_ops"], st, audience="Operations / IT")
    readiness = snapshot.get("readiness") or {}
    story += _status_summary(snapshot, st)

    story.append(_p("Operational metrics", st["h2"]))
    rows = [[_p("Metric", st["cellb"]), _p("Value", st["cellb"]), _p("Note", st["cellb"])]]
    metrics = [
        ("Connector health", f"{readiness.get('connector_health_pct', 0)}%", "Share of configured connectors reporting healthy"),
        ("Checks performed", str(readiness.get("checks_performed", 0)), "Automated readiness checks in the evaluated window"),
        ("Devices checked", str(readiness.get("devices_checked", 0)), "From device/endpoint telemetry"),
        ("Accounts checked", str(readiness.get("accounts_checked", 0)), "From identity telemetry"),
        ("Backups verified", str(readiness.get("backups_verified", 0)), "Completed backup jobs observed"),
        ("Telemetry events (24h)", str(snapshot.get("telemetry_event_count", 0)), "Raw events consumed by the engine"),
        ("Verification confidence", f"{(readiness.get('verification') or {}).get('confidence_pct', 0)}%", "Trust engine confidence in this report"),
    ]
    for m in metrics:
        rows.append([_p(m[0], st["cell"]), _p(m[1], st["cell"]), _p(m[2], st["cell"])])
    story.append(_table(rows, [50 * mm, 30 * mm, 94 * mm]))

    story.append(_p("Connector inventory", st["h2"]))
    story.append(_connectors_table(snapshot, st))

    story.append(_p("Readiness checks", st["h2"]))
    all_rows = flatten_findings(snapshot)
    story.append(_findings_table(all_rows, st))
    passed = _passed(snapshot)
    if passed:
        story.append(_p("Passed checks", st["h3"]))
        story.append(_table([[_p("Check", st["cellb"]), _p("Source", st["cellb"]), _p("Verified", st["cellb"])]] + [
            [_p(c.get("label"), st["cell"]), _p(_verif(c).get("verification_source") or "--", st["cell"]),
             _p(_verif(c).get("data_age_description") or _fmt_ts(_verif(c).get("last_verified_at")), st["cell"])]
            for c in passed
        ], [100 * mm, 36 * mm, 38 * mm]))

    story.append(_p("Coverage", st["h2"]))
    story.append(_coverage_table(snapshot, st))

    story.append(_p("30-day trend", st["h2"]))
    points = (readiness.get("trend") or {}).get("points") or []
    if points:
        story.append(_table([[_p("Date", st["cellb"]), _p("Health %", st["cellb"]), _p("What changed", st["cellb"])]] + [
            [_p(p.get("date"), st["cell"]), _p(str(p.get("clinic_health_pct")), st["cell"]),
             _p("; ".join(p.get("delta_reasons") or []) or "--", st["cell"])] for p in points[-30:]
        ], [30 * mm, 24 * mm, 120 * mm]))
    else:
        story.append(_p("No daily history recorded yet. Trend data accrues after the first full day of monitoring.", st["body"]))

    story.append(_p("Value delivered", st["h2"]))
    story.append(_value_table(snapshot, st))

    timeline = readiness.get("timeline") or []
    if timeline:
        story.append(_p("Timeline", st["h2"]))
        story.append(_table([[_p("When", st["cellb"]), _p("Event", st["cellb"]), _p("Source", st["cellb"])]] + [
            [_p(_fmt_ts(t.get("timestamp")), st["cell"]), _p(t.get("label"), st["cell"]), _p(t.get("source"), st["cell"])]
            for t in timeline[:40]
        ], [36 * mm, 100 * mm, 38 * mm]))
    return story


DEVICE_LABEL_KEYS = ["security warning", "endpoint", "malware", "edr", "device", "unpatched"]
ACCESS_LABEL_KEYS = ["account is still active", "haven't signed in", "former", "departed", "offboard"]
MFA_LABEL_KEYS = ["mfa", "multi-factor", "two-factor", "2fa"]
EMAIL_LABEL_KEYS = ["email security", "phishing", "spf", "dkim", "dmarc", "mail filter"]
FIREWALL_LABEL_KEYS = ["firewall", "perimeter"]

HIPAA_MAP = [
    # (citation, safeguard, coverage areas (substring), check categories, label keywords)
    ("§164.308(a)(1)(ii)(D)", "Information system activity review", ["Network Logs", "Endpoints"], ["device_security"], DEVICE_LABEL_KEYS),
    ("§164.308(a)(3)", "Workforce security: terminate access when staff leave", ["Users"], ["access_control"], ACCESS_LABEL_KEYS),
    ("§164.308(a)(5)(ii)(D)", "Password / credential management", ["Users", "Multi-Factor"], [], MFA_LABEL_KEYS + ["password"]),
    ("§164.308(a)(7)", "Contingency plan: data backup and disaster recovery", ["Backup"], ["backup"], BACKUP_LABEL_KEYS),
    ("§164.310(d)", "Device and media controls", ["Devices"], ["device_security"], DEVICE_LABEL_KEYS),
    ("§164.312(a)(1)", "Technical access control (unique user ID, automatic logoff)", ["Users"], ["access_control"], ACCESS_LABEL_KEYS),
    ("§164.312(b)", "Audit controls", ["Network Logs"], [], ["audit log", "logging", "security warning"]),
    ("§164.312(c)", "Integrity of ePHI (backup verification)", ["Backup"], ["backup"], BACKUP_LABEL_KEYS),
    ("§164.312(d)", "Person or entity authentication (MFA)", ["Multi-Factor"], [], MFA_LABEL_KEYS),
    ("§164.312(e)", "Transmission security (email)", ["Email"], [], EMAIL_LABEL_KEYS),
]


def _area_state(snapshot: Dict[str, Any], area_keys: List[str], categories: List[str],
                label_keys: Optional[List[str]] = None) -> Dict[str, str]:
    """Evidence state for a safeguard: fail > warning > pass > monitored > not verified."""
    readiness = snapshot.get("readiness") or {}
    cov = _coverage(snapshot)
    label_keys = label_keys or []
    monitored_areas = [a for a in cov.get("monitored") or [] if any(k.lower() in (a.get("area") or "").lower() for k in area_keys)]

    def _matches(c):
        return _check_matches(c, categories, label_keys)

    for key, state in (("failed_checks", "fail"), ("warnings", "warning")):
        for c in readiness.get(key) or []:
            if _matches(c):
                return {"state": state, "evidence": c.get("label") or "", "source": _verif(c).get("verification_source") or "",
                        "verified_at": _verif(c).get("last_verified_at") or ""}
    for c in readiness.get("passed_checks") or []:
        if _matches(c):
            return {"state": "pass", "evidence": c.get("label") or "", "source": _verif(c).get("verification_source") or "",
                    "verified_at": _verif(c).get("last_verified_at") or ""}
    if monitored_areas:
        src = ", ".join(sorted({a.get("source") or "connector" for a in monitored_areas}))
        return {"state": "monitored", "evidence": "Area monitored; no failing check in the evaluated window.",
                "source": src, "verified_at": readiness.get("generated_at") or ""}
    return {"state": "unknown", "evidence": f"{NOT_VERIFIED}: no connector covers this safeguard.", "source": "", "verified_at": ""}


EVIDENCE_LABELS = {"pass": "Verified", "monitored": "Monitored", "fail": "Gap found", "warning": "Attention", "unknown": NOT_VERIFIED}


def _build_hipaa_audit(snapshot: Dict[str, Any], st) -> List:
    story: List = []
    _header(story, snapshot, TEMPLATE_TITLES["hipaa_audit"], st, audience="Compliance / auditors")
    story += _status_summary(snapshot, st)
    story.append(_p("Scope and method", st["h2"]))
    story.append(_p(
        "This dossier maps continuously verified technical safeguards to the HIPAA Security Rule "
        "(45 CFR Part 164, Subpart C). Each row states the evidence state observed by ResilAI from connected "
        "systems at generation time. A safeguard with no connected telemetry is reported as not yet verified; "
        "it is never assumed to be in place. This document supports, but does not replace, a formal risk analysis.",
        st["body"]))

    story.append(_p("Safeguard mapping", st["h2"]))
    rows = [[_p(h, st["cellb"]) for h in ("Citation", "Safeguard", "Evidence state", "Observed evidence", "Source / verified")]]
    for citation, safeguard, areas, cats, keys in HIPAA_MAP:
        s = _area_state(snapshot, areas, cats, keys)
        color = _status_color(s["state"]) if s["state"] != "monitored" else PASS_GREEN
        rows.append([
            _p(citation, st["cell"]), _p(safeguard, st["cell"]),
            Paragraph(esc(EVIDENCE_LABELS[s["state"]]), ParagraphStyle("ev" + s["state"], parent=st["cellb"], textColor=color)),
            _p(s["evidence"], st["cell"]),
            _p(((s["source"] + " / ") if s["source"] else "") + _fmt_ts(s["verified_at"] or None), st["cell"]),
        ])
    story.append(_table(rows, [26 * mm, 42 * mm, 22 * mm, 50 * mm, 34 * mm]))

    story.append(_p("Backup and recovery proof (§164.308(a)(7), §164.312(c))", st["h2"]))
    b = _backup_status(snapshot)
    story.append(_p(f"{EVIDENCE_LABELS.get(b['state'], b['state'])}: {b['label']} {b['detail']}", st["body"]))

    story.append(_p("Open findings", st["h2"]))
    story.append(_findings_table(flatten_findings(snapshot), st))

    story.append(_p("Control verification engine results", st["h2"]))
    vr = snapshot.get("verification_results") or []
    if vr:
        story.append(_table([[_p(h, st["cellb"]) for h in ("Control", "State", "Confidence", "Evidence items", "Last verified")]] + [
            [_p(r["control_id"], st["cell"]), _p(r["state"], st["cell"]), _p(r["confidence"], st["cell"]),
             _p(str(r["evidence_count"]), st["cell"]), _p(_fmt_ts(r["last_verified_at"]), st["cell"])] for r in vr
        ], [50 * mm, 30 * mm, 26 * mm, 28 * mm, 40 * mm]))
    else:
        story.append(_p(f"{NOT_VERIFIED}: the control verification engine has not recorded any control states for this organization.", st["body"]))

    story.append(_p("Coverage statement", st["h2"]))
    story.append(_coverage_table(snapshot, st))
    story.append(_p("Connected sources", st["h2"]))
    story.append(_connectors_table(snapshot, st))
    return story


def _build_technical_telemetry(snapshot: Dict[str, Any], st) -> List:
    story: List = []
    _header(story, snapshot, TEMPLATE_TITLES["technical_telemetry"], st, audience="Auditors / security engineers")
    readiness = snapshot.get("readiness") or {}
    story.append(_p("Evidence chain", st["h2"]))
    rows = [
        [_p("Field", st["cellb"]), _p("Value", st["cellb"])],
        [_p("Snapshot SHA-256", st["cell"]), _p(snapshot.get("evidence_hash", ""), st["cell"])],
        [_p("Readiness report id", st["cell"]), _p(readiness.get("report_id", ""), st["cell"])],
        [_p("Audit snapshot id", st["cell"]), _p(readiness.get("audit_snapshot_id") or "--", st["cell"])],
        [_p("Report date", st["cell"]), _p(readiness.get("report_date", ""), st["cell"])],
        [_p("Telemetry source", st["cell"]), _p(snapshot.get("data_source", ""), st["cell"])],
        [_p("Telemetry events consumed (24h)", st["cell"]), _p(str(snapshot.get("telemetry_event_count", 0)), st["cell"])],
        [_p("Snapshot schema", st["cell"]), _p(str(snapshot.get("schema_version", 1)), st["cell"])],
    ]
    story.append(_table(rows, [60 * mm, 114 * mm]))
    story += [Spacer(1, 6)] + _status_summary(snapshot, st)

    story.append(_p("Connector sync state", st["h2"]))
    story.append(_connectors_table(snapshot, st))

    story.append(_p("Control verification results", st["h2"]))
    vr = snapshot.get("verification_results") or []
    if vr:
        story.append(_table([[_p(h, st["cellb"]) for h in ("Control", "State", "Confidence", "Evidence", "Last verified")]] + [
            [_p(r["control_id"], st["cell"]), _p(r["state"], st["cell"]), _p(r["confidence"], st["cell"]),
             _p(str(r["evidence_count"]), st["cell"]), _p(_fmt_ts(r["last_verified_at"]), st["cell"])] for r in vr
        ], [50 * mm, 30 * mm, 26 * mm, 28 * mm, 40 * mm]))
    else:
        story.append(_p("No control verification records exist yet for this organization.", st["body"]))

    story.append(_p("Check-level verification context", st["h2"]))
    checks = []
    for key in ("failed_checks", "warnings", "passed_checks"):
        checks += readiness.get(key) or []
    if checks:
        story.append(_table([[_p(h, st["cellb"]) for h in ("Status", "Check", "Source", "Method", "Health", "Conf.", "Verified")]] + [
            [_p(c.get("status"), st["cell"]), _p(c.get("label"), st["cell"]),
             _p(_verif(c).get("verification_source") or "--", st["cell"]),
             _p(_verif(c).get("verification_method") or "--", st["cell"]),
             _p(_verif(c).get("connector_health") or "--", st["cell"]),
             _p(str(_verif(c).get("confidence_pct", "--")), st["cell"]),
             _p(_fmt_ts(_verif(c).get("last_verified_at")), st["cell"])] for c in checks
        ], [16 * mm, 58 * mm, 24 * mm, 24 * mm, 16 * mm, 10 * mm, 26 * mm]))
    else:
        story.append(_p(f"{NOT_VERIFIED}: no checks evaluated. {_why_unknown(snapshot)}", st["body"]))

    unknowns = readiness.get("unknowns") or []
    if unknowns:
        story.append(_p("Unverifiable items", st["h2"]))
        story.append(_table([[_p(h, st["cellb"]) for h in ("Item", "Impact", "Source", "Last seen")]] + [
            [_p(u.get("label"), st["cell"]), _p(u.get("impact"), st["cell"]), _p(u.get("source"), st["cell"]),
             _p(u.get("last_seen_description") or _fmt_ts(u.get("last_seen")), st["cell"])] for u in unknowns
        ], [60 * mm, 54 * mm, 30 * mm, 30 * mm]))

    story.append(_p("Verification reasons", st["h2"]))
    reasons = (readiness.get("verification") or {}).get("reasons") or []
    if reasons:
        for r in reasons:
            story.append(_p(f"[{r.get('icon')}] {r.get('text')}", st["body"]))
    else:
        story.append(_p("No verification reasons recorded.", st["body"]))
    return story


def _build_executive_readiness(snapshot: Dict[str, Any], st) -> List:
    story: List = []
    _header(story, snapshot, TEMPLATE_TITLES["executive_pdf"], st, audience="Executive leadership")
    story += _status_summary(snapshot, st)
    assessment = snapshot.get("assessment")
    if assessment:
        story.append(_p("Questionnaire assessment", st["h2"]))
        story.append(_p(
            f"{assessment.get('title') or 'Assessment'}: overall {assessment.get('overall_score')}/100, "
            f"tier {assessment.get('tier_label') or '--'}, {assessment.get('findings_count', 0)} finding(s) "
            f"({assessment.get('critical_high_count', 0)} critical/high).", st["body"]))
        ds = assessment.get("domain_scores") or []
        if ds:
            story.append(_table([[_p("Domain", st["cellb"]), _p("Score", st["cellb"])]] + [
                [_p(d.get("domain_name"), st["cell"]), _p(str(d.get("score")), st["cell"])] for d in ds
            ], [120 * mm, 54 * mm]))
    else:
        story.append(_p("Questionnaire assessment", st["h2"]))
        story.append(_p("No questionnaire assessment exists for this organization; this report is built from "
                        "continuous readiness telemetry only.", st["body"]))
    story.append(_p("Priority items", st["h2"]))
    story.append(_findings_table(flatten_findings(snapshot), st, limit=10))
    story.append(_p("What is verified", st["h2"]))
    passed = _passed(snapshot)
    if passed:
        for c in passed[:10]:
            story.append(_p("- " + (c.get("label") or ""), st["body"]))
    else:
        story.append(_p(f"{NOT_VERIFIED}: no control has passed an automated check yet. {_why_unknown(snapshot)}", st["body"]))
    story.append(_p("Coverage", st["h2"]))
    story.append(_coverage_table(snapshot, st))
    story.append(_p("Value delivered", st["h2"]))
    story.append(_value_table(snapshot, st))
    return story


def _business_meaning(snapshot: Dict[str, Any]) -> str:
    """Deterministic plain-English paragraph for the boss report."""
    readiness = snapshot.get("readiness") or {}
    status = readiness.get("status") or "unknown"
    findings = flatten_findings(snapshot)
    fails = [f for f in findings if f["severity"] == "fail"]
    backup = _backup_status(snapshot)
    cov = _coverage(snapshot).get("coverage_pct", 0)
    if status == "unknown":
        return (f"We cannot yet say whether the practice is protected. {_why_unknown(snapshot)} "
                "Nothing in this report is assumed: until systems are connected, every control counts as unverified. "
                "The single most valuable step this week is connecting the identity and backup systems.")
    if status == "safe_to_open":
        return (f"The practice can open and operate normally today. Every evaluated control passed and {cov}% of the "
                "defined security areas are watched continuously. "
                + ("Backups are confirmed, so a ransomware event would be recoverable. " if backup["state"] == "pass"
                   else "Backup status is not confirmed, so recovery from ransomware is not yet proven. ")
                + "Keep the current monitoring in place and review the unmonitored areas listed above.")
    if status == "critical_risk":
        return (f"The practice has {len(fails)} issue(s) that could directly expose patient records or stop operations. "
                "Each one has a named owner and a fix that takes minutes, not days. "
                + ("Backups are confirmed, so data can be restored if something goes wrong. " if backup["state"] == "pass"
                   else "Backups are not confirmed, so an incident today could mean real data loss. ")
                + "Ask the owners listed above to close these items before the end of the week.")
    return (f"The practice can operate today, but {len(findings)} item(s) need attention before they become incidents. "
            + ("Backups are confirmed. " if backup["state"] == "pass" else "Backup status is not yet confirmed. ")
            + f"{cov}% of defined security areas are monitored; the rest are assumed, not verified. "
            "Assign the owners above and re-check next Monday.")


def _build_boss_report(snapshot: Dict[str, Any], st) -> List:
    """Exactly one A4 page: wrapped in KeepInFrame(mode='shrink')."""
    readiness = snapshot.get("readiness") or {}
    status = readiness.get("status") or "unknown"
    org = snapshot.get("organization") or {}
    name = org.get("clinic_name") or org.get("name") or "Your practice"
    findings = flatten_findings(snapshot)
    passed = _passed(snapshot)
    backup = _backup_status(snapshot)
    cov = _coverage(snapshot)

    body: List = []
    body.append(_p(TEMPLATE_TITLES["boss_report"], st["title"]))
    body.append(Paragraph(
        f"{esc(name)} &nbsp;|&nbsp; {esc(_fmt_ts(snapshot.get('generated_at')))} &nbsp;|&nbsp; "
        f"Source: {esc(_source_label(snapshot))}", st["subtitle"]))
    body.append(HRFlowable(width="100%", thickness=1.2, color=PASS_GREEN, spaceAfter=6))

    headline = {
        "safe_to_open": "Headline: the practice is safe to operate today.",
        "action_needed": "Headline: the practice can operate, but a few things need fixing this week.",
        "critical_risk": "Headline: there are issues that need action today.",
        "unknown": "Headline: we cannot verify your protection yet because no systems are connected.",
    }[status if status in STATUS_LABELS else "unknown"]
    body.append(Paragraph(esc(headline), ParagraphStyle("hl", parent=st["headline"], textColor=_status_color(status))))
    body.append(_kpi_row([
        (_score_text(snapshot) + ("" if _score_text(snapshot) == "--" else "/100"), "Readiness score", _status_color(status)),
        (str(len(passed)), "Things verified OK", PASS_GREEN),
        (str(len(findings)), "Things needing attention", FAIL_RED if findings else PASS_GREEN),
        (f"{cov.get('coverage_pct', 0)}%", "Security areas watched", INK),
    ], st))
    body.append(Spacer(1, 6))

    def _three(title: str, items: List[str], empty: str):
        body.append(_p(title, st["h3"]))
        if not items:
            body.append(_p(empty, st["body"]))
        for it in items[:3]:
            body.append(_p("- " + it, st["body"]))

    fine = [c.get("label") or "" for c in passed]
    if not fine:
        fine = [f"{a['area']} is monitored by {a.get('source') or 'a connector'}" for a in cov.get("monitored") or []]
    _three("Three things that are fine", fine, f"{NOT_VERIFIED}: nothing has passed an automated check yet. {_why_unknown(snapshot)}")

    attention = [f"{f['label']} (who should act: {f['owner']})" for f in findings]
    _three("Three things that need attention", attention, "Nothing needs attention in the evaluated checks.")

    body.append(_p("Backup status", st["h3"]))
    body.append(Paragraph(
        f"<b>{esc(CHECK_LABELS.get(backup['state'], backup['state']))}.</b> {esc(backup['label'])} {esc(backup['detail'])}",
        st["body"]))

    body.append(_p("What this means for the business", st["h3"]))
    body.append(_p(_business_meaning(snapshot), st["body"]))

    msp = snapshot.get("msp")
    if msp:
        body.append(_p(f"Your IT provider: {msp.get('msp_name')} - {msp.get('contact_email') or ''} "
                       f"{('/ ' + msp['contact_phone']) if msp.get('contact_phone') else ''}", st["small"]))
    body.append(_p("Every number on this page comes from ResilAI's deterministic readiness engine. "
                   "Nothing is estimated by hand.", st["small"]))

    frame_h = PAGE_H - 2 * MARGIN - 8 * mm
    return [KeepInFrame(CONTENT_W, frame_h, body, mode="shrink", hAlign="LEFT")]


INSURANCE_CONTROLS = [
    # (control, area keys, categories, label keywords, Coalition, Chubb, Travelers)
    ("Multi-factor authentication (email, remote access, privileged accounts)",
     ["Multi-Factor"], [], MFA_LABEL_KEYS,
     "Sec. 2: Email & Access Security - MFA", "Cyber ERM Application: Access Controls / MFA", "CyberRisk App Q: MFA for remote access & email"),
    ("Immutable / offline backups with tested restores",
     ["Backup"], ["backup"], BACKUP_LABEL_KEYS,
     "Sec. 4: Backups - offline/immutable copies, restore testing", "Cyber ERM: Business Continuity & Backups", "CyberRisk App Q: Backups segregated & tested"),
    ("Lateral movement containment (EDR, endpoint hardening, network logging)",
     ["Endpoints", "Network Logs", "Devices"], ["device_security"], DEVICE_LABEL_KEYS,
     "Sec. 3: Endpoint Detection & Response", "Cyber ERM: Network Security / EDR", "CyberRisk App Q: EDR deployed on all endpoints"),
    ("Timely removal of departed-staff access",
     ["Users"], ["access_control"], ACCESS_LABEL_KEYS,
     "Sec. 2: Access management - account deprovisioning", "Cyber ERM: Access Controls - offboarding", "CyberRisk App Q: Privileged account hygiene"),
    ("Email security (filtering, authentication)",
     ["Email"], [], EMAIL_LABEL_KEYS,
     "Sec. 2: Email Security", "Cyber ERM: Email Security", "CyberRisk App Q: Email filtering & SPF/DKIM"),
    ("Firewall / perimeter monitoring",
     ["Firewall"], [], FIREWALL_LABEL_KEYS,
     "Sec. 3: Network Security", "Cyber ERM: Network Security", "CyberRisk App Q: Firewall & logging"),
]


def _build_cyber_insurance(snapshot: Dict[str, Any], st) -> List:
    story: List = []
    _header(story, snapshot, TEMPLATE_TITLES["cyber_insurance"], st, audience="Cyber insurance underwriters")
    story += _status_summary(snapshot, st)
    story.append(_p("How to read this binder", st["h2"]))
    story.append(_p(
        "Each control below is answered from telemetry observed by ResilAI at generation time and mapped to the "
        "questionnaire sections commonly used by Coalition, Chubb and Travelers. 'Verified' means a passing "
        "automated check exists; 'Monitored' means the area reports telemetry with no failing check; 'Gap found' "
        "means a failing check exists; 'Not yet verified' means no connected system covers the control and the "
        "applicant should answer from other evidence. ResilAI does not self-attest on the applicant's behalf.",
        st["body"]))

    story.append(_p("Control evidence matrix", st["h2"]))
    rows = [[_p(h, st["cellb"]) for h in ("Control", "Evidence state", "Observed evidence", "Source / verified")]]
    for control, areas, cats, keys, *_ in INSURANCE_CONTROLS:
        s = _area_state(snapshot, areas, cats, keys)
        color = PASS_GREEN if s["state"] in ("pass", "monitored") else _status_color(s["state"])
        rows.append([
            _p(control, st["cell"]),
            Paragraph(esc(EVIDENCE_LABELS[s["state"]]), ParagraphStyle("ins" + s["state"], parent=st["cellb"], textColor=color)),
            _p(s["evidence"], st["cell"]),
            _p(((s["source"] + " / ") if s["source"] else "") + _fmt_ts(s["verified_at"] or None), st["cell"]),
        ])
    story.append(_table(rows, [52 * mm, 24 * mm, 58 * mm, 40 * mm]))

    story.append(_p("Questionnaire cross-reference", st["h2"]))
    rows = [[_p(h, st["cellb"]) for h in ("Control", "Coalition", "Chubb", "Travelers")]]
    for control, _a, _c, _k, coalition, chubb, travelers in INSURANCE_CONTROLS:
        rows.append([_p(control, st["cell"]), _p(coalition, st["cell"]), _p(chubb, st["cell"]), _p(travelers, st["cell"])])
    story.append(_table(rows, [50 * mm, 42 * mm, 40 * mm, 42 * mm]))

    story.append(_p("Backup immutability and restore evidence", st["h2"]))
    b = _backup_status(snapshot)
    story.append(_p(f"{EVIDENCE_LABELS.get(b['state'], b['state'])}: {b['label']} {b['detail']}", st["body"]))
    readiness = snapshot.get("readiness") or {}
    story.append(_p(f"Backups verified in the evaluated window: {readiness.get('backups_verified', 0)}. "
                    "Immutability (air-gap / object lock) is reported only when the backup connector exposes it; "
                    "otherwise answer from vendor documentation.", st["small"]))

    story.append(_p("Open items that affect underwriting answers", st["h2"]))
    story.append(_findings_table(flatten_findings(snapshot), st))

    story.append(_p("Connected evidence sources", st["h2"]))
    story.append(_connectors_table(snapshot, st))
    story.append(_p("Coverage statement", st["h2"]))
    story.append(_coverage_table(snapshot, st))
    story.append(_p("This binder is evidence support for an insurance application. It is not a certification and "
                    "does not guarantee coverage or premium outcomes.", st["small"]))
    return story


def _build_msp_summary(snapshot: Dict[str, Any], st) -> List:
    story: List = []
    _header(story, snapshot, TEMPLATE_TITLES["msp_summary"], st, audience="Clinic leadership (prepared by MSP)")
    msp = snapshot.get("msp")
    readiness = snapshot.get("readiness") or {}
    story += _status_summary(snapshot, st)

    story.append(_p("Prepared by", st["h2"]))
    if msp:
        rows = [
            [_p("MSP", st["cellb"]), _p(msp.get("msp_name") or "--", st["cell"])],
            [_p("Contact", st["cellb"]), _p(" / ".join(x for x in (msp.get("contact_email"), msp.get("contact_phone")) if x) or "--", st["cell"])],
            [_p("Escalation", st["cellb"]), _p(msp.get("escalation_email") or "--", st["cell"])],
            [_p("Contract", st["cellb"]), _p(f"{msp.get('contract_type') or '--'} (response SLA {msp.get('response_sla_hours') or '--'} h)", st["cell"])],
        ]
        story.append(_table(rows, [34 * mm, 140 * mm], header=False, zebra=False))
    else:
        story.append(_p("No MSP relationship is on file for this organization. Add one under clinic settings so "
                        "escalation contacts print here.", st["body"]))

    story.append(_p("What we monitor vs. what we do not", st["h2"]))
    story.append(_coverage_table(snapshot, st))

    story.append(_p("Open issues and owners", st["h2"]))
    findings = flatten_findings(snapshot)
    story.append(_findings_table(findings, st))

    story.append(_p("Next actions", st["h2"]))
    actions = []
    for f in findings[:6]:
        fix = f["recommended_action"] or "Review and remediate."
        mins = f" (about {f['estimated_minutes']} min)" if f.get("estimated_minutes") else ""
        actions.append(f"{f['owner']}: {fix}{mins}")
    nm = _coverage(snapshot).get("not_monitored") or []
    if nm:
        actions.append("MSP: connect " + ", ".join(a["area"] for a in nm[:4]) + " so these areas are verified rather than assumed.")
    if not actions:
        actions.append("No actions required. Continue monitoring and review next month.")
    for a in actions:
        story.append(_p("- " + a, st["body"]))

    story.append(_p("What is working", st["h2"]))
    passed = _passed(snapshot)
    if passed:
        for c in passed[:8]:
            story.append(_p(f"- {c.get('label')} ({_verif(c).get('verification_source') or 'verified'})", st["body"]))
    else:
        story.append(_p(f"{NOT_VERIFIED}: {_why_unknown(snapshot)}", st["body"]))

    story.append(_p("Connectors", st["h2"]))
    story.append(_connectors_table(snapshot, st))
    v = readiness.get("value") or {}
    story.append(_p(f"Value this period ({v.get('period_label') or 'last 30 days'}): "
                    f"{v.get('accounts_protected', 0)} accounts protected, {v.get('devices_protected', 0)} devices protected, "
                    f"{v.get('backups_verified', 0)} backups verified, {v.get('problems_prevented', 0)} problems prevented.",
                    st["small"]))
    return story


BUILDERS: Dict[str, Callable[[Dict[str, Any], Dict[str, ParagraphStyle]], List]] = {
    "board_story": _build_board_story,
    "monthly_ops": _build_monthly_ops,
    "hipaa_audit": _build_hipaa_audit,
    "technical_telemetry": _build_technical_telemetry,
    "executive_pdf": _build_executive_readiness,
    "boss_report": _build_boss_report,
    "cyber_insurance": _build_cyber_insurance,
    "msp_summary": _build_msp_summary,
}


# ──────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────

def render_pdf(template: str, snapshot: Dict[str, Any]) -> bytes:
    """Render ``template`` from ``snapshot`` to PDF bytes."""
    builder = BUILDERS.get(template)
    if builder is None:
        raise ValueError(f"Unknown report template: {template}")
    st = _styles()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=MARGIN,
        title=TEMPLATE_TITLES.get(template, template),
        author="ResilAI",
        subject=f"{template} report",
    )
    story = builder(snapshot, st)
    on_page = _on_page(snapshot)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buffer.getvalue()


CSV_COLUMNS = [
    "severity", "label", "detail", "category", "owner", "recommended_action",
    "estimated_minutes", "source", "verification_status", "last_verified_at",
]


def render_csv(snapshot: Dict[str, Any]) -> bytes:
    """Flat findings export (open items plus passed checks)."""
    out = io.StringIO()
    writer = csv.writer(out)
    org = snapshot.get("organization") or {}
    writer.writerow(["# organization", org.get("name") or org.get("id") or ""])
    writer.writerow(["# template", snapshot.get("template") or ""])
    writer.writerow(["# generated_at", snapshot.get("generated_at") or ""])
    writer.writerow(["# overall_score", snapshot.get("overall_score") if snapshot.get("overall_score") is not None else NOT_VERIFIED])
    writer.writerow(["# evidence_hash", snapshot.get("evidence_hash") or ""])
    writer.writerow(CSV_COLUMNS)
    for row in flatten_findings(snapshot):
        writer.writerow([row.get(c, "") if row.get(c) is not None else "" for c in CSV_COLUMNS])
    for c in _passed(snapshot):
        v = _verif(c)
        writer.writerow([
            "pass", c.get("label") or "", c.get("detail") or "", (c.get("action") or {}).get("category") or "",
            "", "", "", v.get("verification_source") or "", v.get("verification_status") or "",
            v.get("last_verified_at") or "",
        ])
    return out.getvalue().encode("utf-8")


def render_json(snapshot: Dict[str, Any]) -> bytes:
    return json.dumps(snapshot, indent=2, default=str).encode("utf-8")


def render(template: str, fmt: str, snapshot: Dict[str, Any]) -> tuple[bytes, str, str]:
    """Render to (bytes, media_type, extension) for the requested format."""
    fmt = (fmt or "pdf").lower()
    if fmt == "json":
        return render_json(snapshot), "application/json", "json"
    if fmt == "csv":
        return render_csv(snapshot), "text/csv", "csv"
    return render_pdf(template, snapshot), "application/pdf", "pdf"
