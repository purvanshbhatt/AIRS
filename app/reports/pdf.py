"""
Professional PDF Report Generator for AIRS Assessments.

Generates consultant-grade PDF reports with:
- Title page with organization and date
- Executive summary with overall score donut
- Domain heatmap table
- Top findings with severity badges
- 30/60/90 day remediation roadmap
- Appendix with all answers
"""

from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List, Tuple
import math

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable, Image
)
from reportlab.graphics.shapes import Drawing, Wedge, Circle, String, Rect
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF

from app.core.rubric import get_rubric


# =============================================================================
# COLOR PALETTE - Professional consulting-grade colors
# =============================================================================

class Colors:
    """Professional color palette."""
    # Primary
    DARK_BLUE = colors.HexColor('#1a365d')      # Headers
    MEDIUM_BLUE = colors.HexColor('#2b6cb0')    # Accents
    LIGHT_BLUE = colors.HexColor('#4299e1')     # Links, highlights
    
    # Severity
    CRITICAL = colors.HexColor('#9b2c2c')       # Dark red
    HIGH = colors.HexColor('#c53030')           # Red
    MEDIUM = colors.HexColor('#dd6b20')         # Orange
    LOW = colors.HexColor('#d69e2e')            # Yellow
    INFO = colors.HexColor('#3182ce')           # Blue
    
    # Heatmap
    HEAT_CRITICAL = colors.HexColor('#fed7d7')  # Light red (score 0-1)
    HEAT_LOW = colors.HexColor('#feebc8')       # Light orange (score 1-2)
    HEAT_MEDIUM = colors.HexColor('#fefcbf')    # Light yellow (score 2-3)
    HEAT_GOOD = colors.HexColor('#c6f6d5')      # Light green (score 3-4)
    HEAT_EXCELLENT = colors.HexColor('#9ae6b4') # Green (score 4-5)
    
    # Neutral
    WHITE = colors.white
    LIGHT_GRAY = colors.HexColor('#f7fafc')
    GRAY = colors.HexColor('#a0aec0')
    DARK_GRAY = colors.HexColor('#4a5568')
    TEXT = colors.HexColor('#2d3748')


