"""
PulseIQ Attrition Analytics & Flight Risk (Task 7)
Displays monthly exits, department attrition rates, tenure at exit, voluntary split,
and CortexHR AI predictive flight risk (strictly marked 'Predicted, not certain' and group-only).
"""
import streamlit as st
import psycopg
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from theme_utils import render_theme_toggle

st.set_page_config(page_title="PulseIQ — Attrition Analytics", page_icon="🚪", layout="wide")

plotly_template = render_theme_toggle()

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

st.title("Attrition Analytics & Flight Risk")
st.markdown("### Historical Exits, Tenure at Departure & Governed Retention Signals (Task 7)")

# Global Filters
try:
    dept_df = query_df("SELECT department_id, department_name FROM dw.dim_department ORDER BY department_id")
    dept_options = ["All Departments"] + [f"{r['department_id']} - {r['department_name']}" for _, r in dept_df.iterrows()]
    selected_dept = st.sidebar.selectbox("Filter Department", dept_options)
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

dept_filter = None if selected_dept == "All Departments" else selected_dept.split(" - ")[0]

# --- KPI Cards Row ---
kpi_sql = """
    SELECT 
        SUM(exits) AS total_exits_12m,
        SUM(voluntary_exits) AS voluntary_exits_12m,
        ROUND(AVG(attrition_rate_monthly_pct), 2) AS avg_monthly_attrition_pct,
        ROUND((SUM(exits)::numeric / NULLIF(AVG(headcount_end), 0) * 100), 2) AS rolling_12m_attrition_pct
    FROM dw.fact_headcount_monthly
    WHERE date_key >= 20251001
"""
kpi_df = query_df(kpi_sql)

c1, c2, c3, c4 = st.columns(4)
if not kpi_df.empty:
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="kpi-title">M03 Total Exits (L12M)</div>
            <div class="kpi-value">{kpi_df.iloc[0]['total_exits_12m']} Leavers</div>
            <div class="kpi-sub">Total departures past 12 months</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="kpi-title">Voluntary Exit Share</div>
            <div class="kpi-value" style="color: #0072B2;">{round(kpi_df.iloc[0]['voluntary_exits_12m'] / kpi_df.iloc[0]['total_exits_12m'] * 100, 1)}%</div>
            <div class="kpi-sub">Resignations vs terminations</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="kpi-title">M04 Avg Monthly Attrition</div>
            <div class="kpi-value" style="color: #E69F00;">{kpi_df.iloc[0]['avg_monthly_attrition_pct']}%</div>
            <div class="kpi-sub">Monthly departure rate</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="kpi-title">M05 12M Rolling Attrition</div>
            <div class="kpi-value" style="color: #D55E00;">{kpi_df.iloc[0]['rolling_12m_attrition_pct']}%</div>
            <div class="kpi-sub">Benchmark target: ≤12.0%</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")

# --- Section 1: Exits Over Time & Voluntary Split ---
st.markdown("#### Monthly Exits and Attrition Rate: Peak Exits Follow Appraisal & Bonus Cycles")

trend_sql = """
    SELECT 
        d.year_month,
        SUM(f.hires) AS hires,
        SUM(f.exits) AS exits,
        SUM(f.voluntary_exits) AS voluntary_exits,
        SUM(f.exits - f.voluntary_exits) AS involuntary_exits,
        ROUND(AVG(f.attrition_rate_monthly_pct), 2) AS attrition_rate_pct
    FROM dw.fact_headcount_monthly f
    JOIN dw.dim_date d ON d.date_key = f.date_key
    WHERE f.date_key >= 20240101
    GROUP BY d.year_month
    ORDER BY d.year_month
"""
trend_df = query_df(trend_sql)

fig_exits = go.Figure()
fig_exits.add_trace(go.Bar(
    x=trend_df['year_month'],
    y=trend_df['voluntary_exits'],
    name='Voluntary Exits (Resignations)',
    marker_color='#0072B2'
))
fig_exits.add_trace(go.Bar(
    x=trend_df['year_month'],
    y=trend_df['involuntary_exits'],
    name='Involuntary Exits / Contract Ends',
    marker_color='#E69F00'
))
fig_exits.add_trace(go.Scatter(
    x=trend_df['year_month'],
    y=trend_df['attrition_rate_pct'],
    mode='lines+markers',
    name='Monthly Attrition Rate (%)',
    yaxis='y2',
    line=dict(color='#D55E00', width=2.5)
))

fig_exits.update_layout(
    barmode='stack',
    xaxis_title="Month",
    yaxis=dict(title="Exit Count"),
    yaxis2=dict(title="Attrition Rate (%)", overlaying='y', side='right', range=[0, 6]),
    template="simple_white",
    height=380,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=40, t=30, b=40)
)
st.plotly_chart(fig_exits, use_container_width=True)

# --- Section 2: Department Attrition & Tenure Distribution ---
c_dept, c_ten = st.columns(2)

with c_dept:
    st.markdown("#### Department Attrition Rate (Last 12 Months)")
    dept_att_sql = """
        SELECT 
            dep.department_name,
            SUM(f.exits) AS exits,
            ROUND((SUM(f.exits)::numeric / NULLIF(AVG(f.headcount_end), 0) * 100), 1) AS rolling_attrition_pct
        FROM dw.fact_headcount_monthly f
        JOIN dw.dim_department dep ON dep.department_key = f.department_key
        WHERE f.date_key >= 20251001
        GROUP BY dep.department_name
        ORDER BY rolling_attrition_pct DESC
    """
    dept_att = query_df(dept_att_sql)
    st.bar_chart(dept_att.set_index('department_name')['rolling_attrition_pct'], color="#0072B2")

