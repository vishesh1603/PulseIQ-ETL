"""
Page 11 — Alert History (Task 18)
KPI breach log and alerting status dashboard.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from theme_utils import apply_theme, get_theme_colors

apply_theme()
colors = get_theme_colors()

st.set_page_config(
    page_title="Alert History — PulseIQ",
    page_icon="🚨",
    layout="wide",
)

PG_CONN = os.getenv("WAREHOUSE_DSN", "postgresql://pulseiq:pulseiq@localhost:5433/pulseiq")

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.alert-critical { background: linear-gradient(135deg,#2d0a0a,#1a0505);
    border-left:4px solid #ff4b4b; padding:12px 16px; border-radius:8px;
    color:#ff8080; font-weight:600; margin-bottom:8px; }
.alert-warning  { background: linear-gradient(135deg,#2d2200,#1a1400);
    border-left:4px solid #ffcc00; padding:12px 16px; border-radius:8px;
    color:#ffd966; font-weight:600; margin-bottom:8px; }
.metric-pill { display:inline-block; padding:2px 10px; border-radius:12px;
    font-size:0.8em; font-weight:700; margin:2px; }
.pill-critical { background:#ff4b4b22; color:#ff4b4b; border:1px solid #ff4b4b44; }
.pill-warning  { background:#ffcc0022; color:#ffcc00; border:1px solid #ffcc0044; }
.pill-ok       { background:#00c85122; color:#00c851; border:1px solid #00c85144; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("# 🚨 Alert History")
st.markdown("Real-time KPI breach monitoring. Alerts are generated after each ETL run.")

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_alerts() -> pd.DataFrame:
    try:
        import psycopg
        conn = psycopg.connect(PG_CONN)
        df = pd.read_sql(
            """
            SELECT alert_id, metric_code, metric_name, current_value,
                   target_value, severity, breach_month, channel_used,
                   delivered_at
            FROM dw.alert_log
            ORDER BY delivered_at DESC
            LIMIT 500
            """,
            conn,
        )
        conn.close()
        return df
    except Exception as exc:
        return pd.DataFrame()


@st.cache_data(ttl=60)
def load_last_run_info() -> dict:
    log_path = PROJECT_ROOT / "logs" / "last_run.json"
    if log_path.exists():
        try:
            return json.loads(log_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


@st.cache_data(ttl=60)
def load_scheduler_log() -> list[dict]:
    sched_path = PROJECT_ROOT / "logs" / "scheduler.log"
    entries = []
    if sched_path.exists():
        for line in sched_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
    return entries[-20:]  # last 20 entries


# ── Pipeline Health Banner ─────────────────────────────────────────────────────
last_run = load_last_run_info()
sched_log = load_scheduler_log()

col1, col2, col3, col4 = st.columns(4)
with col1:
    status = last_run.get("status", "UNKNOWN")
    icon = "✅" if status == "SUCCESS" else "❌" if status == "FAILED" else "⏳"
    st.metric("Last ETL Status", f"{icon} {status}")
with col2:
    started = last_run.get("started_at", "—")
    if started != "—":
        try:
            started = datetime.fromisoformat(started).strftime("%d %b %Y %H:%M")
        except Exception:
            pass
    st.metric("Last Run At", started)
with col3:
    duration = last_run.get("duration_seconds", None)
    st.metric("Duration", f"{duration:.1f}s" if duration else "—")
with col4:
    latest_sched = sched_log[-1] if sched_log else {}
    sched_status = latest_sched.get("status", "—")
    st.metric("Scheduler Status", sched_status)

st.divider()

# ── Re-run Alerting ───────────────────────────────────────────────────────────
col_btn, col_info = st.columns([1, 4])
with col_btn:
    if st.button("🔄 Re-run KPI Checks Now", type="primary", use_container_width=True,
                 key="rerun_alerts"):
        alerting_path = PROJECT_ROOT / "scripts" / "alerting.py"
        if alerting_path.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("alerting", alerting_path)
            mod = importlib.util.load_module_from_spec(spec)   # type: ignore
            spec.loader.exec_module(mod)                       # type: ignore
            with st.spinner("Running KPI checks…"):
                triggered = mod.run_all_kpi_checks()
            if triggered:
                st.warning(f"⚠️ {len(triggered)} KPI breach(es) detected and logged.")
            else:
                st.success("✅ All KPI checks passed — no breaches.")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("alerting.py not found in scripts/")

st.divider()

# ── Load Alert Data ───────────────────────────────────────────────────────────
df = load_alerts()

if df.empty:
    st.info(
        "No alerts in the database yet. "
        "Click **Re-run KPI Checks Now** above to run the first check, "
        "or ensure the ETL pipeline has run at least once."
    )
    st.stop()

# ── Summary Metrics ───────────────────────────────────────────────────────────
n_critical = (df["severity"] == "CRITICAL").sum()
n_warning  = (df["severity"] == "WARNING").sum()
n_total    = len(df)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Alerts (All Time)", n_total)
m2.metric("🔴 Critical", n_critical)
m3.metric("🟡 Warning", n_warning)
df_30d = df[pd.to_datetime(df["delivered_at"]) >= pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=30)]
m4.metric("Last 30 Days", len(df_30d))

st.divider()

# ── Filter Controls ───────────────────────────────────────────────────────────
col_f1, col_f2 = st.columns(2)
with col_f1:
    sel_sev = st.multiselect(
        "Filter by Severity", ["CRITICAL", "WARNING", "INFO"],
        default=["CRITICAL", "WARNING"], key="alert_sev_filter"
    )
with col_f2:
    days_back = st.slider("Show last N days", 7, 365, 30, key="alert_days_filter")

df_filtered = df.copy()
if sel_sev:
    df_filtered = df_filtered[df_filtered["severity"].isin(sel_sev)]
df_filtered["delivered_at"] = pd.to_datetime(df_filtered["delivered_at"], utc=True)
cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=days_back)
df_filtered = df_filtered[df_filtered["delivered_at"] >= cutoff]

# ── Breach Frequency Chart ─────────────────────────────────────────────────────
st.subheader("📊 Breach Frequency by Metric")
if not df_filtered.empty:
    freq = (
        df_filtered.groupby(["metric_code", "severity"])
        .size()
        .reset_index(name="count")
    )
    fig = px.bar(
        freq,
        x="metric_code",
        y="count",
        color="severity",
        color_discrete_map={"CRITICAL": "#ff4b4b", "WARNING": "#ffcc00", "INFO": "#4b9eff"},
        labels={"metric_code": "Metric", "count": "Breaches", "severity": "Severity"},
        title=f"KPI Breaches — Last {days_back} Days",
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color=colors.get("text", "#ffffff"),
        legend_title_text="Severity",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No breaches in this date range.")

st.divider()

# ── Alert Log Table ───────────────────────────────────────────────────────────
st.subheader("🗂️ Alert Log Detail")

if not df_filtered.empty:
    display_df = df_filtered[[
        "delivered_at", "severity", "metric_code", "metric_name",
        "current_value", "target_value", "breach_month", "channel_used"
    ]].copy()

    display_df["delivered_at"] = display_df["delivered_at"].dt.strftime("%Y-%m-%d %H:%M")
    display_df.columns = [
        "Alert Time", "Severity", "Code", "Metric Name",
        "Value", "Target", "Breach Month", "Channel"
    ]

    def _highlight(row):
        if row["Severity"] == "CRITICAL":
            return ["background-color: #2d0a0a"] * len(row)
        elif row["Severity"] == "WARNING":
            return ["background-color: #2d2200"] * len(row)
        return [""] * len(row)

    st.dataframe(
        display_df.style.apply(_highlight, axis=1),
        use_container_width=True,
        height=400,
    )
else:
    st.info("No alerts match the current filters.")

# ── Scheduler Log ─────────────────────────────────────────────────────────────
st.divider()
with st.expander("⚙️ Scheduler Heartbeat Log (last 20 entries)"):
    if sched_log:
        sched_df = pd.DataFrame(sched_log)
        st.dataframe(sched_df, use_container_width=True)
    else:
        st.info(
            "No scheduler heartbeat entries yet. "
            "Start the scheduler with: `python scripts/scheduler.py`"
        )

st.caption("PulseIQ Phase 4 — Task 18: KPI Alerting & Webhook Notifications")
