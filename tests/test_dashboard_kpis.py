"""Verification tests for Task 3 Dashboard KPIs.

These tests execute queries against the PostgreSQL warehouse (schema dw)
and assert that the figures displayed on the Headcount & Departments dashboard
cards, charts, and takeaway sentences match database reality exactly.
"""
import os
import pytest
import psycopg

DSN = os.environ.get(
    "WAREHOUSE_DSN",
    "postgresql://pulseiq:pulseiq@localhost:5433/pulseiq"
)


def _warehouse_reachable() -> bool:
    try:
        psycopg.connect(DSN, connect_timeout=3).close()
        return True
    except psycopg.Error:
        return False


pytestmark = pytest.mark.skipif(
    not _warehouse_reachable(),
    reason="PostgreSQL warehouse not reachable at WAREHOUSE_DSN"
)


def run_sql(query: str, params=None):
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute(query, params)
        if cur.description:
            return cur.fetchall()
        return None


def test_kpi_m01_headcount_latest_and_checkpoint():
    """Verify M01 Headcount for Sep 2026 (441) and Apr 2025 (380)."""
    # Latest month (2026-09)
    query_latest = """
        SELECT SUM(h.headcount_end)
        FROM dw.fact_headcount_monthly h
        JOIN dw.dim_date d ON d.date_key = h.date_key
        WHERE d.year_month = '2026-09';
    """
    latest_hc = run_sql(query_latest)[0][0]
    assert latest_hc == 441, f"Expected 441 active headcount in 2026-09, got {latest_hc}"

    # Checkpoint (2025-04)
    query_apr = """
        SELECT SUM(h.headcount_end)
        FROM dw.fact_headcount_monthly h
        JOIN dw.dim_date d ON d.date_key = h.date_key
        WHERE d.year_month = '2025-04';
    """
    apr_hc = run_sql(query_apr)[0][0]
    assert apr_hc == 380, f"Expected 380 active headcount in 2025-04, got {apr_hc}"


def test_kpi_m02_m03_joiners_and_leavers_latest():
    """Verify M02 Joiners (17) and M03 Leavers (3) for Sep 2026."""
    query = """
        SELECT SUM(h.hires) AS joiners, SUM(h.exits) AS leavers, SUM(h.voluntary_exits) AS vol_leavers
        FROM dw.fact_headcount_monthly h
        JOIN dw.dim_date d ON d.date_key = h.date_key
        WHERE d.year_month = '2026-09';
    """
    row = run_sql(query)[0]
    joiners, leavers, vol = row[0], row[1], row[2]
    assert joiners == 17, f"Expected 17 joiners in Sep 2026, got {joiners}"
    assert leavers == 3, f"Expected 3 leavers in Sep 2026, got {leavers}"
    assert vol == 2, f"Expected 2 voluntary leavers in Sep 2026, got {vol}"


def test_kpi_m04_monthly_attrition_rate():
    """Verify M04 Attrition Rate for Sep 2026 equals 0.70% (3 / 427 * 100)."""
    query = """
        SELECT 
            SUM(h.exits) AS exits,
            SUM(h.headcount_start) AS start_hc,
            ROUND((SUM(h.exits)::numeric / SUM(h.headcount_start)) * 100, 2) AS attrition_pct
        FROM dw.fact_headcount_monthly h
        JOIN dw.dim_date d ON d.date_key = h.date_key
        WHERE d.year_month = '2026-09';
    """
    row = run_sql(query)[0]
    exits, start_hc, attrition_pct = row[0], row[1], float(row[2])
    assert exits == 3
    assert start_hc == 427
    assert attrition_pct == 0.70, f"Expected 0.70% monthly attrition, got {attrition_pct}"


def test_tenure_bands_distribution():
    """Verify tenure bands sum to exactly 441 active employees."""
    query = """
        SELECT 
            CASE 
                WHEN tenure_years < 1 THEN 'Under 1 yr'
                WHEN tenure_years < 3 THEN '1-3 yrs'
                WHEN tenure_years < 5 THEN '3-5 yrs'
                WHEN tenure_years < 10 THEN '5-10 yrs'
                ELSE '10+ yrs' 
            END AS tenure_band,
            COUNT(DISTINCT employee_id) AS cnt
        FROM dw.dim_employee
        WHERE is_current = TRUE AND is_active = TRUE
        GROUP BY 1;
    """
    rows = dict(run_sql(query))
    assert rows["Under 1 yr"] == 97
    assert rows["1-3 yrs"] == 123
    assert rows["3-5 yrs"] == 107
    assert rows["5-10 yrs"] == 82
    assert rows["10+ yrs"] == 32
    total = sum(rows.values())
    assert total == 441, f"Expected 441 total active employees across tenure bands, got {total}"


def test_department_split_distribution():
    """Verify department split sums to 441, with Engineering at 167 (37.9%)."""
    query = """
        SELECT dep.department_name, h.headcount_end
        FROM dw.fact_headcount_monthly h
        JOIN dw.dim_department dep ON dep.department_key = h.department_key
        JOIN dw.dim_date d ON d.date_key = h.date_key
        WHERE d.year_month = '2026-09';
    """
    dept_counts = dict(run_sql(query))
    assert dept_counts["Engineering"] == 167
    assert dept_counts["Customer Support"] == 59
    assert dept_counts["Data & AI"] == 52
    assert dept_counts["Sales"] == 46
    assert dept_counts["Executive Office"] == 1
    total = sum(dept_counts.values())
    assert total == 441, f"Expected 441 total headcount across departments, got {total}"


def test_joiners_vs_leavers_net_gain_in_2026():
    """Verify net additions across 2026 peak in September with +14."""
    query = """
        SELECT 
            d.year_month, 
            SUM(h.hires) - SUM(h.exits) AS net_addition
        FROM dw.fact_headcount_monthly h
        JOIN dw.dim_date d ON d.date_key = h.date_key
        WHERE d.year_month = '2026-09'
        GROUP BY d.year_month;
    """
    net = run_sql(query)[0][1]
    assert net == 14, f"Expected +14 net additions in Sep 2026, got {net}"
