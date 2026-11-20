"""
PDF export of the insurance questionnaire answer pack.

Renders the pack built by ``app.services.questionnaires.insurance_answers``
with the shared report styles in ``app.reports.templates``. Nothing is
computed here: every value, sentence and time is read from the pack.

Page one carries the attestation notice ("You attest. ResilAI shows the
evidence it has, as of <time>."), the sample-data banner for demo
workspaces and the answer counts. The last section is a signature block
left blank: the customer signs, ResilAI never submits.
"""
from __future__ import annotations

import io
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.reports.templates import (
    CONTENT_W,
    FAIL_RED,
    INK,
    MARGIN,
    MUTED,
    PAGE_W,
    PASS_GREEN,
    RULE,
    UNKNOWN_GRAY,
    WARN_ORANGE,
    _fmt_ts,
    _kpi_row,
    _p,
    _styles,
    _table,
    esc,
)
from reportlab.lib.units import mm

VALUE_COLORS = {
    "yes": PASS_GREEN,
    "no": FAIL_RED,
    "partial": WARN_ORANGE,
    "not_verified": UNKNOWN_GRAY,
    "human_only": INK,
}


def _notice_box(text: str, st) -> Table:
    box = Table([[Paragraph(f"<b>{esc(text)}</b>", st["body"])]], colWidths=[CONTENT_W])
    box.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1.2, INK),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return box


def _sample_banner(st) -> Table:
    box = Table([[Paragraph(
        "<b>SAMPLE DATA.</b> This pack was built from a demo workspace's sample telemetry. "
        "It describes no real organisation and must not be sent to an insurer.", st["body"])]],
        colWidths=[CONTENT_W])
    box.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, WARN_ORANGE),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff7ed")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return box


def _evidence_cell(answer: Dict[str, Any], st) -> List[Any]:
    parts: List[Any] = [_p(answer.get("basis") or "", st["cell"])]
    if answer.get("evidence_source"):
        parts.append(_p(f"Evidence: {answer['evidence_source']}, as of {_fmt_ts(answer.get('evidence_time'))}",
                        st["small"]))
    coverage = answer.get("coverage") or {}
    if coverage.get("checked"):
        parts.append(_p("Looked at: " + "; ".join(coverage["checked"]), st["small"]))
    if coverage.get("not_checked"):
        parts.append(_p("Not looked at: " + "; ".join(coverage["not_checked"]), st["small"]))
    return parts


def _signature_block(pack: Dict[str, Any], st) -> List[Any]:
    statement = (pack.get("attestation") or {}).get("statement") or ""
    rows = [
        [_p("Name", st["cellb"]), "", _p("Title / role", st["cellb"]), ""],
        [_p("Signature", st["cellb"]), "", _p("Date", st["cellb"]), ""],
    ]
    table = Table(rows, colWidths=[CONTENT_W * 0.14, CONTENT_W * 0.34, CONTENT_W * 0.16, CONTENT_W * 0.34])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
        ("TOPPADDING", (0, 0), (-1, -1), 16),
        # Blank lines to sign on.
        ("LINEBELOW", (1, 0), (1, -1), 0.6, INK),
        ("LINEBELOW", (3, 0), (3, -1), 0.6, INK),
    ]))
    return [KeepTogether([
        _p("Attestation and signature", st["h2"]),
        _p(statement, st["body"]),
        table,
        Spacer(1, 4),
        _p("Left blank on purpose: the person who signs is responsible for the answers.", st["small"]),
    ])]


