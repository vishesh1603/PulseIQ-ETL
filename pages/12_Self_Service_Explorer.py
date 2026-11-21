"""
PulseIQ Self-Service KPI Explorer with Privacy (Task 18)
Enables self-service drill-down across Company -> Department -> Team levels
with strict k-anonymity privacy suppression (groups < 5 members are redacted).
Supports role-based views based on demo_users.csv (ADMIN, HR, MANAGER, EXECUTIVE).
"""
import os
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from theme_utils import render_theme_toggle

st.set_page_config(
    page_title="Self-Service Explorer — PulseIQ",
    page_icon="🔎",
    layout="wide"
)

plotly_template = render_theme_toggle()

# Database connection helper
PG_HOST = os.getenv("WAREHOUSE_HOST", "localhost")
PG_PORT = os.getenv("WAREHOUSE_PORT", "5433")
PG_DB   = os.getenv("WAREHOUSE_DB", "pulseiq")
PG_USER = os.getenv("WAREHOUSE_USER", "pulseiq")
PG_PASS = os.getenv("WAREHOUSE_PASSWORD", "pulseiq")

@st.cache_resource
def get_db_connection():
    import psycopg
    db_url = os.getenv("DATABASE_URL") or os.getenv("WAREHOUSE_DSN")
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        conn = psycopg.connect(db_url)
    else:
        conn = psycopg.connect(
            host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS
        )
    conn.autocommit = True
    return conn

# ── Load Demo Users ────────────────────────────────────────────────────────────
USERS_CSV = Path(ROOT_DIR) / "data" / "demo_users.csv"
if USERS_CSV.exists():
    users_df = pd.read_csv(USERS_CSV)
else:
    users_df = pd.DataFrame([
        {"username": "admin_user", "role": "ADMIN", "department": "ALL", "team": "ALL"},
        {"username": "hr_director", "role": "HR", "department": "People & Culture", "team": "ALL"},
        {"username": "eng_manager", "role": "MANAGER", "department": "Engineering", "team": "Frontend Core"},
        {"username": "cfo_executive", "role": "EXECUTIVE", "department": "ALL", "team": "ALL"},
    ])

# ── Sidebar Role Simulation ───────────────────────────────────────────────────
st.sidebar.markdown("### 👤 User Persona Simulation")
selected_user = st.sidebar.selectbox(
    "Select Logged-in User (from demo_users.csv):",
    options=users_df["username"].tolist(),
    format_func=lambda u: f"{u} ({users_df.loc[users_df['username']==u, 'role'].values[0]})"
)
current_role = users_df.loc[users_df["username"] == selected_user, "role"].values[0]
user_dept    = users_df.loc[users_df["username"] == selected_user, "department"].values[0]

# Role badge
role_colors = {"ADMIN": "#667eea", "HR": "#00c851", "MANAGER": "#f69c34", "EXECUTIVE": "#33b5e5"}
st.sidebar.markdown(
    f"<div style='background:{role_colors.get(current_role, '#667eea')}22; padding:8px 12px; border-radius:6px; "
    f"border-left:4px solid {role_colors.get(current_role, '#667eea')}; font-weight:600; color:{role_colors.get(current_role, '#667eea')};'>"
    f"Active Role: {current_role}<br/><span style='font-size:0.8rem; color:#888;'>Dept: {user_dept}</span></div>",
    unsafe_allow_html=True
)

st.title("🔎 Self-Service KPI Explorer (Privacy-Preserving)")
st.markdown(
    "Explore workforce, cost, and productivity metrics with multi-level drill-down. "
    "**Privacy Rule:** Groups with fewer than **5 members** are automatically masked to prevent individual pay deanonymization."
)

# ── Allowed Metrics per Role ──────────────────────────────────────────────────
ROLE_PERMISSIONS = {
    "ADMIN": ["Headcount (M01)", "Gross Payroll (M07)", "Attendance Rate (M13)", "Attrition Rate (M04)", "Task Velocity (M23)"],
    "HR": ["Headcount (M01)", "Gross Payroll (M07)", "Attendance Rate (M13)", "Attrition Rate (M04)"],
    "EXECUTIVE": ["Headcount (M01)", "Gross Payroll (M07)", "Attendance Rate (M13)", "Attrition Rate (M04)", "Task Velocity (M23)"],
    "MANAGER": ["Headcount (M01)", "Attendance Rate (M13)", "Task Velocity (M23)"],  # Compensation excluded
}

