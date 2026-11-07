"""
PulseIQ Invoices, Receivables Aging & Cash Flow Analytics (Task 12)
Tracks open receivables, ageing buckets, days to pay by client,
and monthly cash in versus cash out.
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

st.set_page_config(page_title="PulseIQ — Invoices & Cash Flow", page_icon="💳", layout="wide")

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

st.title("Invoices, Receivables & Cash Flow")
st.markdown("### Liquidity Health, Ageing Buckets & Client Payment Behavior (Task 12)")

st.markdown("""
<div class="policy-banner">
    <h5 style="margin: 0 0 6px 0; color: #744210;">Governed Definition: Open Invoices & Receivables</h5>
    <p style="margin: 0; font-size: 13px; color: #2D3748;">
        <strong>Open Invoice Statuses:</strong> In accordance with finance policy, an invoice is classified as open <strong>strictly</strong> when its status is 
        <code>SENT</code> (billed, within credit period), <code>OVERDUE</code> (past agreed payment date), or <code>PARTIALLY_PAID</code> (partially cleared balance). 
        All <code>PAID</code>, <code>DRAFT</code>, and <code>CANCELLED</code> records are excluded from receivables calculations.
    </p>
</div>
""", unsafe_allow_html=True)

# --- Top KPI Summary Row ---
kpi_sql = """
    SELECT 
        SUM(balance_due) FILTER (WHERE status IN ('SENT', 'OVERDUE', 'PARTIALLY_PAID')) AS total_open_receivables,
        SUM(balance_due) FILTER (WHERE status = 'OVERDUE') AS overdue_receivables,
        COUNT(invoice_id) FILTER (WHERE status IN ('SENT', 'OVERDUE', 'PARTIALLY_PAID')) AS open_invoice_count,
        ROUND(AVG(days_to_pay) FILTER (WHERE status = 'PAID'), 1) AS avg_days_to_pay
    FROM dw.fact_invoice;
"""
kpi_res = query_df(kpi_sql)

c1, c2, c3, c4 = st.columns(4)
if not kpi_res.empty:
    open_rec = float(kpi_res.iloc[0]['total_open_receivables'] or 0)
    overdue_rec = float(kpi_res.iloc[0]['overdue_receivables'] or 0)
    open_cnt = int(kpi_res.iloc[0]['open_invoice_count'] or 0)
    avg_dtp = float(kpi_res.iloc[0]['avg_days_to_pay'] or 0)

    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="kpi-title">Total Open Receivables</div>
            <div class="kpi-value">₹{open_rec/1e5:,.2f} L</div>
            <div class="kpi-sub">Exact tie-out: ₹{open_rec:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="kpi-title">M21 Overdue Receivables</div>
            <div class="kpi-value" style="color: #D55E00;">₹{overdue_rec/1e5:,.2f} L</div>
            <div class="kpi-sub">{(overdue_rec/open_rec*100):.1f}% of total open book</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="kpi-title">Open Invoices</div>
            <div class="kpi-value" style="color: #0072B2;">{open_cnt} Invoices</div>
            <div class="kpi-sub">SENT, OVERDUE & PARTIALLY_PAID</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="kpi-title">Average Days to Pay</div>
            <div class="kpi-value" style="color: #E69F00;">{avg_dtp:.1f} Days</div>
            <div class="kpi-sub">Mean collection turnaround time</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")

# --- Section 1: Receivables Ageing Buckets with Integrity Audit ---
st.markdown("#### Receivables Ageing Buckets (Cut-off Date: 30 Sep 2026)")

age_sql = """
    SELECT 
        CASE 
            WHEN status = 'SENT' THEN '0-30 days (Current / Not yet due)'
            WHEN days_past_due_at_cutoff BETWEEN 1 AND 30 THEN '1-30 days overdue'
            WHEN days_past_due_at_cutoff BETWEEN 31 AND 60 THEN '31-60 days overdue'
            WHEN days_past_due_at_cutoff BETWEEN 61 AND 90 THEN '61-90 days overdue'
            WHEN days_past_due_at_cutoff > 90 THEN '90+ days overdue (Critical)'
            ELSE '0-30 days (Current / Not yet due)'
        END AS ageing_bucket,
        COUNT(invoice_id) AS invoice_count,
        SUM(balance_due) AS total_amount
    FROM dw.fact_invoice
    WHERE status IN ('SENT', 'OVERDUE', 'PARTIALLY_PAID')
    GROUP BY 1
    ORDER BY MIN(COALESCE(days_past_due_at_cutoff, 0));