def build_story(pack: Dict[str, Any]) -> List[Any]:
    st = _styles()
    story: List[Any] = []
    org = pack.get("organization") or {}
    questionnaire = pack.get("questionnaire") or {}
    summary = pack.get("summary") or {}
    counts = summary.get("counts") or {}

    story.append(_p("Cyber insurance application: answer pack", st["title"]))
    story.append(Paragraph(
        f"{esc(org.get('name') or org.get('id') or '')} &nbsp;|&nbsp; Generated {esc(_fmt_ts(pack.get('generated_at')))} "
        f"&nbsp;|&nbsp; {esc(questionnaire.get('title') or '')}, question bank {esc(questionnaire.get('version') or '')}",
        st["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=1.2, color=PASS_GREEN, spaceAfter=8))

    story.append(_notice_box(pack.get("notice") or "", st))
    story.append(Spacer(1, 6))
    if pack.get("is_demo"):
        story.append(_sample_banner(st))
        story.append(Spacer(1, 6))
    story.append(_p(
        "Each answer shows the evidence it rests on, when that evidence was observed, and what was and was not "
        f"looked at. Evidence older than {pack.get('evidence_max_age_hours', 48)} hours, or from a connection that is "
        "failing, is never used: those questions read \"Not verified: answer manually\". Questions marked "
        "\"You answer this\" cannot be answered from connected systems. ResilAI does not submit this application; "
        "you review it, correct it and sign it.", st["body"]))

    story.append(_kpi_row([
        (str(counts.get("yes", 0)), "Yes", PASS_GREEN),
        (str(counts.get("no", 0)), "No", FAIL_RED),
        (str(counts.get("partial", 0)), "Partly", WARN_ORANGE),
        (str(counts.get("not_verified", 0)), "Not verified", UNKNOWN_GRAY),
        (str(counts.get("human_only", 0)), "You answer", INK),
    ], st))

    sources = pack.get("sources") or []
    if sources:
        story.append(_p("Connected sources", st["h2"]))
        rows = [[_p("Source", st["cellh"]), _p("State", st["cellh"]), _p("Newest evidence", st["cellh"])]]
        for s in sources:
            state = "Usable" if s.get("state") == "fresh" else (s.get("reason") or s.get("state"))
            rows.append([_p(s.get("label"), st["cellb"]), _p(state, st["cell"]),
                         _p(_fmt_ts(s.get("as_of")) if s.get("as_of") else "None", st["cell"])])
        story.append(_table(rows, [CONTENT_W * 0.25, CONTENT_W * 0.5, CONTENT_W * 0.25]))

    answers = pack.get("answers") or []
    for topic in pack.get("topics") or []:
        in_topic = [a for a in answers if a.get("topic") == topic.get("id")]
        if not in_topic:
            continue
        story.append(_p(topic.get("label"), st["h2"]))
        rows = [[_p("Question", st["cellh"]), _p("Answer", st["cellh"]), _p("Evidence", st["cellh"])]]
        for a in in_topic:
            color = VALUE_COLORS.get(a.get("value"), MUTED)
            answer_style = st["cellb"].clone("ans-" + str(a.get("id")), textColor=color)
            rows.append([_p(a.get("question"), st["cell"]), _p(a.get("value_label"), answer_style),
                         _evidence_cell(a, st)])
        story.append(_table(rows, [CONTENT_W * 0.34, CONTENT_W * 0.14, CONTENT_W * 0.52]))

    story.append(Spacer(1, 8))
    story.extend(_signature_block(pack, st))
    return story


def _on_page(pack: Dict[str, Any]):
    label = "SAMPLE DATA | " if pack.get("is_demo") else ""
    text = f"{label}{pack.get('notice') or ''}"

    def _draw(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTED)
        canvas.drawString(MARGIN, 10 * mm, text[:120])
        canvas.drawRightString(PAGE_W - MARGIN, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    return _draw


def render_answer_pack_pdf(pack: Dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN, topMargin=MARGIN, bottomMargin=MARGIN,
        title="Cyber insurance application: answer pack",
        author="ResilAI",
        subject="Questionnaire answer pack",
    )
    on_page = _on_page(pack)
    doc.build(build_story(pack), onFirstPage=on_page, onLaterPages=on_page)
    return buffer.getvalue()
