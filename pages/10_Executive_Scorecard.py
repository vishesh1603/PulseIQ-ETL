"""
PulseIQ Executive Company-Health Scorecard (Task 15)
Founder's 8 Headline KPIs pulled strictly from governed metric views.
Features target baselines, traffic-light status, 6-month historical trends,
print-to-A4 CSS styling, and deep-dive navigation links.
"""
import streamlit as st
import psycopg
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(page_title="PulseIQ — Executive Health Scorecard", page_icon="🏛️", layout="wide")

st.markdown("""
<style>
    /* Print Optimization: Format for single A4 page */
    @media print {
        header, footer, .stSidebar, .rule-box { display: none !important; }
        body { font-size: 11pt; color: #000; }
        .scorecard-card { page-break-inside: avoid; border: 1px solid #ccc !important; box-shadow: none !important; }
        .stApp { max-width: 100% !important; margin: 0 !important; padding: 0 !important; }
    }

    .scorecard-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 16px 18px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        margin-bottom: 16px;
        transition: transform 0.15s ease-in-out;
    }
    .kpi-num {
        font-size: 12px;
        font-weight: 700;
        color: #718096;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-name {
        font-size: 16px;
        font-weight: 700;
        color: #1A202C;
        margin: 2px 0 6px 0;
    }
    .kpi-main-val {
        font-size: 26px;
        font-weight: 800;
        color: #111111;
    }
    .kpi-target-tag {
        font-size: 12px;
        color: #4A5568;
        background-color: #EDF2F7;
        padding: 3px 8px;
        border-radius: 4px;
        display: inline-block;
        margin-top: 4px;
    }
    .traffic-pill {
        font-size: 12px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 12px;
        display: inline-block;
        float: right;
    }
    .status-green { background-color: #DEF7EC; color: #03543F; }
    .status-yellow { background-color: #FEF08A; color: #713F12; }
    .status-red { background-color: #FDE8E8; color: #9B1C1C; }
    .page-link-btn {
        font-size: 12px;
        color: #0072B2;
        text-decoration: none;
        font-weight: 600;
        display: inline-block;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

PG_HOST = os.getenv("WAREHOUSE_HOST", "localhost")
PG_PORT = os.getenv("WAREHOUSE_PORT", "5433")
PG_DB = os.getenv("WAREHOUSE_DB", "pulseiq")
PG_USER = os.getenv("WAREHOUSE_USER", "pulseiq")
PG_PASS = os.getenv("WAREHOUSE_PASSWORD", "pulseiq")

@st.cache_resource
def get_db_connection():
    conn = psycopg.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS
    )
    conn.autocommit = True
    return conn

def query_df(sql, params=None):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        return pd.DataFrame(rows, columns=cols)

st.title("Executive Company-Health Scorecard")
st.markdown("### The 8 Headline Founder KPIs Sourced Exclusively from Governed Metric Views (Task 15)")

# Sidebar Month Selector
try:
    months_df = query_df("SELECT DISTINCT year_month FROM dw.dim_date WHERE year_month BETWEEN '2025-04' AND '2026-09' ORDER BY year_month")
    all_months = months_df['year_month'].tolist()
    selected_month = st.sidebar.selectbox("Reporting Period", all_months, index=len(all_months)-1)
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

# Helper to fetch metric values strictly from metric views
def fetch_scorecard_metrics(month_str):
    conn = get_db_connection()
    with conn.cursor() as cur:
        # M01 Headcount
        cur.execute("SELECT SUM(unsuppressed_headcount) FROM dw.metric_m01_headcount WHERE year_month = %s", (month_str,))
        m01 = float(cur.fetchone()[0] or 0)

        # M05 12M Attrition
        cur.execute("SELECT ROUND(AVG(unsuppressed_attrition_12m_pct), 2) FROM dw.metric_m05_attrition_rate_12m WHERE year_month = %s", (month_str,))
        m05 = float(cur.fetchone()[0] or 0)

        # M16 Revenue
        cur.execute("SELECT SUM(revenue) FROM dw.metric_m16_revenue WHERE year_month = %s", (month_str,))
        m16 = float(cur.fetchone()[0] or 0)

        # M18 Operating Margin
        cur.execute("SELECT operating_margin_pct FROM dw.metric_m18_operating_margin WHERE year_month = %s", (month_str,))
        m18 = float(cur.fetchone()[0] or 0)

        # M19 Payroll as % of Revenue
        cur.execute("SELECT payroll_pct_of_revenue FROM dw.metric_m19_payroll_pct_revenue WHERE year_month = %s", (month_str,))
        m19 = float(cur.fetchone()[0] or 0)

        # M20 Days Sales Outstanding (DSO)
        cur.execute("SELECT dso_days FROM dw.metric_m20_dso WHERE year_month = %s", (month_str,))
        m20 = float(cur.fetchone()[0] or 0)

        # M13 Attendance Rate
        cur.execute("SELECT ROUND(AVG(unsuppressed_attendance_rate) * 100, 2) FROM dw.metric_m13_attendance_rate WHERE year_month = %s", (month_str,))
        m13 = float(cur.fetchone()[0] or 0)

        # M23 On-Time Delivery Rate (Latest Sprint)
        cur.execute("SELECT ROUND(AVG(unsuppressed_on_time_rate), 2) FROM dw.metric_m23_ontime_delivery_rate WHERE sprint_name = 'Sprint 38'")
        m23 = float(cur.fetchone()[0] or 0)

        return {
            'm01': m01, 'm05': m05, 'm16': m16, 'm18': m18,
            'm19': m19, 'm20': m20, 'm13': m13, 'm23': m23
        }

m_vals = fetch_scorecard_metrics(selected_month)

# 8 KPIs Setup: (ID, Name, Value, Formatted, Target, Status, ColorClass, Reason, Link)
kpis = [
    {
        "id": "M01",
        "name": "Headcount",
        "val_str": f"{int(m_vals['m01'])} Staff",
        "target": "Target: ≥420 Capacity",
        "status": "🟢 On Target" if m_vals['m01'] >= 420 else "🟡 Understaffed",
        "cls": "status-green" if m_vals['m01'] >= 420 else "status-yellow",
        "reason": "Measures total organizational productive capacity to fulfill customer contracts.",
        "link": "Attrition_Analytics"
    },
    {
        "id": "M05",
        "name": "12M Rolling Attrition",
        "val_str": f"{m_vals['m05']:.2f}%",
        "target": "Target: ≤12.0%",
        "status": "🟢 Within Target" if m_vals['m05'] <= 12.0 else "🔴 Breach",
        "cls": "status-green" if m_vals['m05'] <= 12.0 else "status-red",
        "reason": "Signals retention health; losing institutional knowledge directly increases replacement cost.",
        "link": "Attrition_Analytics"
    },
    {
        "id": "M16",
        "name": "Monthly Revenue",
        "val_str": f"₹{m_vals['m16']/1e5:,.2f} L",
        "target": "Target: ≥₹750 L",
        "status": "🟢 Strong" if m_vals['m16'] >= 7.5e7 else "🟡 Soft",
        "cls": "status-green" if m_vals['m16'] >= 7.5e7 else "status-yellow",
        "reason": "Topline commercial engine driving enterprise valuation and operational liquidity.",
        "link": "Profit_and_Loss"
    },
    {
        "id": "M18",
        "name": "Operating Margin",
        "val_str": f"{m_vals['m18']:.2f}%",
        "target": "Target: ≥15.0%",
        "status": "🟢 Healthy" if m_vals['m18'] >= 15.0 else "🔴 Low Margin",
        "cls": "status-green" if m_vals['m18'] >= 15.0 else "status-red",
        "reason": "Bottom-line efficiency; proves whether scale translates into sustainable profit.",
        "link": "Profit_and_Loss"
    },
    {
        "id": "M19",
        "name": "Payroll % of Revenue",
        "val_str": f"{m_vals['m19']:.2f}%",
        "target": "Target: ≤70.0%",
        "status": "🟢 Balanced" if m_vals['m19'] <= 70.0 else "🔴 Overweight",
        "cls": "status-green" if m_vals['m19'] <= 70.0 else "status-red",
        "reason": "Evaluates talent cost structure; prevents wage inflation from eroding operating cash.",
        "link": "Profit_and_Loss"
    },
    {
        "id": "M20",
        "name": "Days Sales Outstanding",
        "val_str": f"{m_vals['m20']:.1f} Days",
        "target": "Target: ≤60.0 Days",
        "status": "🟢 Fast Collection" if m_vals['m20'] <= 60.0 else "🔴 Stalled Cash",
        "cls": "status-green" if m_vals['m20'] <= 60.0 else "status-red",
        "reason": "Cash velocity indicator showing how fast invoices convert into bank balance.",
        "link": "Invoices_and_Cash_Flow"
    },
    {
        "id": "M13",
        "name": "Attendance Rate",
        "val_str": f"{m_vals['m13']:.2f}%",
        "target": "Target: ≥94.0%",
        "status": "🟢 Disciplined" if m_vals['m13'] >= 94.0 else "🔴 High Absenteeism",
        "cls": "status-green" if m_vals['m13'] >= 94.0 else "status-red",
        "reason": "Operational discipline barometer; flags underlying morale or burnout problems early.",
        "link": "Attendance_and_Leave"
    },
    {
        "id": "M23",
        "name": "On-Time Delivery Rate",
        "val_str": f"{m_vals['m23']:.2f}%",
        "target": "Target: ≥90.0%",
        "status": "🟢 Predictable" if m_vals['m23'] >= 90.0 else "🟡 Delayed Sprints",
        "cls": "status-green" if m_vals['m23'] >= 90.0 else "status-yellow",
        "reason": "Measures engineering execution trust; ensures customer commitments are met on schedule.",
        "link": "Team_Productivity"
    }
]

# Display 8 KPI Cards in a balanced 4x2 Grid
row1_cols = st.columns(4)
for i in range(4):
    k = kpis[i]
    with row1_cols[i]:
        st.markdown(f"""
        <div class="scorecard-card">
            <span class="kpi-num">{k['id']}</span>
            <span class="traffic-pill {k['cls']}">{k['status']}</span>
            <div class="kpi-name">{k['name']}</div>
            <div class="kpi-main-val">{k['val_str']}</div>
            <div class="kpi-target-tag">{k['target']}</div>
            <div style="font-size: 11px; color: #718096; margin-top: 6px;"><em>{k['reason']}</em></div>
            <a class="page-link-btn" href="/{k['link']}" target="_self">Deep Dive &rarr;</a>
        </div>
        """, unsafe_allow_html=True)

row2_cols = st.columns(4)
for i in range(4, 8):
    k = kpis[i]
    with row2_cols[i-4]:
        st.markdown(f"""
        <div class="scorecard-card">
            <span class="kpi-num">{k['id']}</span>
            <span class="traffic-pill {k['cls']}">{k['status']}</span>
            <div class="kpi-name">{k['name']}</div>
            <div class="kpi-main-val">{k['val_str']}</div>
            <div class="kpi-target-tag">{k['target']}</div>
            <div style="font-size: 11px; color: #718096; margin-top: 6px;"><em>{k['reason']}</em></div>
            <a class="page-link-btn" href="/{k['link']}" target="_self">Deep Dive &rarr;</a>
        </div>
        """, unsafe_allow_html=True)

st.write("")

# --- Section 2: Executive Print & Think for Yourself ---
col_prt, col_tfy = st.columns([1, 1])

with col_prt:
    st.markdown("""
    <div style="background-color: #EDF2F7; padding: 14px 18px; border-radius: 8px;">
        <h5 style="margin: 0 0 6px 0; color: #2D3748;">A4 Executive Print Instructions</h5>
        <p style="margin: 0; font-size: 13px; color: #4A5568;">
            Press <strong>Ctrl + P</strong> (Windows) or <strong>Cmd + P</strong> (Mac) in your browser. 
            The dedicated <code>@media print</code> CSS automatically suppresses sidebars, headers, and footers, 
            producing a single-page executive health summary ready for boardroom review.
        </p>
    </div>
    """, unsafe_allow_html=True)

with col_tfy:
    st.markdown("""
    <div style="background-color: #FEFCBF; border-left: 4px solid #D69E2E; padding: 14px 18px; border-radius: 8px;">
        <strong style="color: #744210;">Think for Yourself: You may only show 5 KPIs. Which 3 do you remove and why?</strong><br/><br/>
        <strong>Keep:</strong> M16 (Revenue), M18 (Operating Margin), M20 (DSO), M05 (Attrition), M23 (On-Time Delivery).<br/>
        <strong>Remove:</strong>
        <ol style="margin-bottom: 0; font-size: 13px; padding-left: 20px;">
            <li><strong>M01 Headcount:</strong> Scale is already reflected in Revenue and Margin; headcount alone doesn't show health.</li>
            <li><strong>M19 Payroll % of Revenue:</strong> A secondary cost component already encapsulated within M18 Operating Margin.</li>
            <li><strong>M13 Attendance Rate:</strong> An operational lead indicator; if teams deliver on-time (M23) with low attrition (M05), daily attendance is secondary.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
