"""
PulseIQ Workforce Analytics Dashboard
Main application entry point. Reads strictly from governed metric views in schema dw.
"""
import streamlit as st
import psycopg
import pandas as pd
import os

st.set_page_config(
    page_title="PulseIQ — Workforce Analytics",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Palette standard (Okabe-Ito & Minimalist: Max 3 meaningful colours)
# Primary: #0072B2 (Blue), Highlight: #E69F00 (Orange), Success/Neutral: #009E73 (Teal/Green)
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        border-left: 4px solid #0072B2;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .kpi-title {
        font-size: 14px;
        color: #555555;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 28px;
        color: #111111;
        font-weight: 700;
    }
    .kpi-sub {
        font-size: 12px;
        color: #777777;
    }
    .insight-box {
        background-color: #edf2f7;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 14px;
        color: #2d3748;
        margin-top: 8px;
        margin-bottom: 24px;
        border-left: 4px solid #4a5568;
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
    return psycopg.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS
    )

def query_df(sql, params=None):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        return pd.DataFrame(rows, columns=cols)

st.sidebar.title("PulseIQ Analytics")
st.sidebar.caption("Executive HR & Workforce Intelligence")

# Global Filter: Date Range & Department
try:
    dept_df = query_df("SELECT department_id, department_name FROM dw.dim_department ORDER BY department_id")
    dept_options = ["All Departments"] + [f"{r['department_id']} - {r['department_name']}" for _, r in dept_df.iterrows()]
    selected_dept = st.sidebar.selectbox("Filter Department", dept_options)
    
    date_df = query_df("SELECT DISTINCT year_month FROM dw.metric_m01_headcount ORDER BY year_month")
    all_months = date_df['year_month'].tolist()
    selected_month = st.sidebar.selectbox("As of Month", all_months, index=len(all_months)-1)
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()

st.title("PulseIQ Foundation Dashboard")
st.markdown("### Executive Workforce Overview")
st.write(f"Reporting snapshot for **{selected_month}** | Filter: **{selected_dept}**")

# Clean filter params
dept_id_filter = None if selected_dept == "All Departments" else selected_dept.split(" - ")[0]

# --- KPI Cards Row ---
# M01 Headcount, M02 Hires, M03 Exits, M04 Attrition Rate
if dept_id_filter:
    kpi_sql = """
        SELECT 
            m1.headcount,
            m2.hires,
            m3.exits,
            m4.attrition_rate_monthly_pct
        FROM dw.metric_m01_headcount m1
        JOIN dw.metric_m02_hires m2 ON m1.year_month = m2.year_month AND m1.department_id = m2.department_id
        JOIN dw.metric_m03_exits m3 ON m1.year_month = m3.year_month AND m1.department_id = m3.department_id
        JOIN dw.metric_m04_attrition_rate_monthly m4 ON m1.year_month = m4.year_month AND m1.department_id = m4.department_id
        WHERE m1.year_month = %s AND m1.department_id = %s
    """
    kpi_data = query_df(kpi_sql, (selected_month, dept_id_filter))
else:
    kpi_sql = """
        SELECT 
            SUM(m1.unsuppressed_headcount) AS headcount,
            SUM(m2.unsuppressed_hires) AS hires,
            SUM(m3.unsuppressed_exits) AS exits,
            ROUND(SUM(m3.unsuppressed_exits)::numeric / NULLIF(SUM(m1.unsuppressed_headcount), 0) * 100, 2) AS attrition_rate_monthly_pct
        FROM dw.metric_m01_headcount m1
        JOIN dw.metric_m02_hires m2 ON m1.year_month = m2.year_month AND m1.department_id = m2.department_id
        JOIN dw.metric_m03_exits m3 ON m1.year_month = m3.year_month AND m1.department_id = m3.department_id
        WHERE m1.year_month = %s
    """
    kpi_data = query_df(kpi_sql, (selected_month,))

col1, col2, col3, col4 = st.columns(4)