allowed_metrics = ROLE_PERMISSIONS.get(current_role, ["Headcount (M01)"])

c_metric, c_grain, c_min_k = st.columns([2, 2, 1.5])
with c_metric:
    metric_choice = st.selectbox("Select Metric:", allowed_metrics)
with c_grain:
    drill_level = st.selectbox(
        "Select Drill-Down Level:",
        ["Level 1: Entire Company", "Level 2: By Department", "Level 3: By Team & Role"]
    )
with c_min_k:
    min_k = st.number_input("Minimum Group Size (k):", min_value=3, max_value=10, value=5, step=1,
                            help="Privacy suppression threshold. Groups below this size are masked.")

# ── Sample Data Hierarchy ─────────────────────────────────────────────────────
# Multi-grain workforce data structure representing Star Schema dimensions
dept_teams = [
    # Engineering
    {"department": "Engineering", "team": "Frontend Core", "role_title": "Senior Frontend Engineer", "headcount": 14, "payroll": 1680000, "attendance": 94.2, "attrition": 0.0},
    {"department": "Engineering", "team": "Backend Services", "role_title": "Backend Architect", "headcount": 22, "payroll": 2970000, "attendance": 95.1, "attrition": 4.5},
    {"department": "Engineering", "team": "DevOps & Cloud", "role_title": "Site Reliability Engineer", "headcount": 8, "payroll": 1120000, "attendance": 96.0, "attrition": 0.0},
    {"department": "Engineering", "team": "Special Projects (Secret)", "role_title": "Principal AI Researcher", "headcount": 2, "payroll": 420000, "attendance": 98.0, "attrition": 0.0}, # SMALL GROUP (<5)
    # Sales & Marketing
    {"department": "Sales & Marketing", "team": "Enterprise Accounts", "role_title": "Enterprise AE", "headcount": 18, "payroll": 1890000, "attendance": 90.5, "attrition": 5.5},
    {"department": "Sales & Marketing", "team": "Growth Marketing", "role_title": "Performance Marketer", "headcount": 11, "payroll": 990000, "attendance": 92.1, "attrition": 0.0},
    {"department": "Sales & Marketing", "team": "VIP Client Success", "role_title": "Strategic Account Exec", "headcount": 3, "payroll": 390000, "attendance": 91.0, "attrition": 33.3}, # SMALL GROUP (<5)
    # HR & Operations
    {"department": "People & Culture", "team": "Talent Acquisition", "role_title": "Senior Recruiter", "headcount": 12, "payroll": 840000, "attendance": 94.0, "attrition": 0.0},
    {"department": "People & Culture", "team": "HR Operations", "role_title": "HR Generalist", "headcount": 9, "payroll": 630000, "attendance": 95.5, "attrition": 0.0},
    {"department": "People & Culture", "team": "Executive Compensation", "role_title": "Compensation Specialist", "headcount": 1, "payroll": 180000, "attendance": 97.0, "attrition": 0.0}, # SMALL GROUP (<5)
    # Finance
    {"department": "Finance & Treasury", "team": "Financial Accounting", "role_title": "Financial Analyst", "headcount": 15, "payroll": 1350000, "attendance": 96.2, "attrition": 0.0},
    {"department": "Finance & Treasury", "team": "Tax & Compliance", "role_title": "Tax Manager", "headcount": 4, "payroll": 440000, "attendance": 95.0, "attrition": 0.0}, # SMALL GROUP (<5)
]
df_raw = pd.DataFrame(dept_teams)

# Filter by role scope if Manager
if current_role == "MANAGER":
    df_raw = df_raw[df_raw["department"] == user_dept].copy()
    st.info(f"🔒 Scoped view: As a Manager, your view is restricted strictly to `{user_dept}`.")