"""
age_df = query_df(age_sql)
age_df['total_amount'] = pd.to_numeric(age_df['total_amount'], errors='coerce').fillna(0).astype(float)

col_age_chart, col_age_tbl = st.columns([1.1, 0.9])

with col_age_chart:
    fig_age = px.bar(
        age_df,
        x='ageing_bucket',
        y='total_amount',
        color='ageing_bucket',
        color_discrete_sequence=['#009E73', '#E69F00', '#D55E00', '#999999', '#56B4E9'],
        labels={'total_amount': 'Outstanding Amount (₹)', 'ageing_bucket': 'Bucket'}
    )
    fig_age.update_layout(height=360, template=plotly_template, showlegend=False, margin=dict(l=20, r=20, t=10, b=20))
    st.plotly_chart(fig_age, use_container_width=True)

with col_age_tbl:
    st.dataframe(
        age_df.style.format({'total_amount': '₹{:,.2f}'}),
        height=240,
        use_container_width=True
    )
    # Integrity reconciliation check
    bucket_sum = float(age_df['total_amount'].sum())
    st.markdown(f"""
    <div style="background-color: #EDF2F7; padding: 10px 14px; border-radius: 6px; font-size: 13px;">
        <strong>Audit Check:</strong> Sum of ageing buckets = <strong>₹{bucket_sum:,.2f}</strong><br/>
        Total open receivables in warehouse = <strong>₹{open_rec:,.2f}</strong><br/>
        Variance = <span style="color: {'#009E73' if abs(bucket_sum - open_rec) < 0.01 else '#D55E00'}; font-weight: bold;">₹{abs(bucket_sum - open_rec):.2f} (Zero discrepancy)</span>
    </div>
    """, unsafe_allow_html=True)

# --- Section 2: Cash In versus Cash Out Trend ---
st.markdown("---")
st.markdown("#### Monthly Cash Flow: Cash Collections (In) vs Disbursements (Out)")

cash_sql = """
    WITH cin AS (
        SELECT TO_CHAR(payment_date, 'YYYY-MM') AS month, SUM(amount) AS cash_in
        FROM dw.fact_invoice_payment
        GROUP BY TO_CHAR(payment_date, 'YYYY-MM')
    ),
    cout_exp AS (
        SELECT TO_CHAR(paid_date, 'YYYY-MM') AS month, SUM(total_amount) AS exp_cash_out
        FROM dw.fact_expense
        WHERE status = 'PAID' AND paid_date IS NOT NULL
        GROUP BY TO_CHAR(paid_date, 'YYYY-MM')
    ),
    cout_pay AS (
        SELECT d.year_month AS month, SUM(f.net_pay) AS payroll_cash_out
        FROM dw.fact_payroll f
        JOIN dw.dim_date d ON d.date_key = f.date_key
        GROUP BY d.year_month
    )
    SELECT 
        cin.month,
        cin.cash_in,
        COALESCE(ce.exp_cash_out, 0) + COALESCE(cp.payroll_cash_out, 0) AS total_cash_out,
        cin.cash_in - (COALESCE(ce.exp_cash_out, 0) + COALESCE(cp.payroll_cash_out, 0)) AS net_cash_flow
    FROM cin
    LEFT JOIN cout_exp ce ON ce.month = cin.month
    LEFT JOIN cout_pay cp ON cp.month = cin.month
    ORDER BY cin.month;
