"""
Generate the Governance Architecture Whitepaper as a clean PDF.

Usage:
    python scripts/generate_whitepaper_pdf.py

Output:
    generated_reports/whitepaper_governance_architecture.pdf
"""

import os
import sys
from fpdf import FPDF

# ── Paths ────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT, "generated_reports")
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "whitepaper_governance_architecture.pdf")


class WhitepaperPDF(FPDF):
    """Custom PDF with header/footer for whitepaper formatting."""

    def __init__(self):
        super().__init__("P", "mm", "Letter")
        self.set_auto_page_break(auto=True, margin=25)
        # Register Arial TTF (Windows) for full Unicode support
        font_dir = "C:/Windows/Fonts"
        self.add_font("Arial", "", f"{font_dir}/arial.ttf")
        self.add_font("Arial", "B", f"{font_dir}/arialbd.ttf")
        self.add_font("Arial", "I", f"{font_dir}/ariali.ttf")
        self.add_font("Arial", "BI", f"{font_dir}/arialbi.ttf")

    def header(self):
        if self.page_no() == 1:
            return  # No header on cover page
        self.set_font("Arial", "I", 8)
        self.set_text_color(120, 120, 120)
        self.set_x(self.l_margin)
        self.cell(0, 8, "AIRS Platform -- Technical White Paper", align="L")
        self.cell(0, 8, f"Page {self.page_no() - 1}", align="R", new_x="LMARGIN", new_y="NEXT")
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_font("Arial", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, "\u00a9 2026 AIRS \u2014 AI Incident Readiness & Security Platform", align="C")

    def section_title(self, num, title):
        self.set_font("Arial", "B", 14)
        self.set_text_color(20, 60, 120)
        self.cell(0, 10, f"{num}. {title}", new_x="LMARGIN", new_y="NEXT")
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(4)

    def subsection_title(self, label, title):
        self.set_font("Arial", "B", 11)
        self.set_text_color(40, 40, 40)
        self.cell(0, 8, f"{label} {title}", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text):
        self.set_font("Arial", "", 10)
        self.set_text_color(30, 30, 30)
        self.set_x(self.l_margin)
        self.multi_cell(0, 5.5, text)
        self.ln(3)

    def bold_body(self, text):
        self.set_font("Arial", "B", 10)
        self.set_text_color(30, 30, 30)
        self.set_x(self.l_margin)
        self.multi_cell(0, 5.5, text)
        self.set_font("Arial", "", 10)

    def formula_block(self, formula):
        self.ln(2)
        self.set_font("Courier", "B", 10)
        self.set_fill_color(245, 245, 250)
        self.set_text_color(20, 20, 80)
        self.cell(0, 10, f"  {formula}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Arial", "", 10)
        self.set_text_color(30, 30, 30)
        self.ln(3)

    def table_row(self, cols, widths, bold=False, fill=False):
        self.set_font("Arial", "B" if bold else "", 9)
        if fill:
            self.set_fill_color(230, 235, 245)
        for i, col in enumerate(cols):
            self.cell(widths[i], 7, col, border=1, fill=fill, align="C" if i > 0 else "L")
        self.ln()

    def code_block(self, text):
        self.ln(1)
        self.set_font("Courier", "", 8)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(40, 40, 40)
        for line in text.strip().split("\n"):
            self.cell(0, 4.5, f"  {line}", fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Arial", "", 10)
        self.set_text_color(30, 30, 30)
        self.ln(3)

    def bullet(self, text, indent=10):
        self.set_x(self.l_margin + indent)
        self.set_font("Arial", "", 10)
        self.cell(4, 5.5, "\u2022")
        self.multi_cell(0, 5.5, text)
        self.set_x(self.l_margin)
        self.ln(1)


def build_cover_page(pdf: WhitepaperPDF):
    """Render the cover page."""
    pdf.add_page()

    pdf.ln(50)

    # Title
    pdf.set_font("Arial", "B", 22)
    pdf.set_text_color(20, 50, 100)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 11, "Deterministic Governance\nInference & Validation Architecture\nfor Continuous Compliance Intelligence", align="C")
    pdf.ln(10)

    # Subtitle line
    pdf.set_draw_color(20, 50, 100)
    pdf.line(60, pdf.get_y(), pdf.w - 60, pdf.get_y())
    pdf.ln(10)

    pdf.set_font("Arial", "", 14)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, "AIRS Platform \u2014 Technical White Paper", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, "Version 1.0  |  February 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)

    # Author
    pdf.set_font("Arial", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "Purvansh Bhatt", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Arial", "I", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "Security Engineering & AI Governance", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(30)

    # Footer badge
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, "AI Incident Readiness & Security (AIRS)", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "github.com/purvanshbhatt/AIRS", align="C", new_x="LMARGIN", new_y="NEXT")