def get_attr(obj: Any, key: str, default: Any = None) -> Any:
    """Get attribute from dict or object."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def get_severity_color(severity: str) -> colors.Color:
    """Get color for severity level."""
    severity_lower = str(severity).lower()
    if 'critical' in severity_lower:
        return Colors.CRITICAL
    elif 'high' in severity_lower:
        return Colors.HIGH
    elif 'medium' in severity_lower:
        return Colors.MEDIUM
    elif 'low' in severity_lower:
        return Colors.LOW
    return Colors.INFO


def get_heatmap_color(score: float) -> colors.Color:
    """Get heatmap color based on score (0-5 scale)."""
    if score < 1:
        return Colors.HEAT_CRITICAL
    elif score < 2:
        return Colors.HEAT_LOW
    elif score < 3:
        return Colors.HEAT_MEDIUM
    elif score < 4:
        return Colors.HEAT_GOOD
    return Colors.HEAT_EXCELLENT


# =============================================================================
# SCORE DONUT CHART
# =============================================================================

def create_score_donut(score: float, size: int = 150) -> Drawing:
    """
    Create a donut chart showing overall score.
    
    Args:
        score: Score from 0-100
        size: Diameter in points
    """
    drawing = Drawing(size, size)
    
    # Calculate angles (ReportLab uses degrees, 0 = 3 o'clock, counter-clockwise)
    score_angle = (score / 100) * 360
    remaining_angle = 360 - score_angle
    
    center = size / 2
    outer_radius = size / 2 - 5
    inner_radius = outer_radius * 0.6
    
    # Determine color based on score
    if score >= 80:
        score_color = Colors.HEAT_EXCELLENT
    elif score >= 60:
        score_color = Colors.HEAT_GOOD
    elif score >= 40:
        score_color = Colors.HEAT_MEDIUM
    elif score >= 20:
        score_color = Colors.HEAT_LOW
    else:
        score_color = Colors.HEAT_CRITICAL
    
    # Draw background circle (remaining portion)
    if remaining_angle > 0:
        bg_wedge = Wedge(
            center, center,
            outer_radius,
            90 - score_angle,  # Start after score wedge
            90,  # End at top
            radius1=inner_radius,
            fillColor=Colors.LIGHT_GRAY,
            strokeColor=None
        )
        drawing.add(bg_wedge)
    
    # Draw score wedge
    if score > 0:
        score_wedge = Wedge(
            center, center,
            outer_radius,
            90,  # Start at top (12 o'clock)
            90 - score_angle,  # End based on score
            radius1=inner_radius,
            fillColor=score_color,
            strokeColor=None
        )
        drawing.add(score_wedge)
    
    # Add center circle for cleaner look
    center_circle = Circle(
        center, center,
        inner_radius - 2,
        fillColor=Colors.WHITE,
        strokeColor=None
    )
    drawing.add(center_circle)
    
    # Score text in center
    score_text = String(
        center, center + 8,
        f"{score:.0f}",
        fontSize=28,
        fontName='Helvetica-Bold',
        fillColor=Colors.DARK_BLUE,
        textAnchor='middle'
    )
    drawing.add(score_text)
    
    # "out of 100" text
    label_text = String(
        center, center - 12,
        "out of 100",
        fontSize=10,
        fontName='Helvetica',
        fillColor=Colors.GRAY,
        textAnchor='middle'
    )
    drawing.add(label_text)
    
    return drawing


# =============================================================================
# PDF REPORT GENERATOR
# =============================================================================

class ProfessionalPDFGenerator:
    """Generate professional PDF assessment reports."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.rubric = get_rubric()
        self.page_width = letter[0] - 144  # Minus margins
    
    def _setup_custom_styles(self):
        """Configure professional typography."""
        # Main title
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            fontName='Helvetica-Bold',
            fontSize=32,
            leading=38,
            alignment=TA_CENTER,
            textColor=Colors.DARK_BLUE,
            spaceAfter=12
        ))
        
        # Subtitle
        self.styles.add(ParagraphStyle(
            name='ReportSubtitle',
            fontName='Helvetica',
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            textColor=Colors.MEDIUM_BLUE,
            spaceAfter=30
        ))
        
        # Section headers
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=Colors.DARK_BLUE,
            spaceBefore=20,
            spaceAfter=12,
            borderPadding=(0, 0, 5, 0)
        ))
        
        # Subsection headers
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=Colors.MEDIUM_BLUE,
            spaceBefore=15,
            spaceAfter=8
        ))
        
        # Body text - use unique name to avoid conflict
        self.styles.add(ParagraphStyle(
            name='ReportBodyText',
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=Colors.TEXT,
            alignment=TA_JUSTIFY,
            spaceAfter=8
        ))
        
        # Small text
        self.styles.add(ParagraphStyle(
            name='ReportSmallText',
            fontName='Helvetica',
            fontSize=8,
            leading=10,
            textColor=Colors.GRAY,
            spaceAfter=4
        ))
        
        # Finding title
        self.styles.add(ParagraphStyle(
            name='FindingTitle',
            fontName='Helvetica-Bold',
            fontSize=11,
            leading=14,
            textColor=Colors.TEXT,
            spaceBefore=8,
            spaceAfter=4
        ))
        
        # Finding body
        self.styles.add(ParagraphStyle(
            name='FindingBody',
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=Colors.DARK_GRAY,
            leftIndent=15,
            spaceAfter=6
        ))
        
        # Roadmap item
        self.styles.add(ParagraphStyle(
            name='RoadmapItem',
            fontName='Helvetica',
            fontSize=10,
            leading=13,
            textColor=Colors.TEXT,
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=4
        ))
        
        # Table header
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            fontName='Helvetica-Bold',
            fontSize=9,
            leading=11,
            textColor=Colors.WHITE,
            alignment=TA_CENTER
        ))
        
        # Table cell
        self.styles.add(ParagraphStyle(
            name='TableCell',
            fontName='Helvetica',
            fontSize=9,
            leading=11,
            textColor=Colors.TEXT
        ))
        
        # Metadata
        self.styles.add(ParagraphStyle(
            name='Metadata',
            fontName='Helvetica',
            fontSize=11,
            leading=16,
            textColor=Colors.DARK_GRAY,
            alignment=TA_CENTER,
            spaceAfter=6
        ))
    
    def generate(self, data: Dict[str, Any]) -> bytes:
        """
        Generate complete PDF report.
        
        Args:
            data: Assessment data dict with organization, scores, findings, answers
        
        Returns:
            PDF bytes
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
            title="AIRS Assessment Report"
        )
        
        story = []
        
        # Section 1: Title Page
        story.extend(self._build_title_page(data))
        story.append(PageBreak())
        
        # Section 2: Executive Summary with Score Donut
        story.extend(self._build_executive_summary(data))
        story.append(Spacer(1, 20))
        
        # Section 3: Domain Heatmap Table
        story.extend(self._build_domain_heatmap(data))
        story.append(PageBreak())
        
        # Section 4: Top Findings with Severity Badges
        story.extend(self._build_top_findings(data))
        story.append(Spacer(1, 20))
        
        # Section 5: 30/60/90 Day Roadmap
        story.extend(self._build_roadmap(data))
        story.append(PageBreak())
        
        # Section 6: Appendix - All Answers
        story.extend(self._build_appendix(data))
        
        doc.build(story)
        return buffer.getvalue()
    
    # =========================================================================
    # SECTION 1: TITLE PAGE
    # =========================================================================
    
    def _build_title_page(self, data: Dict[str, Any]) -> List:
        """Build professional title page."""
        elements = []
        
        # Top spacing
        elements.append(Spacer(1, 1.5 * inch))
        
        # Logo placeholder / AIRS branding
        elements.append(Paragraph("AIRS", self.styles['ReportTitle']))
        elements.append(Paragraph(
            "Artificial Intelligence Readiness Score",
            self.styles['ReportSubtitle']
        ))
        
        # Divider
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(HRFlowable(
            width="50%",
            thickness=2,
            color=Colors.MEDIUM_BLUE,
            spaceBefore=0,
            spaceAfter=30,
            hAlign='CENTER'
        ))
        
        # Report type
        elements.append(Paragraph(
            "Security Readiness Assessment Report",
            ParagraphStyle(
                'ReportType',
                parent=self.styles['Metadata'],
                fontSize=14,
                fontName='Helvetica-Bold',
                textColor=Colors.DARK_BLUE
            )
        ))
        
        elements.append(Spacer(1, 0.8 * inch))
        
        # Organization info table
        org_name = get_attr(data, "organization_name", "Unknown Organization")
        org_industry = get_attr(data, "organization_industry", "")
        org_size = get_attr(data, "organization_size", "")
        assessment_title = get_attr(data, "title", "Security Readiness Assessment")
        version = get_attr(data, "version", "1.0")
        report_date = datetime.now().strftime("%B %d, %Y")
        
        info_data = [
            ["Organization", org_name],
            ["Assessment", assessment_title],
            ["Date", report_date],
            ["Version", version],
        ]
        
        if org_industry:
            info_data.insert(1, ["Industry", org_industry])
        if org_size:
            info_data.insert(2, ["Size", org_size])
        
        info_table = Table(info_data, colWidths=[2 * inch, 3.5 * inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), Colors.DARK_BLUE),
            ('TEXTCOLOR', (1, 0), (1, -1), Colors.TEXT),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (0, -1), 15),
        ]))
        elements.append(info_table)
        
        # Confidentiality notice
        elements.append(Spacer(1, 1.5 * inch))
        elements.append(Paragraph(
            "CONFIDENTIAL",
            ParagraphStyle(
                'Confidential',
                parent=self.styles['Metadata'],
                fontName='Helvetica-Bold',
                fontSize=10,
                textColor=Colors.CRITICAL
            )
        ))
        elements.append(Paragraph(
            "This document contains sensitive security assessment information. "
            "Distribution should be limited to authorized personnel only.",
            ParagraphStyle(
                'ConfidentialNote',
                parent=self.styles['Metadata'],
                fontSize=8,
                textColor=Colors.GRAY
            )
        ))
        
        return elements
    
    # =========================================================================
    # SECTION 2: EXECUTIVE SUMMARY
    # =========================================================================
    
    def _build_executive_summary(self, data: Dict[str, Any]) -> List:
        """Build executive summary with score donut."""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=Colors.LIGHT_BLUE,
            spaceBefore=0,
            spaceAfter=15
        ))
        
        overall_score = get_attr(data, "overall_score", 0) or 0
        maturity_level = get_attr(data, "maturity_level", 1) or 1
        maturity_name = get_attr(data, "maturity_name", "Initial")
        findings = get_attr(data, "findings", []) or []
        
        # Create donut chart
        donut = create_score_donut(overall_score, 140)
        
        # Score interpretation
        if overall_score >= 80:
            score_interpretation = "Excellent - Organization demonstrates strong security readiness across most domains."
        elif overall_score >= 60:
            score_interpretation = "Good - Security fundamentals are in place with some areas for improvement."
        elif overall_score >= 40:
            score_interpretation = "Fair - Significant gaps exist that require attention to reduce risk exposure."
        elif overall_score >= 20:
            score_interpretation = "Poor - Critical security gaps present significant organizational risk."
        else:
            score_interpretation = "Critical - Immediate action required to address fundamental security deficiencies."
        
        # Count findings by severity
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for f in findings:
            sev = str(get_attr(f, "severity", "")).lower()
            for key in severity_counts:
                if key in sev:
                    severity_counts[key] += 1
                    break
        
        # Summary paragraph
        org_name = get_attr(data, "organization_name", "The organization")
        summary_text = (
            f"{org_name} achieved an overall security readiness score of "
            f"<b>{overall_score:.0f} out of 100</b>, placing them at "
            f"<b>Maturity Level {maturity_level} ({maturity_name})</b>. "
            f"{score_interpretation} "
            f"This assessment identified <b>{len(findings)} findings</b> across five security domains, "
            f"including {severity_counts['critical']} critical, {severity_counts['high']} high, "
            f"{severity_counts['medium']} medium, and {severity_counts['low']} low severity issues."
        )
        
        # Create side-by-side layout
        summary_para = Paragraph(summary_text, self.styles['ReportBodyText'])
        
        # Table with donut on left, text on right
        layout_data = [[donut, summary_para]]
        layout_table = Table(
            layout_data,
            colWidths=[160, self.page_width - 170]
        )
        layout_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('LEFTPADDING', (1, 0), (1, 0), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(layout_table)
        
        # Key metrics summary
        elements.append(Spacer(1, 15))
        
        metrics_data = [
            ["Metric", "Value", "Status"],
            ["Overall Score", f"{overall_score:.0f}/100", self._get_score_status(overall_score, 100)],
            ["Maturity Level", f"Level {maturity_level}", maturity_name],
            ["Total Findings", str(len(findings)), f"{severity_counts['critical'] + severity_counts['high']} require urgent attention"],
            ["Critical Issues", str(severity_counts['critical']), "Immediate action required" if severity_counts['critical'] > 0 else "None identified"],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2 * inch, 1.5 * inch, 2.8 * inch])
        metrics_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), Colors.DARK_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), Colors.WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            # Data rows
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), Colors.TEXT),
            # Layout
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, Colors.GRAY),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [Colors.WHITE, Colors.LIGHT_GRAY]),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(metrics_table)
        
        return elements
    
    def _get_score_status(self, score: float, max_score: float) -> str:
        """Get status label for a score."""
        pct = (score / max_score) * 100 if max_score > 0 else 0
        if pct >= 80:
            return "Excellent"
        elif pct >= 60:
            return "Good"
        elif pct >= 40:
            return "Fair"
        elif pct >= 20:
            return "Poor"
        return "Critical"
    
    # =========================================================================
    # SECTION 3: DOMAIN HEATMAP
    # =========================================================================
    
    def _build_domain_heatmap(self, data: Dict[str, Any]) -> List:
        """Build domain scores as heatmap table."""
        elements = []
        
        elements.append(Paragraph("Domain Score Analysis", self.styles['SectionHeader']))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=Colors.LIGHT_BLUE,
            spaceBefore=0,
            spaceAfter=15
        ))
        
        elements.append(Paragraph(
            "The following table presents scores across five security domains. "
            "Colors indicate performance level: green (strong), yellow (adequate), "
            "orange (needs improvement), red (critical gap).",
            self.styles['ReportBodyText']
        ))
        elements.append(Spacer(1, 10))
        
        scores = get_attr(data, "scores", []) or []
        
        if not scores:
            elements.append(Paragraph(
                "No domain scores available. Please compute scores first.",
                self.styles['ReportBodyText']
            ))
            return elements
        
        # Build heatmap table
        table_data = [["Domain", "Score", "Weight", "Contribution", "Status"]]
        row_colors = []
        
        for score in scores:
            domain_name = get_attr(score, "domain_name", "Unknown")
            score_val = get_attr(score, "score", 0) or 0
            weight = get_attr(score, "weight", 0) or 0
            
            # Calculate weighted contribution
            contribution = (score_val / 5.0) * weight
            
            # Status text
            if score_val >= 4:
                status = "Strong"
            elif score_val >= 3:
                status = "Adequate"
            elif score_val >= 2:
                status = "Needs Improvement"
            else:
                status = "Critical Gap"
            
            table_data.append([
                domain_name,
                f"{score_val:.1f} / 5.0",
                f"{weight}%",
                f"{contribution:.1f}",
                status
            ])
            row_colors.append(get_heatmap_color(score_val))
        
        table = Table(table_data, colWidths=[2.3 * inch, 1.1 * inch, 0.9 * inch, 1.1 * inch, 1.4 * inch])
        
        # Build style with heatmap colors
        style_commands = [
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), Colors.DARK_BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), Colors.WHITE),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, Colors.WHITE),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ]
        
        # Add heatmap background colors for each data row
        for i, color in enumerate(row_colors, start=1):
            style_commands.append(('BACKGROUND', (0, i), (-1, i), color))
        
        table.setStyle(TableStyle(style_commands))
        elements.append(table)
        
        # Domain descriptions
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Domain Descriptions", self.styles['SubsectionHeader']))
        
        for domain_id, domain_info in self.rubric["domains"].items():
            domain_name = domain_info.get("name", domain_id)
            description = domain_info.get("description", "")
            if description:
                elements.append(Paragraph(
                    f"<b>{domain_name}:</b> {description}",
                    self.styles['ReportBodyText']
                ))
        
        return elements
    
    # =========================================================================
    # SECTION 4: TOP FINDINGS
    # =========================================================================
    
    def _build_top_findings(self, data: Dict[str, Any]) -> List:
        """Build top findings section with severity badges."""
        elements = []
        
        elements.append(Paragraph("Key Findings", self.styles['SectionHeader']))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=Colors.LIGHT_BLUE,
            spaceBefore=0,
            spaceAfter=15
        ))
        
        findings = get_attr(data, "findings", []) or []
        
        if not findings:
            elements.append(Paragraph(
                "No findings identified in this assessment.",
                self.styles['ReportBodyText']
            ))
            return elements
        
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        
        def get_severity_rank(f):
            sev = str(get_attr(f, "severity", "info")).lower()
            for key, rank in severity_order.items():
                if key in sev:
                    return rank
            return 5
        
        sorted_findings = sorted(findings, key=get_severity_rank)
        
        # Show top 5 (or all if fewer)
        top_findings = sorted_findings[:5]
        
        elements.append(Paragraph(
            f"The following are the top {len(top_findings)} priority findings that require attention:",
            self.styles['ReportBodyText']
        ))
        elements.append(Spacer(1, 10))
        
        for i, finding in enumerate(top_findings, 1):
            elements.extend(self._build_finding_card(finding, i))
        
        # Additional findings summary if more than 5
        if len(findings) > 5:
            remaining = len(findings) - 5
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                f"<i>+ {remaining} additional finding{'s' if remaining > 1 else ''} "
                f"documented in the full assessment.</i>",
                self.styles['ReportSmallText']
            ))
        
        return elements
    
    def _build_finding_card(self, finding: Any, index: int) -> List:
        """Build a single finding card with severity badge."""
        elements = []
        
        severity = str(get_attr(finding, "severity", "medium")).upper()
        title = get_attr(finding, "title", "Untitled Finding")
        evidence = get_attr(finding, "evidence", "")
        recommendation = get_attr(finding, "recommendation", "")
        reference = get_attr(finding, "reference", "")
        domain = get_attr(finding, "domain_name", "")
        
        severity_color = get_severity_color(severity)
        
        # Create severity badge
        badge_style = ParagraphStyle(
            'SeverityBadge',
            fontName='Helvetica-Bold',
            fontSize=8,
            textColor=Colors.WHITE,
        )
        
        # Finding header with badge
        header_text = f"<b>{index}. {title}</b>"
        if domain:
            header_text += f" <font size='8' color='{Colors.GRAY}'>[{domain}]</font>"
        
        # Create table for badge + title
        badge_cell = Paragraph(
            f"<font color='white'>{severity.replace('SEVERITY.', '')}</font>",
            badge_style
        )
        title_cell = Paragraph(header_text, self.styles['FindingTitle'])
        
        header_data = [[badge_cell, title_cell]]
        header_table = Table(header_data, colWidths=[70, self.page_width - 80])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), severity_color),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (0, 0), 5),
            ('RIGHTPADDING', (0, 0), (0, 0), 5),
            ('TOPPADDING', (0, 0), (0, 0), 4),
            ('BOTTOMPADDING', (0, 0), (0, 0), 4),
            ('LEFTPADDING', (1, 0), (1, 0), 10),
        ]))
        elements.append(header_table)
        
        # Evidence
        if evidence:
            elements.append(Paragraph(
                f"<b>Evidence:</b> {evidence}",
                self.styles['FindingBody']
            ))
        
        # Recommendation
        if recommendation:
            # Truncate long recommendations
            rec_text = recommendation[:300] + "..." if len(recommendation) > 300 else recommendation
            elements.append(Paragraph(
                f"<b>Recommendation:</b> {rec_text}",
                self.styles['FindingBody']
            ))
        
        # Reference
        if reference:
            elements.append(Paragraph(
                f"<font color='{Colors.GRAY}'>Reference: {reference}</font>",
                self.styles['ReportSmallText']
            ))
        
        elements.append(Spacer(1, 8))
        
        return elements
    
    # =========================================================================
    # SECTION 5: 30/60/90 DAY ROADMAP
    # =========================================================================
    
    def _build_roadmap(self, data: Dict[str, Any]) -> List:
        """Build 30/60/90 day remediation roadmap."""
        elements = []
        
        elements.append(Paragraph("Remediation Roadmap", self.styles['SectionHeader']))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=Colors.LIGHT_BLUE,
            spaceBefore=0,
            spaceAfter=15
        ))
        
        elements.append(Paragraph(
            "The following roadmap prioritizes remediation activities based on severity, "
            "effort required, and business impact. Focus on critical and high-severity "
            "items first, then address medium and low findings.",
            self.styles['ReportBodyText']
        ))
        elements.append(Spacer(1, 15))
        
        findings = get_attr(data, "findings", []) or []
        
        # Categorize findings by remediation timeline
        day_30 = []  # Critical + low effort, High + low effort
        day_60 = []  # Critical + medium effort, High + medium effort, Medium + low effort
        day_90 = []  # Everything else
        
        for f in findings:
            sev = str(get_attr(f, "severity", "")).lower()
            effort = str(get_attr(f, "remediation_effort", "medium")).lower()
            title = get_attr(f, "title", "")
            
            if not title:
                continue
            
            is_critical = "critical" in sev
            is_high = "high" in sev
            is_medium = "medium" in sev
            is_low_effort = effort == "low"
            is_med_effort = effort == "medium"
            
            if is_critical and is_low_effort:
                day_30.append(f)
            elif is_critical and is_med_effort:
                day_60.append(f)
            elif is_high and is_low_effort:
                day_30.append(f)
            elif is_high and is_med_effort:
                day_60.append(f)
            elif is_medium and is_low_effort:
                day_60.append(f)
            else:
                day_90.append(f)
        
        # Build roadmap sections
        roadmap_sections = [
            ("30 Days - Immediate Actions", day_30, Colors.CRITICAL,
             "Address these critical and high-severity items with low implementation effort immediately."),
            ("60 Days - Short-term Improvements", day_60, Colors.MEDIUM,
             "Tackle these items requiring moderate effort to significantly reduce risk exposure."),
            ("90 Days - Strategic Initiatives", day_90, Colors.MEDIUM_BLUE,
             "Complete remaining remediation to achieve comprehensive security coverage."),
        ]
        
        for title, items, color, description in roadmap_sections:
            elements.extend(self._build_roadmap_section(title, items, color, description))
        
        return elements
    
    def _build_roadmap_section(self, title: str, items: List, color: colors.Color, description: str) -> List:
        """Build a single roadmap section."""
        elements = []
        
        # Section header with colored bar
        header_data = [[Paragraph(f"<b>{title}</b>", ParagraphStyle(
            'RoadmapHeader',
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=Colors.WHITE
        ))]]
        header_table = Table(header_data, colWidths=[self.page_width])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), color),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(header_table)
        
        elements.append(Paragraph(description, self.styles['ReportSmallText']))
        elements.append(Spacer(1, 5))
        
        if not items:
            elements.append(Paragraph(
                "✓ No items in this phase - excellent progress!",
                self.styles['RoadmapItem']
            ))
        else:
            for item in items[:7]:  # Limit to 7 per section
                item_title = get_attr(item, "title", "Unknown")
                sev = str(get_attr(item, "severity", "")).upper().replace("SEVERITY.", "")
                elements.append(Paragraph(
                    f"• [{sev}] {item_title}",
                    self.styles['RoadmapItem']
                ))
            
            if len(items) > 7:
                elements.append(Paragraph(
                    f"  ... and {len(items) - 7} more items",
                    self.styles['ReportSmallText']
                ))
        
        elements.append(Spacer(1, 15))
        return elements
    
    # =========================================================================
    # SECTION 6: APPENDIX - ANSWERS
    # =========================================================================
    
    def _build_appendix(self, data: Dict[str, Any]) -> List:
        """Build appendix with all assessment answers."""
        elements = []
        
        elements.append(Paragraph("Appendix: Assessment Responses", self.styles['SectionHeader']))
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=Colors.LIGHT_BLUE,
            spaceBefore=0,
            spaceAfter=15
        ))
        
        elements.append(Paragraph(
            "The following table documents all responses provided during the assessment. "
            "This serves as a record of the organization's self-reported security posture "
            "at the time of assessment.",
            self.styles['ReportBodyText']
        ))
        elements.append(Spacer(1, 10))
        
        answers = get_attr(data, "answers", []) or []
        
        if not answers:
            elements.append(Paragraph(
                "No answers recorded for this assessment.",
                self.styles['ReportBodyText']
            ))
            return elements
        
        # Group answers by domain
        domains = self.rubric.get("domains", {})
        
        for domain_id, domain_info in domains.items():
            domain_name = domain_info.get("name", domain_id)
            questions = domain_info.get("questions", [])
            
            # Find answers for this domain
            domain_answers = []
            for q in questions:
                q_id = q.get("id", "")
                # Find answer for this question
                answer_val = None
                for a in answers:
                    a_qid = get_attr(a, "question_id", "")
                    if a_qid == q_id:
                        answer_val = get_attr(a, "value", "")
                        break
                
                if answer_val is not None:
                    domain_answers.append({
                        "question": q.get("text", q_id),
                        "answer": self._format_answer(answer_val, q.get("type", "boolean"))
                    })
            
            if domain_answers:
                elements.append(Paragraph(domain_name, self.styles['SubsectionHeader']))
                
                table_data = [["Question", "Response"]]
                for da in domain_answers:
                    # Wrap long questions
                    q_text = da["question"]
                    if len(q_text) > 60:
                        q_text = Paragraph(q_text, self.styles['TableCell'])
                    table_data.append([q_text, da["answer"]])
                
                table = Table(table_data, colWidths=[4.5 * inch, 1.8 * inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), Colors.DARK_BLUE),
                    ('TEXTCOLOR', (0, 0), (-1, 0), Colors.WHITE),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('GRID', (0, 0), (-1, -1), 0.5, Colors.GRAY),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [Colors.WHITE, Colors.LIGHT_GRAY]),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 10))
        
        # Assessment metadata
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Assessment Metadata", self.styles['SubsectionHeader']))
        
        assessment_id = get_attr(data, "id", "N/A")
        created_at = get_attr(data, "created_at", "")
        completed_at = get_attr(data, "completed_at", "")
        
        if created_at and hasattr(created_at, 'strftime'):
            created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")
        if completed_at and hasattr(completed_at, 'strftime'):
            completed_at = completed_at.strftime("%Y-%m-%d %H:%M:%S")
        
        meta_data = [
            ["Assessment ID", str(assessment_id)],
            ["Created", str(created_at) if created_at else "N/A"],
            ["Completed", str(completed_at) if completed_at else "N/A"],
            ["Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ]
        
        meta_table = Table(meta_data, colWidths=[2 * inch, 4 * inch])
        meta_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, -1), Colors.GRAY),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(meta_table)
        
        return elements
    
    def _format_answer(self, value: Any, q_type: str) -> str:
        """Format answer value for display."""
        if value is None:
            return "—"
        
        str_val = str(value).lower()
        
        if q_type == "boolean":
            if str_val in ("true", "yes", "1"):
                return "✓ Yes"
            elif str_val in ("false", "no", "0"):
                return "✗ No"
        
        return str(value)
    
    def get_content_type(self) -> str:
        """Return PDF MIME type."""
        return "application/pdf"


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def generate_pdf_report(data: Dict[str, Any]) -> bytes:
    """
    Generate a professional PDF report from assessment data.
    
    Args:
        data: Assessment data dictionary
    
    Returns:
        PDF bytes
    """
    generator = ProfessionalPDFGenerator()
    return generator.generate(data)
