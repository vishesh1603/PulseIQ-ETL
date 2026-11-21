"""
Page 0 — About PulseIQ & Metric Lineage (Task 19)
Interactive metric catalog and pipeline health panel.
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from theme_utils import apply_theme, get_theme_colors

apply_theme()
colors = get_theme_colors()

st.set_page_config(
    page_title="About & Metric Lineage — PulseIQ",
    page_icon="🔍",
    layout="wide",
)

PG_CONN = os.getenv("DATABASE_URL") or os.getenv("WAREHOUSE_DSN", "postgresql://pulseiq:pulseiq@localhost:5433/pulseiq")
if PG_CONN.startswith("postgres://"): PG_CONN = PG_CONN.replace("postgres://", "postgresql://", 1)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.lineage-header { background: linear-gradient(135deg, #1a1f3c 0%, #0d1117 100%);
    border-left: 5px solid #667eea; padding: 20px 24px; border-radius: 10px; margin-bottom: 24px; }
.lineage-header h2 { margin: 0; font-size: 1.6rem; color: #e2e8f0; }
.lineage-header p  { margin: 8px 0 0; color: #94a3b8; font-size: 0.95rem; }
.owner-badge { display:inline-block; padding:2px 8px; border-radius:10px; font-size:0.75em;
    font-weight:700; }
.owner-hr     { background:#667eea22; color:#667eea; border:1px solid #667eea44; }
.owner-fin    { background:#00c85122; color:#00c851; border:1px solid #00c85144; }
.owner-eng    { background:#f69c3422; color:#f69c34; border:1px solid #f69c3444; }
.owner-ai     { background:#ff4b9622; color:#ff4b96; border:1px solid #ff4b9644; }
.health-ok    { color:#00c851; font-weight:700; }
.health-fail  { color:#ff4b4b; font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ── Hero Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="lineage-header">
  <h2>🔍 About PulseIQ & Metric Lineage</h2>
  <p>Complete traceability for every number on the dashboard — from raw source table to business KPI.</p>
</div>
""", unsafe_allow_html=True)

# ── Platform Overview ─────────────────────────────────────────────────────────
st.markdown("## 🏢 Platform Overview")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("""
    **PulseIQ** is an end-to-end People Analytics platform:
    - 📥 **ETL Pipeline** — extracts, cleans, validates and loads raw HR, payroll, sprint and financial data
    - 🗄️ **PostgreSQL Data Warehouse** — star-schema `dw` with SCD Type 2 employee history
    - 📊 **28 Governed Metric Views** — business-defined formulas with privacy suppression
    - 🤖 **AI Signals** — anomaly detection, attrition risk scoring, headcount forecasting
    """)
with c2:
    st.markdown("""
    **Data Sources:**
    - `dim_employee` — 500+ employee SCD2 history
    - `fact_payroll` — 18 months of payroll (₹14.7 Cr gross)
    - `fact_attendance_monthly` — 10,000+ attendance records
    - `fact_task` — 28k engineering tasks across 16 teams
    - `fact_ledger` — General ledger (P&L, 4000–5999 accounts)
    - `fact_invoice` — ₹13.9 Cr open receivables book
    """)
with c3:
    st.markdown("""
    **Submission:**
    - **Author:** Vishesh Chaturvedi
    - **GitHub:** [vishesh1603/PulseIQ-ETL](https://github.com/vishesh1603/PulseIQ-ETL)
    - **Phase 1 Tag:** `git checkout phase-1`
    - **Phase 2 Tag:** `git checkout phase-2`
    - **Phase 3 Tag:** `git checkout phase-3`
    - **Phase 4 Tag:** `git checkout phase-4`
    """)

st.divider()

# ── Pipeline Health Panel ─────────────────────────────────────────────────────
st.markdown("## ⚙️ Pipeline Health")