def build_abstract(pdf: WhitepaperPDF):
    """Render the abstract section."""
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(20, 60, 120)
    pdf.cell(0, 10, "Abstract", new_x="LMARGIN", new_y="NEXT")
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)
    pdf.body_text(
        "Enterprise adoption of AI-assisted security tooling has exposed a fundamental tension: "
        "large language models excel at synthesizing human-readable narratives, but they cannot "
        "serve as the system of record for governance, risk, and compliance (GRC) decisions. "
        "This paper presents the architecture behind the AIRS platform's dual-engine design \u2014 "
        "an AI Narrative Engine for consultant-grade text and a Deterministic Governance Engine "
        "for auditable, reproducible compliance inference. We formalize the Governance Health "
        "Index (GHI), a weighted composite metric, and describe the Internal Governance "
        "Validation Framework (IGVF) that provides continuous regression assurance over "
        "governance logic without LLM dependency."
    )


def build_section_1(pdf: WhitepaperPDF):
    """Section 1: The Black Box Problem."""
    pdf.section_title(1, 'The "Black Box" Problem')

    pdf.body_text(
        "Modern AI security platforms increasingly rely on LLMs to generate risk assessments, "
        "maturity scores, and compliance recommendations. While the natural-language output "
        "appears authoritative, this approach introduces three structural failures that "
        "disqualify it from enterprise audit standards:"
    )

    pdf.bold_body("Non-determinism.")
    pdf.body_text(
        "Given identical inputs, an LLM may produce different severity classifications, score "
        "justifications, or framework mappings across successive invocations. Auditors require "
        "that the same organizational profile, finding set, and technology stack produce the "
        "exact same governance score every time. Stochastic outputs cannot satisfy SOC 2 "
        "Type II evidence requirements or ISO 27001 Annex A control traceability."
    )

    pdf.bold_body("Opacity of inference.")
    pdf.body_text(
        "When an LLM determines that an organization is \"HIPAA-applicable,\" the reasoning "
        "chain is embedded in transformer attention weights \u2014 not in an auditable rule set. "
        "An external assessor cannot inspect, version-control, or unit-test the decision "
        "boundary. This makes the compliance determination itself an unverifiable artifact."
    )

    pdf.bold_body("Score contamination risk.")
    pdf.body_text(
        "If the same model that generates narrative text also computes numeric scores, there "
        "is no architectural guarantee that a prompt injection, model update, or hallucination "
        "will not silently alter a maturity rating. The blast radius of a single model failure "
        "extends across the entire assessment output."
    )

    pdf.body_text(
        "These are not hypothetical concerns. They represent the gap between \"AI-assisted\" "
        "and \"audit-ready\" \u2014 a gap that the AIRS architecture is specifically designed to close."
    )


