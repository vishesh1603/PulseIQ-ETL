"""
Generate Phase 2: People and Teams Official PDF Report: DataAnalytics_Vishesh_Phase2_Report.pdf
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
import sys, os

PDF_PATH = r"c:\Users\DELL\Downloads\pulseiq-etl1\reports\DataAnalytics_Vishesh_Phase2_Report.pdf"

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
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#718096"))
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 36, 25, page_str)
        self.drawString(36, 25, "PulseIQ — Phase 2: People and Teams Report | Candidate: Vishesh Chaturvedi")
        self.restoreState()

def build_pdf():
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0072B2")
    )
    
    sub_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#4A5568")
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0072B2"),
        spaceBefore=8,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=11.5,
        textColor=colors.HexColor("#2D3748")
    )

    tbl_head_style = ParagraphStyle(
        'TblHead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1
    )

    tbl_cell_style = ParagraphStyle(
        'TblCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#2D3748")
    )

    tbl_bold_cell = ParagraphStyle(
        'TblBoldCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#1A202C")
    )

    story = []

    # ======================== HEADER ========================
    story.append(Paragraph("PulseIQ — Phase 2 Review & Verification Report", title_style))
    story.append(Spacer(1, 3))
    story.append(Paragraph("Phase 2: People and Teams (Tasks 6 to 10) — Attendance Seasonality, Attrition Risk, Team Delivery, Payroll Reconciliation & Variance", sub_style))
    story.append(Spacer(1, 5))

    header_data = [
        [
            Paragraph("<b>Candidate Name:</b> Vishesh Chaturvedi", body_style),
            Paragraph("<b>Track:</b> Data Analytics / Engineering", body_style),
            Paragraph("<b>Phase:</b> Phase 2: People and Teams", body_style)
        ],
        [
            Paragraph("<b>GitHub Repository:</b> <a href='https://github.com/vishesh1603/PulseIQ-ETL' color='#0072B2'><u>github.com/vishesh1603/PulseIQ-ETL</u></a>", body_style),
            Paragraph("<b>Git Tag:</b> <code>phase-2</code>", body_style),
            Paragraph("<b>Collaborator Added:</b> <code>fobesitech</code>", body_style)
        ]
    ]
    t_header = Table(header_data, colWidths=[230, 160, 150])
    t_header.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#EDF2F7")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 6))

    # ======================== SECTION 1: 5 TASKS TABLE ========================
    story.append(Paragraph("1. Phase 2: Five-Task Deliverables Table", h1_style))
    
    tasks_data = [
        [
            Paragraph("Task", tbl_head_style),
            Paragraph("Objective & Curriculum Spec", tbl_head_style),
            Paragraph("Status", tbl_head_style),
            Paragraph("Verified Deliverable & Evidence (Repository Links)", tbl_head_style)
        ],
        [
            Paragraph("<b>Task 6</b><br/>Attendance & Leave", tbl_bold_cell),
            Paragraph("Attendance rate, late arrivals, overtime, leave by type; calendar holiday overlay; explain 3 dips; 3 numeric findings.", tbl_cell_style),
            Paragraph("<font color='#009E73'><b>DONE</b></font>", tbl_bold_cell),
            Paragraph("<code>pages/1_Attendance_and_Leave.py</code>. 19 public holidays mapped. Heatmap by dept. October 2025 (Diwali), Dec 2025 (Year-end) and Aug 2025 dips explained.", tbl_cell_style)
        ],
        [
            Paragraph("<b>Task 7</b><br/>Attrition Analytics", tbl_bold_cell),
            Paragraph("Exits by month, dept, tenure; voluntary split; CortexHR flight risk labelled 'Predicted, not certain'; group-only privacy.", tbl_cell_style),
            Paragraph("<font color='#009E73'><b>DONE</b></font>", tbl_bold_cell),
            Paragraph("<code>pages/2_Attrition_Analytics.py</code>. M04 monthly & M05 rolling attrition; tenure bands (1-2 yr peak); AI flight risk banner with k-anonymity (>=10).", tbl_cell_style)
        ],
        [
            Paragraph("<b>Task 8</b><br/>Team Productivity", tbl_bold_cell),
            Paragraph("Velocity, cycle time, on-time rate across 16 teams and 38 sprints; cancelled/reopened rules; hand-verify 2 teams.", tbl_cell_style),
            Paragraph("<font color='#009E73'><b>DONE</b></font>", tbl_bold_cell),
            Paragraph("<code>pages/3_Team_Productivity.py</code>. Sprint/team selector across 28,868 tasks. T01 (162 pts) & T02 (210 pts) hand-verified on Sprint 1 with 100% precision.", tbl_cell_style)
        ],
        [
            Paragraph("<b>Task 9</b><br/>Payroll Cost & Recon", tbl_bold_cell),
            Paragraph("Gross, net, employer cost, cost per head; 18-month reconciliation against answer key; document 4 bad quarantined rows.", tbl_cell_style),
            Paragraph("<font color='#009E73'><b>DONE</b></font>", tbl_bold_cell),
            Paragraph("<code>pages/4_Payroll_Cost_and_Reconciliation.py</code>. Reconciles to answer key with INR 0.00 difference. Quarantined bad rows (PI-X0001 to PI-X0004) audited.", tbl_cell_style)
        ],
        [
            Paragraph("<b>Task 10</b><br/>Budget vs Actual & KPIs", tbl_bold_cell),
            Paragraph("Compare payroll to budget; sign convention rule; traffic lights against kpi_targets; rank overspend; verify 3 dept-months.", tbl_cell_style),
            Paragraph("<font color='#009E73'><b>DONE</b></font>", tbl_bold_cell),
            Paragraph("<code>pages/5_Budget_vs_Actual_Variance.py</code>. Standard financial sign rules. Traffic lights (Green/Red). April 2025 D01, D00, D02 hand-verified. Top 2 recommendations.", tbl_cell_style)
        ]
    ]

    t_tasks = Table(tasks_data, colWidths=[65, 175, 45, 255])
    t_tasks.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0072B2")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
    ]))
    story.append(t_tasks)
    story.append(Spacer(1, 6))

    # ======================== SECTION 2: PROOF IT WORKS ========================
    story.append(Paragraph("2. Proof It Works: Hand Checks & Official Reconciliations", h1_style))
    
    proof_text = (
        "<b>1. Task 8 Hand Proof (Sprint 1 Delivery across 2 Teams):</b><br/>"
        "• <b>Team T01 (Platform Core):</b> 58 planned, 50 done | <b>Velocity: 162 pts</b> | On-time: 96.0% (48/50) | Cycle Time: <b>4.64 days</b>.<br/>"
        "• <b>Team T02 (Payments & Billing):</b> 70 planned, 63 done | <b>Velocity: 210 pts</b> | On-time: 93.7% (59/63) | Cycle Time: <b>4.79 days</b>.<br/>"
        "<b>2. Task 9 Payroll Reconciliation (18-Month Audit vs Answer Key):</b><br/>"
        "• All 18 months (April 2025 to September 2026) reconcile to the exact paisa (<b>INR 0.00 variance</b>) after quarantining 4 dirty rows.<br/>"
        "• <i>Isolated Bad Rows:</i> <code>PI-X0001</code> & <code>PI-X0002</code> (Duplicates, +INR 213,025.04 gross); <code>PI-X0003</code> & <code>PI-X0004</code> (Orphan Keys, +INR 192,542.42 gross).<br/>"
        "<b>3. Task 10 Budget Variance Hand Proof (April 2025 Sample):</b><br/>"
        "• <b>D01 Engineering:</b> Actual INR 21,428,108.75 vs Budget INR 23,340,000.00 = <b>-INR 1,911,891.25 (-8.19% Favorable Savings)</b>.<br/>"
        "• <b>D00 Executive Office:</b> Actual INR 480,809.00 vs Budget INR 479,000.00 = <b>+INR 1,809.00 (+0.38% Overspend)</b>.<br/>"
        "• <b>D02 Product & Design:</b> Actual INR 4,823,692.67 vs Budget INR 5,285,000.00 = <b>-INR 461,307.33 (-8.73% Favorable Savings)</b>."
    )
    story.append(Paragraph(proof_text, body_style))
    story.append(Spacer(1, 6))

    # ======================== PAGE BREAK ========================
    story.append(PageBreak())

    # ======================== SECTION 3: MINI CHALLENGE ========================
    story.append(Paragraph("3. Mini Challenge: 5-Line Raw-Row Lineage & Hand Proof", h1_style))
    challenge_desc = (
        "<b>Challenge Selection:</b> Engineering (D01) April 2025 Budget Variance (<b>-INR 1,911,891.25</b>).<br/>"
        "<b>5-Line Lineage Trace (Raw Row to Final Dashboard Chart):</b><br/>"
        "<b>1. Raw Fact Rows:</b> In <code>data/raw/PulseIQ_Star_Schema_Dataset.xlsx</code>, sheet <code>fact_payroll</code>, 145 rows match <code>date_key = 20250430</code> and <code>department_id = 'D01'</code>.<br/>"
        "<b>2. Dimension Resolution:</b> In <code>dim_department</code>, department code <code>'D01'</code> resolves to surrogate <code>department_key = 2</code> (Engineering).<br/>"
        "<b>3. Warehouse Aggregation:</b> In schema <code>dw</code>, <code>dw.metric_m09_payroll_cost</code> executes <code>SUM(employer_cost)</code> for D01 in 2025-04, yielding exactly <b>INR 21,428,108.75</b>.<br/>"
        "<b>4. Plan Join:</b> The query inner joins <code>dw.budget_payroll_dept_month</code> on <code>department_id = 'D01'</code> and <code>month = '2025-04-01'</code>, retrieving the approved budget of <b>INR 23,340,000.00</b>.<br/>"
        "<b>5. Final Metric & Rendering:</b> The dashboard applies sign rule <code>Actual - Budget</code>: <code>21,428,108.75 - 23,340,000.00 = -1,911,891.25</code> (-8.19%), rendering a green savings bar on the variance chart."
    )
    story.append(Paragraph(challenge_desc, body_style))
    story.append(Spacer(1, 8))

    # ======================== SECTION 4: SELF-CHECK ========================
    story.append(Paragraph("4. Self-Check: Explaining Reconciliation & Variance in Plain English", h1_style))
    self_check_text = (
        "<b>Q: Can I explain reconciliation and variance to a non-technical person?</b><br/>"
        "<b>Yes:</b><br/>"
        "• <b>Reconciliation:</b> <i>'Think of reconciliation like balancing your bank statement against your credit card receipts at the end of the month. If the bank says you spent INR 53,363,392 and your receipts say you spent INR 53,774,359, reconciliation is the detective work that proves four receipts were either entered twice or made by an unauthorized card. Once you quarantine those four bad receipts, both books match to the exact paisa (INR 0.00 gap), proving that leadership can 100% trust the figures.'</i><br/>"
        "• <b>Variance:</b> <i>'Variance simply answers: Did we spend more or less than we planned? If you set aside INR 10,000 for groceries and spent INR 9,000, your variance is -INR 1,000 (a good savings, green). If you spent INR 11,000, your variance is +INR 1,000 (an overspend, red). By tracking variance by department, managers immediately know where hiring lags saved budget and where deal bonuses ran over.'</i>"
    )
    story.append(Paragraph(self_check_text, body_style))
    story.append(Spacer(1, 8))

    # ======================== SECTION 5: WHAT WAS LEARNED ========================
    story.append(Paragraph("5. What I Learned (In My Own Words)", h1_style))
    learned_text = (
        "Phase 2 demonstrated that operational analytics cannot exist in a vacuum; context dictates reality. "
        "I learned that an attendance dip in October is not an employee crisis—it is Diwali, and analysts must map calendar holidays before raising alarms. "
        "In AI governance, I learned that flight risk scores must be framed as supportive conversation leads rather than personnel verdicts, and must always be masked by k-anonymity. "
        "Finally, establishing clear financial sign conventions upfront is essential to prevent confusion between executives and engineers during variance meetings."
    )
    story.append(Paragraph(learned_text, body_style))
    story.append(Spacer(1, 8))

    # ======================== SECTION 6: PROBLEMS & SOLUTIONS ========================
    story.append(Paragraph("6. Problems Hit and How They Were Solved", h1_style))
    problems_data = [
        [
            Paragraph("Challenge / Bug Encountered", tbl_head_style),
            Paragraph("Root Cause Analysis", tbl_head_style),
            Paragraph("Engineered Resolution", tbl_head_style)
        ],
        [
            Paragraph("<b>Holiday Confounding Attendance Rates</b>", tbl_bold_cell),
            Paragraph("October 2025 showed an apparent 1.2% dip in attendance, creating unnecessary manager alarm.", tbl_cell_style),
            Paragraph("Integrated 19 calendar holidays from <code>dim_date</code> directly into the Plotly chart annotations, contextualizing Diwali/Dussehra break clusters.", tbl_cell_style)
        ],
        [
            Paragraph("<b>Duplicate Payroll Inflation (INR 410k Gap)</b>", tbl_bold_cell),
            Paragraph("Raw <code>fact_payroll</code> contained 2 duplicate item IDs and 2 unmapped employee IDs, violating reconciliation answer keys.", tbl_cell_style),
            Paragraph("Enforced primary key constraints and orphan checks at warehouse ingestion; documented all 4 quarantined rows in an explicit audit table.", tbl_cell_style)
        ],
        [
            Paragraph("<b>Cancelled Tasks Distorting Delivery</b>", tbl_bold_cell),
            Paragraph("Teams with high sprint scope changes showed falsely low completion rates when cancelled tasks were counted as incomplete work.", tbl_cell_style),
            Paragraph("Implemented governed completion formula: <code>COUNT(status='Done') / COUNT(status != 'Cancelled')</code>, documenting rule clearly in app banner.", tbl_cell_style)
        ]
    ]
    t_prob = Table(problems_data, colWidths=[140, 180, 220])
    t_prob.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0072B2")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
    ]))
    story.append(t_prob)
    story.append(Spacer(1, 8))

    # ======================== SECTION 7: PLAN FOR PHASE 3 ========================
    story.append(Paragraph("7. Plan for Phase 3: Money and Operations (Days 11 to 15)", h1_style))
    plan_text = (
        "• <b>Task 11: General Ledger & Profitability:</b> Analyze double-entry ledger lines (accounts 4001-4004 vs 5001-5112) for net margin and operating profit.<br/>"
        "• <b>Task 12: Invoicing, DSO & Collections:</b> Track 743 invoices, aging buckets, and Days Sales Outstanding (M20) collection cycles across 28 corporate clients.<br/>"
        "• <b>Task 13: Accounts Payable & Vendor Expenses:</b> Analyze vendor disbursements, GST input credits, and cost-center allocations.<br/>"
        "• <b>Task 14: Headcount & Payroll Forecasting:</b> Compare 72-row time-series forecast models against actual performance using MAPE (M28).<br/>"
        "• <b>Task 15: Cross-Domain Executive Cockpit:</b> Unify workforce headcount, payroll cost, revenue realization, and AI anomaly alerts into an integrated C-suite dashboard."
    )
    story.append(Paragraph(plan_text, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Report generated successfully at: {PDF_PATH}")

if __name__ == '__main__':
    build_pdf()
