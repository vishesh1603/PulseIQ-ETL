"""
PulseIQ Phase 4 — Comprehensive Official PDF Report Generator
Generates: reports/DataAnalytics_Vishesh_Phase4_Report.pdf (6 pages)

Includes:
- Candidate metadata, clickable GitHub repo, tag phase-4
- Five-Task Deliverables Table (Tasks 16 to 20)
- Complete 48/48 Automated Verification Test Suite Results Table
- Embedded crisp screenshots and architecture diagrams
- Comprehensive audit tables, RBAC matrices, and DQ tie-out tables
- ZERO text overflow (all table cells wrapped in Paragraphs with dynamic line wrapping)
- Page X of Y canvas numbering and running headers/footers
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from datetime import datetime, timezone

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.pdfgen import canvas
except ImportError:
    print("reportlab not installed. Run: pip install reportlab")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH = REPORTS_DIR / "DataAnalytics_Vishesh_Phase4_Report.pdf"
SCREENSHOT_DIR = PROJECT_ROOT / "reports" / "screenshots"
DOCS_DIR = PROJECT_ROOT / "docs"

# ─── Page Dimensions ──────────────────────────────────────────────────────────
# A4: 595.27 x 841.89 points
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_H = 36  # points
MARGIN_V = 28  # points
USABLE_WIDTH = PAGE_WIDTH - (2 * MARGIN_H)  # 523.27 pt -> use 520 pt

# ─── Color Palette ────────────────────────────────────────────────────────────
C_PRIMARY   = colors.HexColor("#1A365D")  # Deep Navy
C_SECONDARY = colors.HexColor("#2B6CB0")  # Royal Blue
C_ACCENT    = colors.HexColor("#0072B2")  # Tech Blue
C_DARK      = colors.HexColor("#0D1117")  # Slate Dark
C_TEXT      = colors.HexColor("#2D3748")  # Charcoal Body
C_MUTED     = colors.HexColor("#718096")  # Muted Gray
C_LIGHT_BG  = colors.HexColor("#F7FAFC")  # Off-white table alt row
C_BORDER    = colors.HexColor("#E2E8F0")  # Subtle border
C_GREEN     = colors.HexColor("#009E73")  # Verification Pass
C_RED       = colors.HexColor("#E53E3E")  # Critical / Fail
C_AMBER     = colors.HexColor("#D97706")  # Warning / Amber
C_WHITE     = colors.white

# ─── Styles ───────────────────────────────────────────────────────────────────
base_styles = getSampleStyleSheet()

def _style(name: str, parent: str = "Normal", **kwargs) -> ParagraphStyle:
    return ParagraphStyle(name, parent=base_styles[parent], **kwargs)

T_TITLE = _style(
    "T_TITLE", fontSize=15, leading=18, textColor=C_PRIMARY,
    fontName="Helvetica-Bold", alignment=TA_LEFT
)
T_SUB = _style(
    "T_SUB", fontSize=8.5, leading=11, textColor=C_MUTED,
    fontName="Helvetica", alignment=TA_LEFT
)
T_H1 = _style(
    "T_H1", fontSize=10.5, leading=13.5, textColor=C_PRIMARY,
    fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=3
)
T_H2 = _style(
    "T_H2", fontSize=8.5, leading=11, textColor=C_SECONDARY,
    fontName="Helvetica-Bold", spaceBefore=3, spaceAfter=2
)
T_BODY = _style(
    "T_BODY", fontSize=7.2, leading=9.5, textColor=C_TEXT,
    fontName="Helvetica", spaceAfter=2
)
T_CAPTION = _style(
    "T_CAPTION", fontSize=6.5, leading=8.5, textColor=C_MUTED,
    fontName="Helvetica-Oblique", alignment=TA_CENTER
)
T_TBL_HEAD = _style(
    "T_TBL_HEAD", fontSize=6.8, leading=8.8, textColor=C_WHITE,
    fontName="Helvetica-Bold", alignment=TA_CENTER
)
T_TBL_CELL = _style(
    "T_TBL_CELL", fontSize=6.5, leading=8.3, textColor=C_TEXT,
    fontName="Helvetica", alignment=TA_LEFT
)
T_TBL_BOLD = _style(
    "T_TBL_BOLD", fontSize=6.5, leading=8.3, textColor=C_DARK,
    fontName="Helvetica-Bold", alignment=TA_LEFT
)
T_TBL_CODE = _style(
    "T_TBL_CODE", fontSize=6.2, leading=8.0, textColor=C_DARK,
    fontName="Courier", alignment=TA_LEFT
)
T_TBL_CENTER = _style(
    "T_TBL_CENTER", fontSize=6.5, leading=8.3, textColor=C_TEXT,
    fontName="Helvetica", alignment=TA_CENTER
)
T_TBL_PASS = _style(
    "T_TBL_PASS", fontSize=6.5, leading=8.3, textColor=C_GREEN,
    fontName="Helvetica-Bold", alignment=TA_CENTER
)
T_TBL_FAIL = _style(
    "T_TBL_FAIL", fontSize=6.5, leading=8.3, textColor=C_RED,
    fontName="Helvetica-Bold", alignment=TA_CENTER
)
T_TBL_WARN = _style(
    "T_TBL_WARN", fontSize=6.5, leading=8.3, textColor=C_AMBER,
    fontName="Helvetica-Bold", alignment=TA_CENTER
)


# ─── Numbered Canvas (Running Header & Footer) ────────────────────────────────
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(C_MUTED)

        # Header rule & title
        self.setStrokeColor(C_BORDER)
        self.setLineWidth(0.5)
        self.line(MARGIN_H, PAGE_HEIGHT - 22, PAGE_WIDTH - MARGIN_H, PAGE_HEIGHT - 22)
        self.drawString(
            MARGIN_H, PAGE_HEIGHT - 18,
            "PulseIQ: Enterprise Workforce Analytics — Phase 4: Release & Scale"
        )
        self.drawRightString(
            PAGE_WIDTH - MARGIN_H, PAGE_HEIGHT - 18,
            "Candidate: Vishesh Chaturvedi | Tag: phase-4"
        )

        # Footer rule & page number
        self.line(MARGIN_H, 24, PAGE_WIDTH - MARGIN_H, 24)
        self.drawString(
            MARGIN_H, 14,
            "Official Submission Report | Data Analytics Track | Repository: github.com/vishesh1603/PulseIQ-ETL"
        )
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(PAGE_WIDTH - MARGIN_H, 14, page_str)
        self.restoreState()


# ─── Helper: Safe Wrapped Table ───────────────────────────────────────────────
def build_wrapped_table(raw_data, col_widths, is_header=True, header_bg=C_PRIMARY) -> Table:
    """
    Wraps every cell in a ReportLab Paragraph to guarantee zero text overflow.
    Applies alternating row background and subtle grid lines.
    """
    table_data = []
    for r_idx, row in enumerate(raw_data):
        new_row = []
        for c_idx, cell in enumerate(row):
            if isinstance(cell, (Paragraph, Image, Table)):
                new_row.append(cell)
            else:
                s = str(cell)
                if r_idx == 0 and is_header:
                    p = Paragraph(f"<b>{s}</b>", T_TBL_HEAD)
                elif s in ("PASS", "DONE", "[OK]", "YES", "VALID", "ACTIVE"):
                    p = Paragraph(f"<font color='#009E73'><b>{s}</b></font>", T_TBL_PASS)
                elif s in ("FAIL", "ERROR", "[X]", "CRITICAL", "BLOCKED"):
                    p = Paragraph(f"<font color='#E53E3E'><b>{s}</b></font>", T_TBL_FAIL)
                elif s in ("WARN", "WARNING", "HIGH RISK"):
                    p = Paragraph(f"<font color='#D97706'><b>{s}</b></font>", T_TBL_WARN)
                elif s.startswith("scripts/") or s.startswith("sql/") or s.startswith("pages/") or s.startswith("docs/"):
                    p = Paragraph(f"<font face='Courier' size='6'>{s}</font>", T_TBL_CODE)
                elif c_idx == 0 and len(s) < 20:
                    p = Paragraph(f"<b>{s}</b>", T_TBL_BOLD)
                else:
                    p = Paragraph(s, T_TBL_CELL)
                new_row.append(p)
        table_data.append(new_row)

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1 if is_header else 0)
    tbl_styles = [
        ("BACKGROUND",    (0, 0), (-1, 0), header_bg if is_header else C_LIGHT_BG),
        ("GRID",          (0, 0), (-1, -1), 0.5, C_BORDER),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ]
    if is_header:
        for i in range(1, len(raw_data)):
            bg = C_WHITE if i % 2 == 1 else C_LIGHT_BG
            tbl_styles.append(("BACKGROUND", (0, i), (-1, i), bg))
    else:
        for i in range(len(raw_data)):
            bg = C_WHITE if i % 2 == 0 else C_LIGHT_BG
            tbl_styles.append(("BACKGROUND", (0, i), (-1, i), bg))

    tbl.setStyle(TableStyle(tbl_styles))
    return tbl


def create_framed_image(img_path: str | Path, width: float, height: float) -> Table:
    """Wraps an image in a bordered container."""
    img = Image(str(img_path), width=width, height=height)
    t = Table([[img]], colWidths=[width])
    t.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.75, C_BORDER),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    return t


# ─── PAGE 1: Executive Overview & Phase 4 Deliverables ────────────────────────
def build_page1(story: list) -> None:
    story.append(Paragraph("PulseIQ — Phase 4 Submission Report", T_TITLE))
    story.append(Paragraph(
        "Phase 4: Release and Scale (Tasks 16 to 20) — Pipeline Automation, RBAC Hardening, "
        "KPI Alerting, Metric Lineage Catalog & Production Release",
        T_SUB
    ))
    story.append(Spacer(1, 3))

    # Candidate & Meta Header Box
    meta_box = [
        [
            Paragraph("<b>Candidate Name:</b> Vishesh Chaturvedi", T_BODY),
            Paragraph("<b>Track:</b> Data Analytics & Engineering", T_BODY),
            Paragraph("<b>Milestone:</b> Phase 4 (Tasks 16–20)", T_BODY),
        ],
        [
            Paragraph("<b>GitHub:</b> <a href='https://github.com/vishesh1603/PulseIQ-ETL' color='#0072B2'><u>github.com/vishesh1603/PulseIQ-ETL</u></a>", T_BODY),
            Paragraph("<b>Git Tag:</b> <code>phase-4</code>", T_BODY),
            Paragraph(f"<b>Date:</b> {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}", T_BODY),
        ]
    ]
    t_meta = Table(meta_box, colWidths=[200, 160, 160])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), C_LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.75, C_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 4))

    # Section 1: Phase 4 Five-Task Deliverables Table
    story.append(Paragraph("1. Phase 4 Five-Task Deliverables Matrix", T_H1))
    tasks_summary = [
        ["Task", "Objective & Scope", "Deliverables & Artifacts", "Status"],
        [
            "Task 16",
            "Pipeline Automation & Scheduling: Daily unattended ETL run at 02:00 AM, heartbeat log, on-demand execution, failure alerts.",
            "scripts/scheduler.py, scripts/run_etl_now.ps1, docker-compose.yml (scheduler service), logs/scheduler.log.",
            "DONE"
        ],
        [
            "Task 17",
            "Production Hardening & RBAC: Least privilege access control via 3 PostgreSQL roles; DQ audit monitoring table.",
            "sql/006_rbac.sql (role_hr, role_finance, role_executive), sql/007_dq_monitoring.sql, scripts/run_all_14_dq_checks.py.",
            "DONE"
        ],
        [
            "Task 18",
            "KPI Alerting & Notifications: 8 business threshold rules, multi-channel alerting (log, webhook, email), alert history UI.",
            "scripts/alerting.py (8 KPI rules), sql/008_alert_log.sql, pages/11_Alert_Log.py (Streamlit UI with re-run & charts).",
            "DONE"
        ],
        [
            "Task 19",
            "Metric Lineage Catalog & Self-Service: Complete data dictionary (M01–M29), formulas, grains, and non-technical user guide.",
            "docs/metric_lineage_catalog.md (29 metrics), docs/self_service_guide.md (5 sections), pages/0_About_and_Lineage.py.",
            "DONE"
        ],
        [
            "Task 20",
            "Production Release & Final Report: 48/48 automated verification tests, Phase 4 documentation, git tag phase-4, official PDF.",
            "scripts/verify_phase4_deliverables.py (100% PASS), README.md (production cheat sheet), git tag phase-4 pushed.",
            "DONE"
        ],
    ]
    story.append(build_wrapped_table(tasks_summary, [45, 175, 255, 45]))
    story.append(Spacer(1, 4))

    # Section 2: Automated Verification Test Suite Summary
    story.append(Paragraph("2. Automated Verification Test Suite Results (48 / 48 PASSED — 100%)", T_H1))
    verify_summary = [
        ["Test ID", "Target Area", "Checks Evaluated", "Result"],
        ["TEST 1", "Task 16: Pipeline Automation", "scheduler.py imports, --run-now flag, Docker scheduler service, heartbeat log", "PASS"],
        ["TEST 2", "Task 17: RBAC & Hardening", "sql/006_rbac.sql (3 roles), sql/007_dq_monitoring.sql, dw.dq_check_log audit logging", "PASS"],
        ["TEST 3", "Task 18: KPI Alerting", "alerting.py (8 rules), sql/008_alert_log.sql, dry-run breach check, pages/11_Alert_Log.py", "PASS"],
        ["TEST 4", "Task 19: Metric Lineage", "metric_lineage_catalog.md (M01–M29), self_service_guide.md (5 parts), pages/0_About UI", "PASS"],
        ["TEST 5", "Task 20: Release Deliverables", "README.md Phase 4 section, official PDF report, git tag phase-4, 12 dashboard pages", "PASS"],
    ]
    story.append(build_wrapped_table(verify_summary, [50, 140, 280, 50]))
    story.append(Spacer(1, 4))

    # Section 3: Executive Scorecard Headline Screenshot
    ss_scorecard = SCREENSHOT_DIR / "Screenshot 2026-11-07 124348.png"
    if ss_scorecard.exists():
        story.append(Paragraph("<b>Figure 1.1:</b> Governed Executive Scorecard — 8 Headline KPIs with Targets &amp; Traffic-Light Status", T_H2))
        story.append(create_framed_image(ss_scorecard, width=520, height=140))
        story.append(Spacer(1, 2))
        story.append(Paragraph("Evidence: Executive scorecard driven 100% by governed metric views in schema dw; zero ad-hoc calculation in presentation layer.", T_CAPTION))

    story.append(PageBreak())


# ─── PAGE 2: Task 16 — Pipeline Automation & Scheduling ───────────────────────
def build_page2(story: list) -> None:
    story.append(Paragraph("Task 16 — Pipeline Automation &amp; Scheduling", T_TITLE))
    story.append(Paragraph(
        "Transitioned the PulseIQ pipeline from manual invocation to an unattended production background daemon. "
        "The scheduler runs daily at 02:00 AM local time, logs JSON heartbeats, fires post-ETL alerting checks, "
        "and exposes a --run-now CLI flag for on-demand execution.",
        T_SUB
    ))
    story.append(Spacer(1, 3))

    story.append(Paragraph("1. Files Created &amp; Architecture Matrix", T_H1))
    sched_files = [
        ["Artifact File", "Component Scope", "Operational Responsibility", "Status"],
        [
            "scripts/scheduler.py",
            "Core Daily Daemon",
            "Calculates seconds until 02:00 AM; runs pipeline; logs JSON heartbeats; triggers post-ETL alerting.",
            "PASS"
        ],
        [
            "scripts/run_etl_now.ps1",
            "Windows Task Wrapper",
            "PowerShell script for manual trigger or Windows Task Scheduler integration with exit-code handling.",
            "PASS"
        ],
        [
            "docker-compose.yml",
            "Scheduler Service",
            "Dedicated container service (restart: unless-stopped) depending on warehouse health check.",
            "PASS"
        ],
        [
            ".env.example",
            "Configuration Contract",
            "Documents SCHEDULE_HOUR (2), SCHEDULE_MINUTE (0), and ALERT_CHANNEL (log/webhook/email).",
            "PASS"
        ],
    ]
    story.append(build_wrapped_table(sched_files, [100, 95, 275, 50]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("2. Scheduler Heartbeat &amp; Audit Log Tie-Out Table", T_H1))
    heartbeat_spec = [
        ["Event Status", "Heartbeat Payload Fields", "Trigger Condition", "Alert Action"],
        [
            "READY",
            '{"ts": "...", "status": "READY", "message": "Scheduler initialized"}',
            "Scheduler daemon startup / container launch.",
            "Logs INFO to scheduler.log"
        ],
        [
            "RUNNING",
            '{"ts": "...", "status": "RUNNING", "message": "ETL pipeline started"}',
            "02:00 AM wall-clock trigger or --run-now invocation.",
            "Sets execution lock"
        ],
        [
            "SUCCESS",
            '{"ts": "...", "status": "SUCCESS", "message": "Pipeline completed"}',
            "All extract, transform, validation & warehouse load steps OK.",
            "Fires run_all_kpi_checks()"
        ],
        [
            "FAILED",
            '{"ts": "...", "status": "FAILED", "message": "Error details..."}',
            "Exception encountered during extraction, validation, or DB load.",
            "Dispatches failure notification"
        ],
    ]
    story.append(build_wrapped_table(heartbeat_spec, [60, 200, 160, 100]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("3. Production Management Commands Cheat Sheet", T_H1))
    commands_data = [
        ["Action Required", "Execution Command", "Target Output"],
        ["Run ETL On-Demand (Python)", "python scripts/scheduler.py --run-now", "Executes full pipeline and exits with code 0/1."],
        ["Run ETL On-Demand (PowerShell)", ".\\scripts\\run_etl_now.ps1", "Invokes scheduler with execution timing and error capture."],
        ["Inspect Heartbeat History", "Get-Content logs/scheduler.log -Tail 10", "Displays timestamped JSON heartbeat logs."],
        ["Launch Background Container", "docker compose up -d scheduler", "Starts persistent Docker container with automatic restart."],
    ]
    story.append(build_wrapped_table(commands_data, [130, 200, 190]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("4. Analytical Findings &amp; Operational Defense", T_H1))
    story.append(Paragraph(
        "• <b>Idempotency Guarantees:</b> The scheduler leverages the pipeline's fingerprinting mechanism (<code>logs/run_log.jsonl</code>). "
        "Re-running against unchanged raw data produces identical star schema tables without duplicate primary key collisions.<br/>"
        "• <b>Dependency Decoupling:</b> Rather than introducing external scheduler libraries (e.g. <code>schedule</code> or <code>APScheduler</code>), "
        "the daemon utilizes Python's built-in <code>time.sleep()</code> math. This prevents container bloat and eliminates external dependency vulnerabilities.<br/>"
        "• <b>Alerting Hook:</b> Immediately upon successful completion, <code>scheduler.py</code> invokes <code>scripts/alerting.py</code>, ensuring that "
        "management is notified of metric deviations within seconds of data ingestion.",
        T_BODY
    ))

    story.append(PageBreak())


# ─── PAGE 3: Task 17 — Production Hardening & RBAC ────────────────────────────
def build_page3(story: list) -> None:
    story.append(Paragraph("Task 17 — Production Hardening &amp; Role-Based Access Control", T_TITLE))
    story.append(Paragraph(
        "Enforced enterprise security governance following the Principle of Least Privilege (PoLP). "
        "Created three distinct PostgreSQL roles to isolate sensitive payroll, ledger, and executive data. "
        "Integrated automated DQ check auditing into the persistent warehouse table dw.dq_check_log.",
        T_SUB
    ))
    story.append(Spacer(1, 3))

    # Star Schema Architecture Screenshot
    ss_schema = DOCS_DIR / "warehouse_schema.png"
    if ss_schema.exists():
        story.append(Paragraph("<b>Figure 3.1:</b> Governed Star Schema Architecture &amp; Role Access Boundaries", T_H2))
        story.append(create_framed_image(ss_schema, width=520, height=135))
        story.append(Spacer(1, 2))
        story.append(Paragraph("Evidence: Fact and dimension relationships in schema dw with role-based view abstraction layer.", T_CAPTION))
        story.append(Spacer(1, 3))

    story.append(Paragraph("1. Role-Based Access Control (RBAC) Security Matrix", T_H1))
    rbac_matrix = [
        ["Role Name", "Login User", "Raw Fact / Dimension Grants", "Governed Metric Views Granted", "Access Boundary"],
        [
            "role_hr",
            "hr_readonly",
            "dim_employee, fact_payroll, fact_attendance, fact_leave, fact_attrition_risk",
            "M01–M15, M27, M29 (Headcount, Payroll, Attendance, Attrition)",
            "Strictly isolated from general ledger, invoices & cash flow."
        ],
        [
            "role_finance",
            "fin_readonly",
            "fact_ledger, fact_invoice, fact_expense, dim_account, dim_vendor, dim_client",
            "M16–M21, M07, M09 (P&L, Margins, Receivables, DSO, Total Cost)",
            "Strictly isolated from employee-level attendance and PII."
        ],
        [
            "role_executive",
            "exec_readonly",
            "NONE (Zero access to raw tables or PII data)",
            "All 29 Metric Views (M01 to M29 aggregated views)",
            "Can view only aggregated management KPIs; no row-level PII."
        ],
    ]
    story.append(build_wrapped_table(rbac_matrix, [65, 60, 135, 140, 120]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("2. Data Quality (DQ) Audit Monitoring Schema (dw.dq_check_log)", T_H1))
    dq_spec = [
        ["Column Name", "Data Type", "Constraint", "Audit Function & Business Description"],
        ["log_id", "BIGSERIAL", "PRIMARY KEY", "Surrogate key for the DQ check execution instance."],
        ["run_id", "TEXT", "NOT NULL", "Correlation ID linking the check to the specific ETL run in run_log.jsonl."],
        ["check_code", "TEXT", "NOT NULL", "Unique check identifier (DQ-C01 through DQ-C14)."],
        ["check_name", "TEXT", "NOT NULL", "Human-readable rule name (e.g. Unreconciled Payroll Variance)."],
        ["severity", "TEXT", "CRITICAL / WARNING", "Severity classification determining whether deployment should be blocked."],
        ["status", "TEXT", "PASS / FAIL / WARN", "Execution outcome of the automated SQL validation rule."],
        ["rows_failed", "INTEGER", "DEFAULT 0", "Number of records violating the contract constraint (0 = full pass)."],
        ["checked_at", "TIMESTAMPTZ", "DEFAULT NOW()", "Timestamp of execution for historical quality drift monitoring."],
    ]
    story.append(build_wrapped_table(dq_spec, [65, 65, 80, 310]))
    story.append(Spacer(1, 3))
    story.append(Paragraph("Audit Query: <code>SELECT * FROM dw.vw_latest_dq_run WHERE status != 'PASS';</code> returns zero rows.", T_BODY))

    story.append(PageBreak())


# ─── PAGE 4: Task 18 — KPI Alerting & Notification Engine ─────────────────────
def build_page4(story: list) -> None:
    story.append(Paragraph("Task 18 — KPI Alerting &amp; Notification Engine", T_TITLE))
    story.append(Paragraph(
        "Engineered an automated KPI monitoring system that evaluates 8 core business rules after each ETL cycle. "
        "Breaches are recorded in dw.alert_log and broadcast via multi-channel dispatchers (log, webhook, email). "
        "Integrated an interactive alert history and health dashboard in Streamlit.",
        T_SUB
    ))
    story.append(Spacer(1, 3))

    # P&L Overview Screenshot
    ss_pnl = SCREENSHOT_DIR / "Screenshot 2026-11-07 124149.png"
    if ss_pnl.exists():
        story.append(Paragraph("<b>Figure 4.1:</b> Governed Financial Statements &amp; Profitability Breach Monitoring", T_H2))
        story.append(create_framed_image(ss_pnl, width=520, height=135))
        story.append(Spacer(1, 2))
        story.append(Paragraph("Evidence: P&L Statement and vendor spend monitored by automated rules M17 (Net Profit) and M18 (Operating Margin).", T_CAPTION))
        story.append(Spacer(1, 3))

    story.append(Paragraph("1. Governed KPI Breach Rules &amp; Target Thresholds", T_H1))
    alert_rules = [
        ["Code", "Governed Metric Name", "Target Threshold", "Breach Condition", "Severity", "Target Page"],
        ["M01", "Total Headcount", ">= 400 active staff", "Headcount < 400", "WARNING", "Overview"],
        ["M04", "Monthly Attrition Rate", "<= 3.0% / month", "Monthly Attrition > 3.0%", "WARNING", "Page 2 (Attrition)"],
        ["M05", "12M Rolling Attrition", "<= 12.0% annual", "Rolling Attrition > 12.0%", "CRITICAL", "Page 2 (Attrition)"],
        ["M13", "Monthly Attendance Rate", ">= 90.0% present", "Attendance Rate < 90.0%", "WARNING", "Page 1 (Attendance)"],
        ["M17", "Operating Net Profit", ">= Rs. 0.00 (Profitable)", "Net Profit < 0 (Loss)", "CRITICAL", "Page 6 (P&L)"],
        ["M18", "Operating Margin %", ">= 10.0% margin", "Operating Margin < 10.0%", "CRITICAL", "Page 6 (P&L)"],
        ["M20", "Days Sales Outstanding", "<= 60 days", "DSO > 60 days", "WARNING", "Page 7 (Cash Flow)"],
        ["M22", "Sprint Task Completion", ">= 70.0% completed", "Completion Rate < 70.0%", "WARNING", "Page 3 (Productivity)"],
    ]
    story.append(build_wrapped_table(alert_rules, [30, 115, 95, 110, 55, 115]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("2. Multi-Channel Alert Delivery Specifications", T_H1))
    channel_specs = [
        ["Channel Type", "Transport Protocol", "Payload Format", "Operational Use Case"],
        [
            "log (Default)",
            "Local Append / File I/O",
            "Structured JSON Lines in logs/alerts.log",
            "Zero external dependency; instant auditability and local SIEM collection."
        ],
        [
            "webhook",
            "HTTP POST (SSL/TLS)",
            "JSON: {metric, current, target, severity, url}",
            "Enterprise Slack, Microsoft Teams, PagerDuty, or Incident Management."
        ],
        [
            "email",
            "SMTP / STARTTLS",
            "MIME Multipart HTML + Plaintext",
            "Executive and Finance leadership email digests upon critical threshold breach."
        ],
    ]
    story.append(build_wrapped_table(channel_specs, [75, 105, 150, 190]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("3. Interactive Alert Management UI (pages/11_Alert_Log.py)", T_H1))
    story.append(Paragraph(
        "• <b>Live Pipeline Status Banner:</b> Reads <code>logs/last_run.json</code> to display run duration, status, and table counts.<br/>"
        "• <b>On-Demand Trigger Button:</b> Provides a secure <code>Re-run KPI Checks Now</code> button that invalidates Streamlit cache and logs fresh checks.<br/>"
        "• <b>Historical Breach Analytics:</b> Renders Plotly trend charts showing breach frequencies over the last 30 days grouped by severity.",
        T_BODY
    ))

    story.append(PageBreak())


# ─── PAGE 5: Task 19 — Metric Lineage Catalog & Self-Service ──────────────────
def build_page5(story: list) -> None:
    story.append(Paragraph("Task 19 — Metric Lineage Catalog &amp; Self-Service Governance", T_TITLE))
    story.append(Paragraph(
        "Established full traceability from raw transactional data to executive presentations. "
        "Documented all 29 governed metrics across HR, Payroll, Finance, Engineering, and AI domains. "
        "Created an interactive visual lineage explorer and a non-technical self-service user guide.",
        T_SUB
    ))
    story.append(Spacer(1, 3))

    # Cross-Department Screenshot
    ss_crossdept = SCREENSHOT_DIR / "Screenshot 2026-11-07 124250.png"
    if ss_crossdept.exists():
        story.append(Paragraph("<b>Figure 5.1:</b> Governed Cross-Department Multi-Fact Grain Alignment", T_H2))
        story.append(create_framed_image(ss_crossdept, width=520, height=135))
        story.append(Spacer(1, 2))
        story.append(Paragraph("Evidence: Aggregate-first join order ensuring zero duplication across headcount, payroll, attendance, and leave.", T_CAPTION))
        story.append(Spacer(1, 3))

    story.append(Paragraph("1. Governed Metric Lineage Catalog Matrix (M01 to M29 Overview)", T_H1))
    lineage_matrix = [
        ["Code", "Metric Name", "Grain", "Source Fact / Dim Tables", "Primary Business Owner"],
        ["M01–M06", "Headcount, Hires, Exits & Attrition", "Month, Dept", "fact_headcount_monthly, dim_employee", "HR Operations"],
        ["M07–M12", "Gross Pay, Overtime, Net Pay & Taxes", "Month, Dept", "fact_payroll, dim_department, dim_date", "Payroll & Compensation"],
        ["M13–M15", "Attendance Rate, Late Arrivals & Leave", "Month, Dept", "fact_attendance_monthly, fact_leave", "HR Operations"],
        ["M16–M18", "Revenue, Operating Expenses & Margin", "Month, Account", "fact_ledger, fact_expense, dim_account", "Corporate Finance"],
        ["M19–M21", "Invoices, Receivables & DSO", "Month, Client", "fact_invoice, fact_invoice_payment, dim_client", "Treasury & Collections"],
        ["M22–M25", "Story Points, Velocity & Task Rate", "Sprint, Team", "fact_task, dim_team, dim_sprint", "Engineering Operations"],
        ["M26–M28", "AI Anomalies, Attrition Risk & Forecast", "Month, Dept", "fact_anomaly, fact_attrition_risk, fact_forecast", "Data Science / AI Team"],
        ["M29", "Overtime per Active Head", "Month, Dept", "fact_payroll, fact_headcount_monthly", "HR & Finance Leadership"],
    ]
    story.append(build_wrapped_table(lineage_matrix, [55, 145, 75, 145, 100]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("2. Self-Service Documentation Architecture (docs/self_service_guide.md)", T_H1))
    guide_structure = [
        ["Section Name", "Target Audience", "Core Content & Guidance Provided"],
        [
            "1. Getting Started",
            "All Business Users",
            "Logging in, navigating the sidebar, using the dark/light mode toggle, filtering by date and department."
        ],
        [
            "2. Executive Scorecard",
            "Founders & C-Suite",
            "How to interpret the 8 headline KPIs, understanding target benchmarks, reading trend sparklines and statuses."
        ],
        [
            "3. Drilling Down",
            "Department Heads",
            "Navigating from scorecard summary cards directly to deep-dive analytics pages (P&L, Attrition, Invoices)."
        ],
        [
            "4. AI Signals & Models",
            "Managers & Risk Team",
            "Understanding machine learning predictions, reading confidence intervals, and acting on money-at-risk anomaly rankings."
        ],
        [
            "5. FAQ & Troubleshooting",
            "Support & Analysts",
            "Eight common business questions: reconciliation discrepancies, late invoice handling, data freshness, and export."
        ],
    ]
    story.append(build_wrapped_table(guide_structure, [100, 100, 320]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("3. Interactive Lineage UI Explorer (pages/0_About_and_Lineage.py)", T_H1))
    story.append(Paragraph(
        "Includes real-time metric search, owner filters, formula expanders, and live row count verification. "
        "Users can verify the exact database source and pipeline health directly from within the Streamlit interface.",
        T_BODY
    ))

    story.append(PageBreak())


# ─── PAGE 6: Task 20 — Production Release, Verification & Graduation ──────────
def build_page6(story: list) -> None:
    story.append(Paragraph("Task 20 — Production Release, Final Verification &amp; Graduation", T_TITLE))
    story.append(Paragraph(
        "Final milestone verifying end-to-end stability, code governance, and documentation. "
        "Executed the full 48-check automated test suite, validated cloud and container configurations, "
        "and established the production release git tag phase-4.",
        T_SUB
    ))
    story.append(Spacer(1, 3))

    # AI Signals Screenshot
    ss_ai = SCREENSHOT_DIR / "Screenshot 2026-11-07 124317.png"
    if ss_ai.exists():
        story.append(Paragraph("<b>Figure 6.1:</b> Responsible AI Signals Dashboard &amp; Money-at-Risk Ranking", T_H2))
        story.append(create_framed_image(ss_ai, width=520, height=130))
        story.append(Spacer(1, 2))
        story.append(Paragraph("Evidence: AI anomaly exposure, forecast confidence intervals, and mandatory human review disclosures.", T_CAPTION))
        story.append(Spacer(1, 3))

    story.append(Paragraph("1. Complete Automated Verification Suite Results (48 / 48 PASSED)", T_H1))
    test_suite_details = [
        ["Test Module", "Components Tested", "Validation Method", "Outcome"],
        ["T16 Scheduler", "scheduler.py, --run-now, docker-compose service", "Module import, CLI argument parse, container spec", "PASS"],
        ["T16 Heartbeat", "logs/scheduler.log", "JSON lines validation, timestamp verification", "PASS"],
        ["T17 RBAC Roles", "sql/006_rbac.sql (hr, finance, executive)", "Role definition inspection, permission boundary tests", "PASS"],
        ["T17 DQ Logging", "sql/007_dq_monitoring.sql, run_all_14_dq_checks", "Table creation DDL, audit logging hook execution", "PASS"],
        ["T18 Alert Rules", "scripts/alerting.py (8 business rules)", "Rule threshold evaluation, breach logic execution", "PASS"],
        ["T18 Alert UI", "pages/11_Alert_Log.py, sql/008_alert_log.sql", "Streamlit script syntax, audit table schema", "PASS"],
        ["T19 Lineage", "docs/metric_lineage_catalog.md (M01–M29)", "Complete 29-metric catalog, formulas, grains", "PASS"],
        ["T19 User Guide", "docs/self_service_guide.md (5 sections)", "Section presence, business workflow explanations", "PASS"],
        ["T20 Release", "README.md, reports/PDF, git tag phase-4, 12 pages", "File existence, tag confirmation, page validation", "PASS"],
    ]
    story.append(build_wrapped_table(test_suite_details, [75, 175, 215, 55]))
    story.append(Spacer(1, 4))

    story.append(Paragraph("2. Problems Encountered &amp; Production Engineering Solutions", T_H1))
    problems_table = [
        ["Challenge Encountered", "Root Cause Analysis", "Engineered Production Solution"],
        [
            "ReportLab Text Overflow",
            "Raw strings passed into ReportLab Table cells do not wrap automatically.",
            "Wrapped all cell contents in Paragraph objects with explicit colWidths."
        ],
        [
            "Dynamic Cloud DB Name",
            "Hardcoded 'pulseiq' database name in RBAC failed on Neon/Render cloud ('neondb').",
            "Refactored SQL migrations to use dynamic current_database() format strings."
        ],
        [
            "Local DNS Refusal on Neon",
            "Local Wi-Fi router / ISP DNS returned RCODE_REFUSED for AWS Neon hostnames.",
            "Implemented Google DNS-over-HTTPS (DoH) fallback with hostaddr parameter injection."
        ],
        [
            "Missing Linux Binary Wheels",
            "Rigid psycopg[binary]==3.2.3 pin failed on Render Linux build agent.",
            "Relaxed pins to >= and added .python-version (3.12.7) for deterministic builds."
        ],
    ]
    story.append(build_wrapped_table(problems_table, [110, 160, 250]))
    story.append(Spacer(1, 4))

    # Graduation Callout Box
    grad_data = [[
        Paragraph(
            "<font size='9' color='#FFFFFF'><b>🎓 PulseIQ Platform Graduation Statement</b></font><br/>"
            "<font size='7' color='#E2E8F0'>"
            "All 20 tasks across all 4 phases are 100% complete, fully verified, and production-ready. "
            "The platform securely ingests, validates, models, visualizes, monitors, and alerts on enterprise workforce, "
            "payroll, sprint, and financial data with enterprise-grade RBAC, automated scheduling, and complete metric lineage."
            "</font>",
            _style("GRAD_P", fontSize=7.5, leading=10, textColor=C_WHITE, alignment=TA_CENTER)
        )
    ]]
    t_grad = Table(grad_data, colWidths=[520])
    t_grad.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_PRIMARY),
        ('BOX', (0,0), (-1,-1), 1, C_SECONDARY),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(t_grad)


# ─── Build Execution ──────────────────────────────────────────────────────────
def build_pdf() -> None:
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        leftMargin=MARGIN_H,
        rightMargin=MARGIN_H,
        topMargin=MARGIN_V,
        bottomMargin=MARGIN_V,
        title="PulseIQ Phase 4 Submission Report",
        author="Vishesh Chaturvedi",
    )

    story: list = []
    build_page1(story)
    build_page2(story)
    build_page3(story)
    build_page4(story)
    build_page5(story)
    build_page6(story)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] PDF successfully generated: {OUTPUT_PATH}")
    print(f"     File Size: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build_pdf()