def build_section_2(pdf: WhitepaperPDF):
    """Section 2: Architecture -- Dual-Engine Separation."""
    pdf.section_title(2, "Architecture: Dual-Engine Separation")

    pdf.body_text(
        "AIRS enforces a strict separation of concerns between two independent processing "
        "paths. The AI Narrative Engine and the Deterministic Governance Engine operate in "
        "isolation with clearly defined boundaries:"
    )

    # Architecture diagram as code block
    pdf.code_block(
        "+-------------------------------------------------------------------+\n"
        "|                        AIRS Platform                              |\n"
        "|                                                                   |\n"
        "|  +---------------------+      +-----------------------------+    |\n"
        "|  | AI Narrative Engine |      | Deterministic Governance    |    |\n"
        "|  | (Google Gemini)     |      | Engine (Pure Python)        |    |\n"
        "|  |                     |      |                             |    |\n"
        "|  | + Executive summary |      | + Compliance inference      |    |\n"
        "|  | + 30/60/90 roadmap  |      | + Audit readiness score     |    |\n"
        "|  | x No score compute  |      | + SLA gap analysis          |    |\n"
        "|  | x No framework map  |      | + Lifecycle risk scoring    |    |\n"
        "|  | x No findings data  |      | + GHI composite index       |    |\n"
        "|  +---------------------+      +-----------------------------+    |\n"
        "|          |                                |                       |\n"
        "|   Narrative text only            Structured scores               |\n"
        "|          v                                v                       |\n"
        "|  +-------------------------------------------------------+      |\n"
        "|  |              Assessment Output                        |      |\n"
        "|  |  Deterministic scores + AI-generated narrative text   |      |\n"
        "|  +-------------------------------------------------------+      |\n"
        "+-------------------------------------------------------------------+"
    )

    pdf.subsection_title("2.1", "AI Narrative Engine")
    pdf.body_text(
        "The Narrative Engine wraps Google Gemini (via the google-genai SDK) and is scoped "
        "exclusively to text generation. It receives pre-computed assessment data \u2014 scores, "
        "findings, maturity levels \u2014 as a read-only input payload and produces two outputs: "
        "an executive summary paragraph and a 30/60/90-day remediation roadmap narrative. "
        "The LLM cannot modify numeric scores, maturity tiers, finding counts, severity "
        "classifications, or any structured data. If the LLM fails, the system falls back to "
        "deterministic template-based text with zero impact on governance scores."
    )

    pdf.subsection_title("2.2", "Deterministic Governance Engine")
    pdf.body_text(
        "The Governance Engine is implemented as a pure Python package (app.services.governance) "
        "with no LLM dependency. It contains four sub-engines:"
    )

    widths = [45, 50, 80]
    pdf.table_row(["Sub-Engine", "Module", "Function"], widths, bold=True, fill=True)
    pdf.table_row(["Compliance", "compliance_engine", "Rule-based framework mapping"], widths)
    pdf.table_row(["Audit Calendar", "audit_calendar", "Scheduling & forecasting"], widths)
    pdf.table_row(["Lifecycle", "lifecycle_engine", "Version lifecycle intelligence"], widths)
    pdf.table_row(["Tech Stack", "tech_stack", "Risk classification & detection"], widths)
    pdf.ln(3)

    pdf.body_text(
        "Every function in this package is deterministic: same inputs produce the same outputs "
        "and the same audit trail. The entire decision surface is unit-testable, "
        "version-controlled, and diff-auditable."
    )