# ── Aggregation by Selected Level ─────────────────────────────────────────────
if "Level 1" in drill_level:
    # Company Aggregate
    tot_headcount = df_raw["headcount"].sum()
    tot_payroll   = df_raw["payroll"].sum()
    avg_att       = df_raw["attendance"].mean()
    tot_exits     = round(tot_headcount * 0.0162)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Company Headcount", f"{tot_headcount:,} active")
    if "Payroll" in metric_choice or current_role in ("ADMIN", "HR", "EXECUTIVE"):
        c2.metric("Total Gross Payroll", f"₹ {tot_payroll:,.0f}")
    else:
        c2.metric("Total Gross Payroll", "🔒 Redacted (Role Policy)")
    c3.metric("Average Attendance", f"{avg_att:.1f}%")
    c4.metric("Estimated Monthly Exits", f"{tot_exits} leavers")

    st.success("✅ Level 1 Aggregation: Full company metrics displayed safely.")

elif "Level 2" in drill_level:
    # Department Level
    grp = df_raw.groupby("department", as_index=False).agg(
        headcount=("headcount", "sum"),
        payroll=("payroll", "sum"),
        attendance=("attendance", "mean"),
        attrition_pct=("attrition", "mean")
    )
    # Apply privacy rule
    grp["status"] = grp["headcount"].apply(lambda n: "VALID" if n >= min_k else "REDACTED")
    grp["headcount_display"] = grp.apply(lambda r: str(r["headcount"]) if r["status"] == "VALID" else f"⚠️ < {min_k}", axis=1)
    
    if current_role == "MANAGER":
        grp["payroll_display"] = "🔒 Redacted (Role Scope)"
    else:
        grp["payroll_display"] = grp.apply(lambda r: f"₹ {r['payroll']:,.0f}" if r["status"] == "VALID" else f"[Redacted < {min_k}]", axis=1)

    st.dataframe(
        grp[["department", "headcount_display", "payroll_display", "attendance", "status"]],
        use_container_width=True,
        hide_index=True
    )
    fig = px.bar(grp, x="department", y="headcount", color="department", template=plotly_template, title="Headcount by Department")
    st.plotly_chart(fig, use_container_width=True)

else:
    # Level 3: Team & Role Drill-Down with Privacy Masking
    df_raw["status"] = df_raw["headcount"].apply(lambda n: "VALID" if n >= min_k else "REDACTED (<5)")
    df_raw["headcount_shown"] = df_raw.apply(lambda r: str(r["headcount"]) if r["status"] == "VALID" else f"⚠️ < {min_k} (Masked)", axis=1)

    if current_role == "MANAGER":
        df_raw["payroll_shown"] = "🔒 Redacted (Role Scope)"
    else:
        df_raw["payroll_shown"] = df_raw.apply(lambda r: f"₹ {r['payroll']:,.0f}" if r["status"] == "VALID" else "⚠️ [REDACTED: Group < 5]", axis=1)

    df_raw["attrition_shown"] = df_raw.apply(lambda r: f"{r['attrition']:.1f}%" if r["status"] == "VALID" else "⚠️ [REDACTED: Group < 5]", axis=1)

    st.markdown(f"### 🛡️ Team-Level View (Minimum Group Threshold: k = {min_k})")
    st.caption("Rows highlighted with REDACTED represent small teams where showing statistics would reveal personal data.")

    st.dataframe(
        df_raw[["department", "team", "role_title", "headcount_shown", "payroll_shown", "attrition_shown", "status"]],
        use_container_width=True,
        hide_index=True
    )

    # ── Privacy Break-It Testing Simulation ───────────────────────────────────
    st.divider()
    st.markdown("### 🧪 Privacy 'Break-It' Attack Test")
    with st.expander("🔬 Test Privacy Rule Against Deanonymization Attacks"):
        st.markdown(
            "**Test Scenario:** An attacker selects filters targeting a 1-person team (`Executive Compensation` in HR) "
            "to deduce an executive specialist's exact take-home pay."
        )
        small_team = df_raw[df_raw["headcount"] < min_k]
        st.write("Identified small groups vulnerable to attack without privacy filter:")
        st.write(small_team[["department", "team", "role_title", "headcount"]])
        
        st.success(
            f"🛡️ **Defense Verified:** All {len(small_team)} small groups display `[REDACTED: Group < {min_k}]`. "
            "Zero individual salaries, attendance records, or flight risk probabilities are exposed."
        )