@st.cache_data(ttl=30)
def load_pipeline_health() -> dict:
    last_run_path = PROJECT_ROOT / "logs" / "last_run.json"
    if last_run_path.exists():
        try:
            return json.loads(last_run_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

lr = load_pipeline_health()
if lr:
    h1, h2, h3, h4, h5 = st.columns(5)
    status = lr.get("status", "UNKNOWN")
    icon = "✅" if status == "SUCCESS" else "❌"
    h1.metric("Pipeline Status", f"{icon} {status}")
    started = lr.get("started_at", "—")
    if started != "—":
        try:
            started = datetime.fromisoformat(started).strftime("%d %b %Y %H:%M UTC")
        except Exception:
            pass
    h2.metric("Last Run", started)
    h3.metric("Duration", f"{lr.get('duration_seconds', 0):.1f}s")
    tables = lr.get("tables", {})
    total_rows_in = sum(t.get("rows_in", 0) for t in tables.values())
    h4.metric("Total Rows Processed", f"{total_rows_in:,}")
    total_rejected = sum(t.get("rows_rejected", 0) for t in tables.values())
    h5.metric("Rows Rejected (Quarantined)", total_rejected)

    with st.expander("📋 Per-Table Row Counts"):
        tbl_data = [
            {
                "Table": name,
                "Rows In": t.get("rows_in", 0),
                "Rows Out": t.get("rows_out", 0),
                "Rejected": t.get("rows_rejected", 0),
                "Repaired": t.get("values_repaired", 0),
                "Reject %": f"{t.get('rejected_pct', 0):.2f}%",
            }
            for name, t in tables.items()
        ]
        st.dataframe(pd.DataFrame(tbl_data), use_container_width=True, hide_index=True)
else:
    st.info("No ETL run log found. Run `python scripts/scheduler.py --run-now` to execute the pipeline.")

st.divider()

# ── Metric Lineage Catalog ────────────────────────────────────────────────────
st.markdown("## 📐 Metric Lineage Catalog (28 Official Metrics + M29)")

# Full metric catalog data
METRIC_CATALOG = [
    ("M01","Headcount","dw.fact_headcount_monthly, dw.dim_employee","dw.metric_m01_headcount","COUNT DISTINCT active employees on last day of month","Department × Month","HR Analytics","count",">=5",">=420"),
    ("M02","Hires","dw.fact_headcount_monthly","dw.metric_m02_hires","Employees whose hire_date falls in the month","Department × Month","HR Analytics","count",">=5","—"),
    ("M03","Exits","dw.fact_headcount_monthly","dw.metric_m03_exits","Employees whose exit_date falls in the month","Department × Month","HR Analytics","count",">=5","—"),
    ("M04","Monthly Attrition Rate","dw.fact_headcount_monthly","dw.metric_m04_attrition_rate_monthly","Exits / headcount_start × 100","Department × Month","HR Analytics","percent",">=10","<=3%/mo"),
    ("M05","12M Attrition Rate","dw.fact_headcount_monthly","dw.metric_m05_attrition_rate_12m","Rolling 12M exits / avg headcount × 100","Department × Month","HR Analytics","percent",">=10","<=12%"),
    ("M06","Voluntary Attrition 12M","dw.fact_headcount_monthly","dw.metric_m06_voluntary_attrition_rate_12m","Voluntary exits / avg headcount × 100 (12M rolling)","Department × Month","HR Analytics","percent",">=10","—"),
    ("M07","Gross Pay","dw.fact_payroll, dw.dim_department, dw.dim_date","dw.metric_m07_gross_pay","SUM(gross_pay) — total earnings before deductions","Department × Month","Payroll","INR",">=5","—"),
    ("M08","Net Pay","dw.fact_payroll","dw.metric_m08_net_pay","SUM(net_pay) — take-home after deductions","Department × Month","Payroll","INR",">=5","—"),
    ("M09","Payroll Cost (Employer)","dw.fact_payroll","dw.metric_m09_payroll_cost","SUM(employer_cost) — gross + employer PF/ESI","Department × Month","Finance","INR",">=5","—"),
    ("M10","Cost Per Head","dw.fact_payroll","dw.metric_m10_cost_per_head","SUM(employer_cost) / COUNT(DISTINCT employee_id)","Department × Month","Finance","INR",">=5","—"),
    ("M11","Overtime Share","dw.fact_payroll","dw.metric_m11_overtime_share","SUM(overtime_pay) / SUM(employer_cost) × 100","Department × Month","Payroll","percent",">=5","—"),
    ("M12","Variable Pay Share","dw.fact_payroll","dw.metric_m12_variable_pay_share","SUM(variable_pay) / SUM(gross_pay) × 100","Department × Month","Payroll","percent",">=5","—"),
    ("M13","Attendance Rate","dw.fact_attendance_monthly","dw.metric_m13_attendance_rate","(present_days + 0.5×half_days) / scheduled_days","Department × Month","HR Analytics","ratio",">=5",">=0.90"),
    ("M14","Late Arrival Rate","dw.fact_attendance_monthly","dw.metric_m14_late_arrival_rate","SUM(late_arrivals) / SUM(present_days)","Department × Month","HR Analytics","ratio",">=5","—"),
    ("M15","Leave Without Pay Days","dw.fact_payroll","dw.metric_m15_lop_days","SUM(lop_days) — unpaid absence and leave","Department × Month","Payroll","days",">=5","—"),
    ("M16","Revenue","dw.fact_ledger (4001–4004), dw.dim_account","dw.metric_m16_revenue","-SUM(signed_amount) for revenue accounts","Account × Month","Finance","INR","None",">=₹7.5Cr"),
    ("M17","Net Profit","dw.fact_ledger (>=4000)","dw.metric_m17_net_profit","-SUM(revenue accounts) - SUM(expense accounts)","Month","Finance","INR","None",">= ₹0"),
    ("M18","Operating Margin","dw.metric_m17_net_profit","dw.metric_m18_operating_margin","Net Profit / Revenue × 100","Month","Finance","percent","None",">=10%"),
    ("M19","Payroll % of Revenue","dw.fact_payroll, dw.fact_ledger","dw.metric_m19_payroll_pct_revenue","SUM(employer_cost) / Revenue × 100","Month","Finance","percent","None","—"),
    ("M20","Days Sales Outstanding","dw.fact_ledger (1100), dw.fact_invoice","dw.metric_m20_dso","Receivables / 90d revenue × 90","Month","Finance","days","None","<=60d"),
    ("M21","Overdue Receivables","dw.fact_invoice, dw.dim_client","dw.metric_m21_overdue_receivables","SUM(balance_due) for open invoices","Client","Finance","INR","None","—"),
    ("M22","Task Completion Rate","dw.fact_task, dw.dim_team, dw.dim_sprint","dw.metric_m22_task_completion_rate","Done / (All - Cancelled) × 100","Team × Sprint","Eng Ops","percent",">=5",">=70%"),
    ("M23","On-Time Delivery Rate","dw.fact_task","dw.metric_m23_ontime_delivery_rate","Done & completed_on_time=Y / Done × 100","Team × Sprint","Eng Ops","percent",">=5","—"),
    ("M24","Velocity","dw.fact_task","dw.metric_m24_velocity","SUM(story_points) for Done tasks","Team × Sprint","Eng Ops","points","None","—"),
    ("M25","Avg Cycle Time","dw.fact_task","dw.metric_m25_average_cycle_time","AVG(completed_date - started_date) for Done","Team × Sprint","Eng Ops","days",">=5","—"),
    ("M26","Anomaly Flag Rate","dw.fact_anomaly","dw.metric_m26_anomaly_flag_rate","COUNT(flagged=Y) / COUNT(*) × 100","Source × Month","AI/ML","percent","None","—"),
    ("M27","High-Risk Attrition Share","dw.fact_attrition_risk, dw.dim_department","dw.metric_m27_high_risk_share","COUNT(risk_band=High) / COUNT(*) × 100","Department","AI/ML","percent",">=10","—"),
    ("M28","Forecast Error (MAPE)","dw.fact_forecast, dw.fact_headcount_monthly","dw.metric_m28_forecast_error","AVG(|actual-forecast| / actual) × 100","Dept × Month","AI/ML","percent","None","—"),
    ("M29","WFH Share","dw.fact_attendance_monthly","dw.metric_m29_wfh_share","SUM(wfh_days) / SUM(present_days) × 100 [Mini Challenge]","Department × Month","HR Analytics","percent",">=5","—"),
]

catalog_df = pd.DataFrame(METRIC_CATALOG, columns=[
    "Code","Metric Name","Source Tables","SQL View","Business Definition",
    "Grain","Owner","Unit","Min Group Size","Target"
])

# ── Search & Filter ───────────────────────────────────────────────────────────
col_s1, col_s2 = st.columns([3, 1])
with col_s1:
    search_term = st.text_input("🔍 Search metrics", placeholder="Search by name, code, source table…",
                                 key="metric_search")
with col_s2:
    owner_filter = st.selectbox("Filter by Owner", ["All"] + sorted(catalog_df["Owner"].unique().tolist()),
                                 key="owner_filter")

filtered_catalog = catalog_df.copy()
if search_term:
    mask = (
        filtered_catalog["Code"].str.contains(search_term, case=False) |
        filtered_catalog["Metric Name"].str.contains(search_term, case=False) |
        filtered_catalog["Source Tables"].str.contains(search_term, case=False) |
        filtered_catalog["Business Definition"].str.contains(search_term, case=False)
    )
    filtered_catalog = filtered_catalog[mask]
if owner_filter != "All":
    filtered_catalog = filtered_catalog[filtered_catalog["Owner"] == owner_filter]

st.markdown(f"Showing **{len(filtered_catalog)}** of **{len(catalog_df)}** metrics")

# Display main table
st.dataframe(
    filtered_catalog[["Code","Metric Name","Owner","Unit","Source Tables","Grain","Target","Min Group Size"]],
    use_container_width=True,
    height=420,
    hide_index=True,
)

# ── SQL View Detail Expanders ─────────────────────────────────────────────────
st.divider()
st.markdown("## 🔎 Metric Detail — Formula & Lineage")
selected_code = st.selectbox(
    "Select a metric to see its formula",
    catalog_df["Code"].tolist(),
    key="metric_detail_select"
)

row = catalog_df[catalog_df["Code"] == selected_code].iloc[0]

c_left, c_right = st.columns(2)
with c_left:
    st.markdown(f"**Metric:** {row['Code']} — {row['Metric Name']}")
    st.markdown(f"**Owner:** {row['Owner']}  |  **Unit:** {row['Unit']}")
    st.markdown(f"**Grain:** {row['Grain']}")
    st.markdown(f"**Target:** {row['Target']}  |  **Min Group Size:** {row['Min Group Size']}")
    st.markdown(f"**Definition:** {row['Business Definition']}")

with c_right:
    st.markdown(f"**Source Table(s):**")
    for src in row["Source Tables"].split(","):
        st.markdown(f"- `{src.strip()}`")
    st.markdown(f"**SQL View:** `{row['SQL View']}`")

    # Fetch live row count from warehouse
    if st.button(f"📊 Show Live Row Count from {row['SQL View']}", key="live_count_btn"):
        try:
            import psycopg
            conn = psycopg.connect(PG_CONN)
            cur = conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {row['SQL View']}")
            count = cur.fetchone()[0]
            conn.close()
            st.success(f"✅ `{row['SQL View']}` has **{count:,}** rows in the warehouse.")
        except Exception as exc:
            st.error(f"Could not query warehouse: {exc}")

st.divider()

# ── Lineage Diagram ───────────────────────────────────────────────────────────
st.markdown("## 🗺️ Data Flow Overview")
st.markdown("""
```
Raw Excel/CSV → ETL Pipeline → PostgreSQL dw Schema → Metric Views → Streamlit Dashboard
     ↑               ↓               ↓                     ↓                ↓
  data/raw     Pandera contracts  Star schema          28 governed        10 pages
                (validate.py)   (dim + fact tables)    SQL views        (pages/)
                                                            ↓
                                                     dw.metric_catalog
                                                   (single source of truth)
```
""")

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.markdown("**Dimension Tables**")
    for d in ["dim_employee","dim_department","dim_role","dim_date",
              "dim_account","dim_vendor","dim_client","dim_leave_type","dim_team","dim_sprint"]:
        st.markdown(f"- `dw.{d}`")
with col_b:
    st.markdown("**Fact Tables**")
    for f in ["fact_payroll","fact_attendance_monthly","fact_leave","fact_task",
              "fact_headcount_monthly","fact_ledger","fact_invoice","fact_expense",
              "fact_attrition_risk","fact_anomaly","fact_forecast"]:
        st.markdown(f"- `dw.{f}`")
with col_c:
    st.markdown("**Monitoring Tables (Phase 4)**")
    for m in ["dq_check_log","alert_log"]:
        st.markdown(f"- `dw.{m}`")
    st.markdown("**RBAC Roles**")
    for r in ["role_hr","role_finance","role_executive"]:
        st.markdown(f"- `{r}`")

st.divider()
st.markdown("""
<div style="text-align:center; color:#94a3b8; font-size:0.85rem;">
PulseIQ Phase 4 — Task 19: Metric Lineage Catalog & Self-Service Documentation<br/>
<a href="https://github.com/vishesh1603/PulseIQ-ETL" target="_blank">GitHub Repository</a>
</div>
""", unsafe_allow_html=True)