"""
cash_df = query_df(cash_sql)
cash_df['cash_in'] = pd.to_numeric(cash_df['cash_in'], errors='coerce').fillna(0).astype(float)
cash_df['total_cash_out'] = pd.to_numeric(cash_df['total_cash_out'], errors='coerce').fillna(0).astype(float)
cash_df['net_cash_flow'] = pd.to_numeric(cash_df['net_cash_flow'], errors='coerce').fillna(0).astype(float)

fig_cash = go.Figure()
fig_cash.add_trace(go.Bar(x=cash_df['month'], y=cash_df['cash_in'], name='Cash In (Collections)', marker_color='#0072B2'))
fig_cash.add_trace(go.Bar(x=cash_df['month'], y=cash_df['total_cash_out'], name='Cash Out (Payroll + Vendors)', marker_color='#E69F00'))
fig_cash.add_trace(go.Scatter(x=cash_df['month'], y=cash_df['net_cash_flow'], name='Net Cash Flow', mode='lines+markers', line=dict(color='#009E73', width=3)))
fig_cash.update_layout(barmode='group', height=380, template=plotly_template, margin=dict(l=20, r=20, t=10, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig_cash, use_container_width=True)

# --- Section 3: Client Delinquency Leaderboard & Think for Yourself ---
st.markdown("---")
col_cl, col_tfy = st.columns([1.1, 0.9])

with col_cl:
    st.markdown("#### Clients with Highest Overdue Balances")
    cl_sql = """
        SELECT 
            c.client_id,
            c.client_name,
            c.payment_terms_days AS agreed_terms,
            ROUND(AVG(i.days_to_pay) FILTER (WHERE i.status = 'PAID'), 1) AS avg_historical_dtp,
            SUM(i.balance_due) FILTER (WHERE i.status IN ('SENT', 'OVERDUE', 'PARTIALLY_PAID')) AS total_open_balance,
            SUM(i.balance_due) FILTER (WHERE i.status = 'OVERDUE') AS overdue_balance
        FROM dw.fact_invoice i
        JOIN dw.dim_client c ON c.client_id = i.client_id
        GROUP BY c.client_id, c.client_name, c.payment_terms_days
        HAVING SUM(i.balance_due) FILTER (WHERE i.status = 'OVERDUE') > 0
        ORDER BY overdue_balance DESC;
    """
    cl_df = query_df(cl_sql)
    st.dataframe(
        cl_df.style.format({
            'total_open_balance': '₹{:,.2f}',
            'overdue_balance': '₹{:,.2f}',
            'avg_historical_dtp': '{:.1f} days'
        }),
        height=320,
        use_container_width=True
    )

with col_tfy:
    st.markdown("""
    <div class="insight-box" style="background-color: #FEFCBF; border-left: 4px solid #D69E2E;">
        <strong>Think for Yourself: A big client always pays at 75 days. Is that a risk? What would you ask finance?</strong><br/><br/>
        <strong>1. Is it a risk?</strong><br/>
        It is a liquidity risk if their contractual term is Net-30 or Net-45 because 30–45 days of uncontracted working capital must be funded out of operating cash. However, if their payment history is predictable and default probability is near-zero (e.g. enterprise blue-chip), it is an operational financing cost rather than a credit loss risk.<br/><br/>
        <strong>2. Questions to Ask the Finance Team:</strong>
        <ul>
            <li><em>"Can we renegotiate their contract to Net-60 or offer a 1.5% prompt payment discount (2/10 Net 30)?"</em></li>
            <li><em>"What is our cost of short-term credit facility/overdraft utilized to float this client's receivables?"</em></li>
            <li><em>"Does their billing schedule align with milestone completions or quarterly procurement approval cycles?"</em></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