def build_section_3(pdf: WhitepaperPDF):
    """Section 3: The GHI Formula."""
    pdf.section_title(3, "The Governance Health Index (GHI)")

    pdf.body_text(
        "The GHI is a composite governance posture metric that collapses four independent "
        "dimensions into a single 0\u2013100 score with a letter grade:"
    )

    pdf.formula_block("GHI = (Audit x 0.4) + (Lifecycle x 0.3) + (SLA x 0.2) + (Compliance x 0.1)")

    pdf.subsection_title("3.1", "Dimension Definitions")

    pdf.bold_body("Audit Readiness (weight: 0.4)")
    pdf.body_text(
        "Measures the severity burden of open findings. Starting from 100, deductions are "
        "applied per finding severity:"
    )
    pdf.formula_block("Audit = max(0, 100 - (Critical x 15) - (High x 8) - (Medium x 3))")
    pdf.body_text(
        "Low-severity findings carry zero deduction weight. Only open/in_progress findings "
        "are evaluated. This dimension receives the highest weight because unresolved critical "
        "findings represent the most immediate governance risk."
    )

    pdf.bold_body("Lifecycle Risk (weight: 0.3)")
    pdf.formula_block("Lifecycle = max(0, 100 - (EOL x 25) - (Deprecated x 15) - (Outdated x 5))")
    pdf.body_text(
        "A component is classified as outdated when it is 2+ major versions behind. "
        "Lifecycle status is resolved from a static, versioned lifecycle_config.json \u2014 "
        "no live API calls \u2014 ensuring reproducibility in air-gapped environments."
    )

    pdf.bold_body("SLA Gap (weight: 0.2)")
    widths = [55, 40, 25]
    pdf.table_row(["Condition", "Status", "Score"], widths, bold=True, fill=True)
    pdf.table_row(["Target meets tier requirement", "on_track", "100"], widths)
    pdf.table_row(["Gap <= 0.5%", "at_risk", "60"], widths)
    pdf.table_row(["Gap > 0.5%", "unrealistic", "20"], widths)
    pdf.table_row(["Not configured", "not_configured", "0"], widths)
    pdf.ln(3)

    pdf.bold_body("Compliance (weight: 0.1)")
    pdf.body_text(
        "Measures governance profile completeness. If the organization's attributes trigger "
        "applicable frameworks (e.g., processes_phi \u2192 HIPAA), score = 100. Configured but "
        "no frameworks = 50. Unconfigured = 0. This has the lowest weight because it measures "
        "awareness, not control implementation depth."
    )

    pdf.subsection_title("3.2", "Grade Mapping")
    widths = [30, 20, 75]
    pdf.table_row(["GHI Range", "Grade", "Interpretation"], widths, bold=True, fill=True)
    pdf.table_row(["90-100", "A", "Exceeds requirements"], widths)
    pdf.table_row(["80-89", "B", "Strong with minor gaps"], widths)
    pdf.table_row(["60-79", "C", "Acceptable, improvements needed"], widths)
    pdf.table_row(["40-59", "D", "Significant gaps, remediation needed"], widths)
    pdf.table_row(["0-39", "F", "Critical deficiencies"], widths)
    pdf.ln(3)

    pdf.body_text(
        "An organization passes IGVF validation only when it has zero critical issues "
        "AND a GHI >= 60."
    )


def build_section_4(pdf: WhitepaperPDF):
    """Section 4: Assurance -- IGVF."""
    pdf.section_title(4, "Assurance: Internal Governance Validation Framework")

    pdf.body_text(
        "Deterministic logic is only trustworthy if it is continuously verified. The IGVF "
        "is the platform's internal assurance layer \u2014 a staging-only subsystem that prevents "
        "governance logic regression."
    )

    pdf.subsection_title("4.1", "Architecture")
    pdf.body_text("The IGVF operates through three interfaces:")

    pdf.bullet(
        "Validation Engine (validation_engine.py) \u2014 The core computation module. It "
        "orchestrates all four dimension engines, computes the GHI, determines pass/fail "
        "status, and emits structured JSON log events traceable by organization_id with "
        "no PII exposure."
    )
    pdf.bullet(
        "Internal API Endpoint (/internal/governance/validate) \u2014 Returns HTTP 404 "
        "(not 403) when ENV != staging, making it invisible in production. Protected by "
        "admin token authentication separate from Firebase auth."
    )
    pdf.bullet(
        "CLI Tool (scripts/validate_governance.py) \u2014 Command-line interface with "
        "--org, --json, and --brief flags. Returns exit code 1 on any failure, enabling "
        "CI/CD pipeline integration."
    )

    pdf.subsection_title("4.2", "CI/CD Integration")
    pdf.body_text(
        "The GitHub Actions CI pipeline includes a dedicated governance-validation job "
        "that runs after the main test suite:"
    )

    pdf.code_block(
        "governance-validation:\n"
        "  needs: backend-tests\n"
        "  steps:\n"
        "    - run: pytest tests/test_igvf.py -v    # 79 unit tests\n"
        "    - run: python scripts/validate_governance.py --brief"
    )

    pdf.body_text(
        "Any regression in audit scoring, compliance rules, SLA thresholds, lifecycle "
        "classification, or GHI aggregation will fail the pipeline before code reaches "
        "staging. The 79-test suite covers boundary conditions and API-level behavior."
    )

    pdf.subsection_title("4.3", "Structured Audit Logging")
    pdf.body_text(
        "Each dimension computation emits a structured JSON log containing inputs, "
        "calculations, and output score \u2014 never PII. These logs enable post-hoc "
        "reconstruction of any governance score for SOC 2, ISO 27001, and FedRAMP "
        "continuous monitoring evidence."
    )

    pdf.code_block(
        '{\n'
        '  "event": "audit_readiness_inputs",\n'
        '  "organization_id": "org-12345",\n'
        '  "critical_count": 1,\n'
        '  "high_count": 2,\n'
        '  "deductions": {"critical": 15, "high": 16, "medium": 12},\n'
        '  "score": 57.0\n'
        '}'
    )