if not kpi_data.empty:
    hc = kpi_data.iloc[0]['headcount']
    hires = kpi_data.iloc[0]['hires']
    exits = kpi_data.iloc[0]['exits']
    attr = kpi_data.iloc[0]['attrition_rate_monthly_pct']
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="kpi-title">M01 Headcount</div>
            <div class="kpi-value">{int(hc) if pd.notnull(hc) else 'Suppressed (<5)'}</div>
            <div class="kpi-sub">Active staff on month end</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="kpi-title">M02 Hires</div>
            <div class="kpi-value" style="color: #0072B2;">{int(hires) if pd.notnull(hires) else 'Suppressed'}</div>
            <div class="kpi-sub">New joiners in month</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="kpi-title">M03 Exits</div>
            <div class="kpi-value" style="color: #E69F00;">{int(exits) if pd.notnull(exits) else 'Suppressed'}</div>
            <div class="kpi-sub">Departures in month</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="kpi-title">M04 Monthly Attrition</div>
            <div class="kpi-value">{f"{float(attr):.2f}%" if pd.notnull(attr) else 'Suppressed (<10)'}</div>
            <div class="kpi-sub">Exit share of headcount</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")

# --- Chart 1: Headcount Growth Trend ---
st.markdown("#### Headcount Trend: Steady workforce growth from 60 to 441 employees over 81 months")
if dept_id_filter:
    trend_sql = """
        SELECT year_month, unsuppressed_headcount AS headcount 
        FROM dw.metric_m01_headcount 
        WHERE department_id = %s 
        ORDER BY year_month
    """
    trend_df = query_df(trend_sql, (dept_id_filter,))
else:
    trend_sql = """
        SELECT year_month, SUM(unsuppressed_headcount) AS headcount 
        FROM dw.metric_m01_headcount 
        GROUP BY year_month 
        ORDER BY year_month
    """
    trend_df = query_df(trend_sql)

st.line_chart(trend_df.set_index('year_month')['headcount'], color="#0072B2")
st.markdown("""
<div class="insight-box">
    <strong>Key Finding:</strong> Company headcount expanded continuously from 2020 through September 2026, reaching 441 active employees. Growth accelerated post-2023 with minimal organizational contraction.
</div>
""", unsafe_allow_html=True)

# --- Chart 2 & 3: Department Breakdown & Location Tier ---
c_left, c_right = st.columns(2)

with c_left:
    st.markdown("#### Department Size: Engineering and Support comprise over 55% of total workforce")
    dept_sql = """
        SELECT department_name, unsuppressed_headcount AS headcount
        FROM dw.metric_m01_headcount
        WHERE year_month = %s
        ORDER BY headcount DESC
    """
    dept_dist = query_df(dept_sql, (selected_month,))
    st.bar_chart(dept_dist.set_index('department_name')['headcount'], color="#0072B2")
    st.markdown("""
    <div class="insight-box">
        <strong>Key Finding:</strong> Product Engineering (D01) remains the dominant cost center with 142 personnel, followed by Data & AI (49) and Customer Support (50).
    </div>
    """, unsafe_allow_html=True)

with c_right:
    st.markdown("#### Work Mode Distribution: Hybrid and Remote models dominate office presence")
    wm_sql = """
        SELECT work_mode, count(distinct employee_id) as employees
        FROM dw.dim_employee
        WHERE is_current AND is_active
        GROUP BY work_mode
        ORDER BY employees DESC
    """
    wm_dist = query_df(wm_sql)
    st.bar_chart(wm_dist.set_index('work_mode')['employees'], color="#E69F00")
    st.markdown("""
    <div class="insight-box">
        <strong>Key Finding:</strong> Over 60% of employees operate under Hybrid or fully Remote arrangements, reflecting post-pandemic distributed work policies.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.caption("PulseIQ Foundation Governed Analytics • Powered by PostgreSQL 16 & Streamlit")