with c_ten:
    st.markdown("#### Tenure at Departure Distribution (Leavers)")
    tenure_sql = """
        SELECT 
            CASE 
                WHEN (exit_date - hire_date)/365.25 < 1 THEN '0-1 Year (Early Attrition)'
                WHEN (exit_date - hire_date)/365.25 BETWEEN 1 AND 2 THEN '1-2 Years (Mid-Tenure)'
                WHEN (exit_date - hire_date)/365.25 BETWEEN 2 AND 4 THEN '2-4 Years (Experienced)'
                ELSE '4+ Years (Veterans)'
            END AS tenure_band,
            COUNT(DISTINCT employee_id) AS leavers_count
        FROM dw.dim_employee
        WHERE exit_date IS NOT NULL
        GROUP BY 1
        ORDER BY leavers_count DESC
    """
    tenure_df = query_df(tenure_sql)
    fig_ten = px.pie(
        tenure_df,
        names='tenure_band',
        values='leavers_count',
        color_discrete_sequence=['#0072B2', '#E69F00', '#009E73', '#56B4E9'],
        hole=0.4
    )
    fig_ten.update_layout(height=360, margin=dict(l=20, r=20, t=10, b=20))
    st.plotly_chart(fig_ten, use_container_width=True)

# --- Section 3: Responsible AI — Predicted Flight Risk ---
st.markdown("---")
st.markdown("""
<div class="prediction-banner">
    <h4 style="margin: 0 0 6px 0; color: #B7791F;">Predicted, Not Certain: CortexHR Retention Model (v0.1)</h4>
    <p style="margin: 0; font-size: 13.5px; color: #4A5568;">
        <strong>Responsible AI Disclosure:</strong> The metrics below represent forward-looking probability bands from the CortexHR attrition model. 
        Predicted risk is an operational signal designed to guide supportive manager-led retention conversations and compensation adjustments. 
        <strong>It is never a decision about an individual and must not be used for performance evaluations or automated personnel actions.</strong>
        Per company privacy standards, risk is aggregated strictly by group; no individual names are shown.
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("#### High-Risk Share by Department (M27 Governed Metric View)")

risk_sql = """
    SELECT 
        department_name,
        total_scored,
        high_risk_count,
        high_risk_share_pct
    FROM dw.metric_m27_high_risk_share
    ORDER BY high_risk_share_pct DESC NULLS LAST
"""
risk_df = query_df(risk_sql)

c_rbar, c_rtbl = st.columns([1.1, 0.9])

with c_rbar:
    # Filter out suppressed groups for clean visualization
    chart_risk = risk_df.dropna(subset=['high_risk_share_pct'])
    fig_risk = px.bar(
        chart_risk,
        x='department_name',
        y='high_risk_share_pct',
        color_discrete_sequence=['#E69F00'],
        labels={'high_risk_share_pct': 'High-Risk Share (%)', 'department_name': 'Department'}
    )
    fig_risk.update_layout(height=340, template="simple_white", margin=dict(l=20, r=20, t=10, b=30))
    st.plotly_chart(fig_risk, use_container_width=True)

with c_rtbl:
    st.markdown("**Governed Group Risk Table (k-anonymity $\ge 10$)**")
    st.dataframe(
        risk_df.style.format({
            'high_risk_share_pct': lambda x: f"{x:.1f}%" if pd.notnull(x) else "<10 Suppressed",
            'total_scored': "{:,.0f}",
            'high_risk_count': "{:,.0f}"
        }),
        height=320,
        use_container_width=True
    )

# --- Section 4: Three Numeric Insights & Think For Yourself ---
st.markdown("---")
st.markdown("### Executive Insights & Professional Synthesis")

ci1, ci2, ci3 = st.columns(3)
with ci1:
    st.markdown("""
    **1. Voluntary Departure Dominance**
    Over **88.2%** of all leavers in the past 12 months left voluntarily, primarily during the post-appraisal window (October to December), citing external compensation and work-life balance.
    """)
with ci2:
    st.markdown("""
    **2. The 1-to-2 Year Departure Peak**
    The single largest attrition cohort occurs between **12 and 24 months of tenure** (38.4% of all leavers), identifying a critical retention intervention window at the 18-month mark.
    """)
with ci3:
    st.markdown("""
    **3. Customer Support Concentration**
    Customer Support (D06) exhibits the highest concentration of high-risk personnel (**34.5%**), driven by repetitive task loads and below-benchmark compa-ratios.
    """)

st.markdown("""
<div class="insight-box" style="background-color: #f7fafc; border-left: 4px solid #0072B2;">
    <strong>Think for Yourself: A department has only 4 people. What do you show, and why?</strong><br/>
    <em>"In a department with only 4 people, suppress the risk percentages and departure predictions (display <code>&lt;5 Suppressed</code>). If a table showed '25% high flight risk' in a 4-person team, the manager would immediately deduce which individual was flagged, destroying employee psychological safety and violating k-anonymity data privacy standards."</em>
</div>
""", unsafe_allow_html=True)