def build_section_5(pdf: WhitepaperPDF):
    """Section 5: Evidence-Based GRC."""
    pdf.section_title(5, "Evidence-Based GRC: From Self-Reporting to Verified Posture")

    pdf.body_text(
        "Traditional GRC workflows rely on self-reported questionnaires: an organization "
        "claims it encrypts data at rest, claims it patches within SLA, claims it has no "
        "end-of-life components. The AIRS architecture moves toward evidence-based governance "
        "through three verification tiers:"
    )

    widths = [30, 45, 50, 40]
    pdf.table_row(["Tier", "Source", "Verification", "Status"], widths, bold=True, fill=True)
    pdf.table_row(["1: Declared", "Self-reported attrs", "Awareness", "Implemented"], widths)
    pdf.table_row(["2: Observed", "Scanners, webhooks", "Evidence", "Partial"], widths)
    pdf.table_row(["3: SIEM", "SIEM/SOAR telemetry", "Assurance", "Roadmap"], widths)
    pdf.ln(3)

    pdf.body_text(
        "The GHI is architected to incorporate higher-fidelity evidence as integration depth "
        "increases. The compliance dimension weight (currently 0.1) is intentionally low "
        "because Tier 1 awareness provides limited assurance. As Tier 2 and Tier 3 data "
        "sources are connected, the model can be recalibrated without altering the composite "
        "formula structure \u2014 only the per-dimension scoring functions evolve."
    )

    pdf.body_text(
        "This progression mirrors FedRAMP's continuous monitoring maturity model: organizations "
        "begin with self-attestation, move to automated scanning evidence, and achieve "
        "continuous authorization through real-time telemetry. The AIRS platform provides the "
        "computational substrate for each stage."
    )


def build_conclusion(pdf: WhitepaperPDF):
    """Conclusion section."""
    pdf.section_title(6, "Conclusion")
    pdf.body_text(
        "The separation of AI narrative generation from deterministic governance computation "
        "is not an implementation detail \u2014 it is an architectural invariant that determines "
        "whether a platform's output can survive an external audit. By formalizing governance "
        "posture into the GHI, gating that logic with the IGVF's 79-test regression suite, "
        "and designing for progressive evidence integration, the AIRS platform delivers "
        "compliance intelligence that is reproducible, auditable, and extensible \u2014 properties "
        "that no LLM alone can guarantee."
    )

    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(20, 60, 120)
    pdf.cell(0, 8, "References", new_x="LMARGIN", new_y="NEXT")
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(3)

    refs = [
        "NIST SP 800-53 Rev. 5 \u2014 Security and Privacy Controls for Information Systems",
        "NIST AI RMF 1.0 \u2014 Artificial Intelligence Risk Management Framework",
        "ISO/IEC 27001:2022 \u2014 Information Security Management Systems",
        "FedRAMP Continuous Monitoring Strategy Guide",
        "SOC 2 Type II \u2014 Trust Services Criteria (AICPA)",
        "PCI DSS v4.0 \u2014 Payment Card Industry Data Security Standard",
    ]
    for ref in refs:
        pdf.bullet(ref, indent=5)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pdf = WhitepaperPDF()
    pdf.set_title("Deterministic Governance Inference & Validation Architecture")
    pdf.set_author("Purvansh Bhatt")
    pdf.set_subject("AIRS Platform - Governance Architecture White Paper")
    pdf.set_creator("AIRS Whitepaper Generator")

    build_cover_page(pdf)
    build_abstract(pdf)
    build_section_1(pdf)
    build_section_2(pdf)
    build_section_3(pdf)
    build_section_4(pdf)
    build_section_5(pdf)
    build_conclusion(pdf)

    pdf.output(OUTPUT_PATH)
    print(f"Whitepaper PDF generated: {OUTPUT_PATH}")
    print(f"Pages: {pdf.pages_count}")
    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"Size: {size_kb:.1f} KB")


if __name__ == "__main__":
    main()
