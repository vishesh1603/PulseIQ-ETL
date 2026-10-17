"""Automated test suite verifying Attendance & Leave KPIs against PostgreSQL warehouse.

Tests all checkpoints and metrics from docs/metric_dictionary.md:
- M13 (Attendance rate) checkpoint: Engineering (D01), Apr 2025 = 0.9509
- Sep 2026 company KPIs (Attendance rate, Late rate, Unpaid leave days, Anomaly flags)
- AI Anomaly counts and referential integrity (405 total, 221 attendance, 184 payroll)
- Weekday leave distribution constraints (3,441 total requests)
"""
import os
import psycopg
import pytest

WAREHOUSE_DSN = os.environ.get(
    "WAREHOUSE_DSN",
    "postgresql://pulseiq:pulseiq@localhost:5433/pulseiq"
)

@pytest.fixture(scope="module")
def conn():
    with psycopg.connect(WAREHOUSE_DSN) as connection:
        yield connection

def test_m13_engineering_apr2025_checkpoint(conn):
    """M13 Checkpoint from metric dictionary: Engineering (D01) in Apr 2025 must equal 0.9509."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT ROUND((SUM(f.present_days) + 0.5 * SUM(f.half_days_unpaid)) / SUM(f.scheduled_days), 4)
            FROM dw.fact_attendance_monthly f
            JOIN dw.dim_department d ON d.department_key = f.department_key
            JOIN dw.dim_date dt ON dt.date_key = f.date_key
            WHERE d.department_id = 'D01' AND dt.year_month = '2025-04';
        """)
        rate = cur.fetchone()[0]
        assert float(rate) == 0.9509, f"Expected 0.9509, got {rate}"

def test_sep2026_attendance_kpis(conn):
    """Validate Sep 2026 company-wide attendance KPIs."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                ROUND((SUM(present_days) + 0.5 * SUM(half_days_unpaid)) / SUM(scheduled_days) * 100, 1),
                ROUND(SUM(late_arrivals)::numeric / SUM(present_days) * 100, 1),
                ROUND(SUM(unpaid_absence_days + 0.5 * half_days_unpaid), 1),
                (SELECT COUNT(*) FROM dw.fact_anomaly WHERE period_key = 20260930 AND source_dataset = 'attendance_monthly_features')
            FROM dw.fact_attendance_monthly
            WHERE date_key = 20260930;
        """)
        att_rate, late_rate, lop_days, anom_count = cur.fetchone()
        assert float(att_rate) == 95.2, f"Expected 95.2%, got {att_rate}"
        assert float(late_rate) == 7.1, f"Expected 7.1%, got {late_rate}"
        assert float(lop_days) == 85.5, f"Expected 85.5 days, got {lop_days}"
        assert anom_count == 10, f"Expected 10 anomalies, got {anom_count}"

def test_fact_anomaly_record_counts(conn):
    """Validate that fact_anomaly holds 405 rows: 221 attendance and 184 payroll."""
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM dw.fact_anomaly;")
        total = cur.fetchone()[0]
        assert total == 405, f"Expected 405 total anomalies, got {total}"

        cur.execute("SELECT count(*) FROM dw.fact_anomaly WHERE source_dataset = 'attendance_monthly_features';")
        att_total = cur.fetchone()[0]
        assert att_total == 221, f"Expected 221 attendance anomalies, got {att_total}"

        cur.execute("SELECT count(*) FROM dw.fact_anomaly WHERE source_dataset = 'payroll_monthly_features';")
        pay_total = cur.fetchone()[0]
        assert pay_total == 184, f"Expected 184 payroll anomalies, got {pay_total}"

def test_fact_anomaly_referential_integrity(conn):
    """All 405 anomaly records must map to valid date keys and valid employees."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT count(*) 
            FROM dw.fact_anomaly a
            LEFT JOIN dw.dim_date d ON d.date_key = a.period_key
            WHERE d.date_key IS NULL;
        """)
        orphan_dates = cur.fetchone()[0]
        assert orphan_dates == 0, f"Found {orphan_dates} anomalies with invalid period_key"

        cur.execute("""
            SELECT count(*)
            FROM dw.fact_anomaly a
            WHERE a.source_dataset = 'attendance_monthly_features'
              AND NOT EXISTS (
                  SELECT 1 FROM dw.fact_attendance_monthly f
                  WHERE f.employee_id = a.employee_id AND f.date_key = a.period_key
              );
        """)
        orphan_att = cur.fetchone()[0]
        assert orphan_att == 0, f"Found {orphan_att} attendance anomalies missing corresponding fact rows"

def test_leave_weekday_distribution(conn):
    """Verify all 3,441 leave requests start on weekdays and match exact warehouse counts."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT d.day_of_week, count(*) 
            FROM dw.fact_leave f
            JOIN dw.dim_date d ON d.date_key = f.start_date_key
            GROUP BY d.day_of_week;
        """)
        counts = dict(cur.fetchall())
        total_requests = sum(counts.values())
        assert total_requests == 3441, f"Expected 3,441 leave requests, got {total_requests}"
        assert "Saturday" not in counts, "Found leave starting on Saturday"
        assert "Sunday" not in counts, "Found leave starting on Sunday"
        assert counts["Friday"] == 720, f"Expected 720 Friday leave requests, got {counts.get('Friday')}"
        assert counts["Monday"] == 649, f"Expected 649 Monday leave requests, got {counts.get('Monday')}"
