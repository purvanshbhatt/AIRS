"""
PDF Report generation service.
"""

from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from app.reports.base import BaseReport


class PDFReportGenerator(BaseReport):
    """Generate PDF assessment reports."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Add custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='Title2',
            parent=self.styles['Heading1'],
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=30
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2c3e50')
        ))
        self.styles.add(ParagraphStyle(
            name='FindingTitle',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            spaceBefore=10,
            spaceAfter=5
        ))
    
    def generate(self, data: Dict[str, Any]) -> bytes:
        """Generate PDF report from assessment data."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # Title page
        story.extend(self._build_title_page(data))
        story.append(PageBreak())
        
        # Executive summary
        story.extend(self._build_executive_summary(data))
        story.append(Spacer(1, 20))
        
        # Domain scores
        story.extend(self._build_domain_scores(data))
        story.append(Spacer(1, 20))
        
        # Findings
        story.extend(self._build_findings(data))
        
        # Recommendations
        story.extend(self._build_recommendations(data))
        
        doc.build(story)
        return buffer.getvalue()
    
    def _build_title_page(self, data: Dict[str, Any]) -> List:
        """Build title page elements."""
        elements = []
        
        elements.append(Spacer(1, 2 * inch))
        elements.append(Paragraph("AIRS", self.styles['Title2']))
        elements.append(Paragraph("AI Incident Readiness Score", self.styles['Title']))
        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph("Assessment Report", self.styles['Heading2']))
        elements.append(Spacer(1, inch))
        
        # Organization info
        org_name = data.get("organization_name", "Unknown Organization")
        elements.append(Paragraph(f"<b>Organization:</b> {org_name}", self.styles['Normal']))
        elements.append(Spacer(1, 10))
        
        assessment_title = data.get("title", "Security Readiness Assessment")
        elements.append(Paragraph(f"<b>Assessment:</b> {assessment_title}", self.styles['Normal']))
        elements.append(Spacer(1, 10))
        
        report_date = datetime.now().strftime("%B %d, %Y")
        elements.append(Paragraph(f"<b>Date:</b> {report_date}", self.styles['Normal']))
        elements.append(Spacer(1, 10))
        
        version = data.get("version", "1.0.0")
        elements.append(Paragraph(f"<b>Version:</b> {version}", self.styles['Normal']))
        
        return elements
    
    def _build_executive_summary(self, data: Dict[str, Any]) -> List:
        """Build executive summary section."""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        overall_score = data.get("overall_score", 0)
        maturity_level = data.get("maturity_level", 1)
        maturity_name = data.get("maturity_name", "Initial")
        
        # Score summary table
        score_data = [
            ["Overall Score", f"{overall_score:.1f} / 100"],
            ["Maturity Level", f"Level {maturity_level} - {maturity_name}"],
        ]
        
        score_table = Table(score_data, colWidths=[2.5 * inch, 3 * inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('PADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 20))
        
        # Maturity description
        maturity_desc = data.get("maturity_description", "")
        if maturity_desc:
            elements.append(Paragraph(
                f"<i>{maturity_desc}</i>",
                self.styles['Normal']
            ))
        
        # Finding summary
        findings = data.get("findings", [])
        high_count = 0
        for f in findings:
            if isinstance(f, dict):
                sev = f.get("severity", "")
            else:
                sev = str(getattr(f, 'severity', ''))
            if "high" in sev.lower():
                high_count += 1
        
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(
            f"<b>Total Findings:</b> {len(findings)} ({high_count} high severity)",
            self.styles['Normal']
        ))
        
        return elements
    
    def _build_domain_scores(self, data: Dict[str, Any]) -> List:
        """Build domain scores section."""
        elements = []
        
        elements.append(Paragraph("Domain Scores", self.styles['SectionHeader']))
        
        scores = data.get("scores", [])
        if not scores:
            elements.append(Paragraph("No scores available.", self.styles['Normal']))
            return elements
        
        def get_attr(obj, key, default=None):
            """Get attribute from dict or object."""
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)
        
        # Domain scores table
        table_data = [["Domain", "Score", "Weight", "Status"]]
        
        for score in scores:
            domain_name = get_attr(score, "domain_name", "Unknown")
            score_val = get_attr(score, "score", 0)
            weight = get_attr(score, "weight", 0)
            
            # Status based on score
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
                status
            ])
        
        table = Table(table_data, colWidths=[2.5 * inch, 1.2 * inch, 1 * inch, 1.5 * inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(table)
        
        return elements
    
    def _build_findings(self, data: Dict[str, Any]) -> List:
        """Build findings section."""
        elements = []
        
        elements.append(Paragraph("Findings", self.styles['SectionHeader']))
        
        findings = data.get("findings", [])
        if not findings:
            elements.append(Paragraph("No findings identified.", self.styles['Normal']))
            return elements
        
        def get_severity(f):
            """Get severity string from finding."""
            if isinstance(f, dict):
                return str(f.get("severity", "")).upper()
            return str(getattr(f, 'severity', '')).upper()
        
        # Group by severity
        severity_order = ["HIGH", "CRITICAL", "MEDIUM", "LOW"]
        
        for severity in severity_order:
            severity_findings = [
                f for f in findings 
                if severity.lower() in get_severity(f).lower()
            ]
            
            if not severity_findings:
                continue
            
            # Severity header
            severity_colors = {
                "CRITICAL": colors.HexColor('#8e44ad'),
                "HIGH": colors.HexColor('#e74c3c'),
                "MEDIUM": colors.HexColor('#f39c12'),
                "LOW": colors.HexColor('#3498db')
            }
            
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(
                f"<font color='{severity_colors.get(severity, colors.black)}'>"
                f"▶ {severity} SEVERITY ({len(severity_findings)})</font>",
                self.styles['FindingTitle']
            ))
            
            def get_attr(obj, key, default=None):
                if isinstance(obj, dict):
                    return obj.get(key, default)
                return getattr(obj, key, default)
            
            for finding in severity_findings:
                title = get_attr(finding, "title", "Unknown")
                evidence = get_attr(finding, "evidence")
                
                elements.append(Paragraph(f"• {title}", self.styles['Normal']))
                if evidence:
                    elements.append(Paragraph(
                        f"<i>Evidence: {evidence}</i>",
                        self.styles['Normal']
                    ))
        
        return elements
    
    def _build_recommendations(self, data: Dict[str, Any]) -> List:
        """Build recommendations section."""
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("Recommendations", self.styles['SectionHeader']))
        
        findings = data.get("findings", [])
        
        def get_attr(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)
        
        # Get unique recommendations
        recommendations = []
        for finding in findings:
            rec = get_attr(finding, "recommendation")
            if rec and rec not in recommendations:
                recommendations.append(rec)
        
        if not recommendations:
            elements.append(Paragraph(
                "No specific recommendations at this time.",
                self.styles['Normal']
            ))
            return elements
        
        # Priority recommendations
        elements.append(Paragraph(
            "Based on the assessment findings, the following actions are recommended:",
            self.styles['Normal']
        ))
        elements.append(Spacer(1, 10))
        
        for i, rec in enumerate(recommendations[:10], 1):  # Top 10
            elements.append(Paragraph(
                f"<b>{i}.</b> {rec}",
                self.styles['Normal']
            ))
            elements.append(Spacer(1, 5))
        
        return elements
    
    def get_content_type(self) -> str:
        """Return PDF MIME type."""
        return "application/pdf"
