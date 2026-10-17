"""Warehouse tests. They need PostgreSQL: set WAREHOUSE_DSN, for example
    WAREHOUSE_DSN=postgresql://pulseiq:pulseiq@localhost:5433/pulseiq
Inside Docker Compose the variable is already set. Each test starts from an empty dw schema."""
import os
from pathlib import Path

import pandas as pd
import psycopg
import pytest

from make_sample_data import main as make_sample
from pulseiq_etl.errors import WarehouseError
from pulseiq_etl.pipeline import run
from pulseiq_etl.warehouse import load_warehouse
from test_pipeline import last_run, settings_for

DSN = os.environ.get("WAREHOUSE_DSN", "")
QUERIES = Path(__file__).resolve().parents[1] / "sql" / "queries"
TABLES = ["dim_date", "dim_department", "dim_role", "dim_leave_type", "dim_employee", "fact_payroll",
          "fact_attendance_monthly", "fact_leave", "fact_headcount_monthly"]


def _reachable() -> bool:
    if not DSN:
        return False
    try:
        psycopg.connect(DSN, connect_timeout=3).close()
        return True
    except psycopg.Error:
        return False


pytestmark = pytest.mark.skipif(not _reachable(), reason="set WAREHOUSE_DSN to a reachable PostgreSQL")


def sql(query: str, params=None) -> pd.DataFrame:
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute(query, params)
        cols = [c.name for c in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=cols)


def query_file(name: str) -> pd.DataFrame:
    return sql((QUERIES / name).read_text())


def reset_schema() -> None:
    with psycopg.connect(DSN, autocommit=True) as conn:
        conn.execute("DROP SCHEMA IF EXISTS dw CASCADE")


@pytest.fixture
def loaded(tmp_path):
    """Sample data, cleaned and loaded into an empty warehouse."""
    reset_schema()
    make_sample(tmp_path / "raw")
    s = settings_for(tmp_path, warehouse_dsn=DSN)
    assert run(s) == 0
    clean = {t: pd.read_parquet(s.clean_dir / f"{t}.parquet") for t in TABLES if t != "fact_headcount_monthly"}
    return s, clean


# ---------- reference answers computed from the clean files with pandas ----------

def ym(series):
    return series.dt.strftime("%Y-%m")


def compare(sql_df, ref_df, keys, **kw):
    a = sql_df.sort_values(keys).reset_index(drop=True)
    b = ref_df.sort_values(keys).reset_index(drop=True)
    for c in a.columns:
        if a[c].dtype == object and c not in keys:
            a[c] = a[c].astype(float)
    pd.testing.assert_frame_equal(a, b[a.columns], check_dtype=False, check_exact=False, atol=kw.get("atol", 0.01), rtol=0)


def headcount_reference(clean) -> pd.DataFrame:
    emp, dept, date = clean["dim_employee"].copy(), clean["dim_department"], clean["dim_date"]
    emp["valid_to"] = emp["valid_to"].fillna(pd.Timestamp("2262-01-01"))
    last = clean["fact_payroll"]["period_end_date"].max()
    ends = sorted(date.loc[(date.is_month_end == "Y") & (date.date <= last), "date"])
    rows = []
    for me in ends:
        alive = emp[(emp.valid_from <= me) & (emp.valid_to >= me) & (emp.hire_date <= me) & (emp.exit_date.isna() | (emp.exit_date > me))]
        counts = alive.groupby("department_id").size()
        for d in dept.itertuples():
            rows.append({"year_month": me.strftime("%Y-%m"), "department_name": d.department_name, "headcount_end": int(counts.get(d.department_id, 0))})
    return pd.DataFrame(rows)


def test_three_questions_match_the_clean_files(loaded):
    _, clean = loaded
    names = clean["dim_department"].set_index("department_id")["department_name"]
    # Q1 cost by department and month
    pay = clean["fact_payroll"].assign(year_month=lambda d: ym(d.period_end_date), department_name=lambda d: d.department_id.map(names))
    q1 = pay.groupby(["year_month", "department_name"], as_index=False).agg(employees_paid=("employee_id", "count"), employer_cost=("employer_cost", "sum"))
    compare(query_file("q1_cost_by_department_month.sql"), q1, ["year_month", "department_name"])
    # Q2 headcount by department and month
    q2 = headcount_reference(clean)
    sql2 = query_file("q2_headcount_by_department_month.sql")
    assert len(sql2) == len(q2) > 0
    compare(sql2, q2, ["year_month", "department_name"])
    # Q3 attendance rate by month
    att = clean["fact_attendance_monthly"].assign(year_month=lambda d: ym(d.period_end_date))
    g = att.groupby("year_month")
    q3 = ((g.present_days.sum() + 0.5 * g.half_days_unpaid.sum()) / g.scheduled_days.sum()).round(4).rename("attendance_rate").reset_index()
    compare(query_file("q3_attendance_rate_by_month.sql"), q3, ["year_month"], atol=0.0001)
    # Q4 cost by role and month
    titles = clean["dim_role"].set_index("role_id")["role_title"]
    q4 = pay.assign(role_title=lambda d: d.role_id.map(titles)).groupby(["year_month", "role_title"], as_index=False).agg(
        employees_paid=("employee_id", "count"), employer_cost=("employer_cost", "sum"))
    sql4 = query_file("q4_cost_by_role_month.sql")
    compare(sql4, q4, ["year_month", "role_title"])


def test_every_table_matches_the_clean_row_counts(loaded):
    _, clean = loaded
    for name, df in clean.items():
        assert sql(f"SELECT count(*) AS n FROM dw.{name}").n[0] == len(df), name


def test_second_load_changes_nothing(loaded):
    s, _ = loaded
    assert run(s) == 0
    for name, st in last_run(s)["warehouse"].items():
        assert st["inserted"] == st["updated"] == st["deleted"] == 0, name
        assert st["unchanged"] == st["rows_in_feed"] > 0, name


def test_changed_and_removed_source_rows_are_applied_not_duplicated(loaded):
    s, clean = loaded
    raw_dep = s.raw_dir / "dim_department.csv"
    dep = pd.read_csv(raw_dep)
    dep.loc[dep.department_id == "D02", "department_name"] = "Revenue"        # a renamed department (type 1)
    dep.to_csv(raw_dep, index=False)
    raw_pay = s.raw_dir / "fact_payroll.csv"
    pay = pd.read_csv(raw_pay)
    gone = pay.loc[pay.employee_id == "EMP-0010"].iloc[0]["payroll_item_id"]
    pay[pay.payroll_item_id != gone].to_csv(raw_pay, index=False)             # a payroll row that disappeared
    assert run(s) == 0
    st = last_run(s)["warehouse"]
    assert st["dim_department"]["updated"] == 1 and st["dim_department"]["rows_in_warehouse"] == 5
    assert st["fact_payroll"]["deleted"] == 1 and st["fact_payroll"]["inserted"] == 0
    assert st["dim_employee"]["updated"] == 0
    assert sql("SELECT department_name FROM dw.dim_department WHERE department_id = 'D02'").department_name[0] == "Revenue"
    assert sql("SELECT count(*) AS n FROM dw.fact_payroll WHERE payroll_item_id = %s", (gone,)).n[0] == 0


def test_department_move_splits_cost_by_month(loaded):
    """EMP-0005 moves from Sales to Support on 1 June 2025."""
    rows = sql("""SELECT d.year_month, dep.department_name, f.employer_cost, e.valid_from, e.valid_to
                  FROM dw.fact_payroll f JOIN dw.dim_date d USING (date_key) JOIN dw.dim_department dep USING (department_key)
                  JOIN dw.dim_employee e USING (employee_key)
                  WHERE f.employee_id = 'EMP-0005' ORDER BY d.year_month""").set_index("year_month")
    assert rows.loc["2025-05", "department_name"] == "Sales"
    assert rows.loc["2025-06", "department_name"] == "Support"
    assert rows.loc["2025-07", "department_name"] == "Support"
    assert str(rows.loc["2025-05", "valid_to"]) == "2025-05-31" and str(rows.loc["2025-06", "valid_from"]) == "2025-06-01"
    may = query_file("q1_cost_by_department_month.sql").query("year_month == '2025-05'").set_index("department_name")
    cost = float(rows.loc["2025-05", "employer_cost"])
    paid = sql("SELECT count(*) AS n FROM dw.fact_payroll f JOIN dw.dim_date USING (date_key) WHERE year_month = '2025-05' AND department_key = (SELECT department_key FROM dw.dim_department WHERE department_name = 'Support')").n[0]
    assert float(may.loc["Sales", "employer_cost"]) >= cost
    # Support has no EMP-0005 cost in May and counts her from June
    hc = sql("""SELECT d.year_month, dep.department_name, h.transfers_in, h.transfers_out FROM dw.fact_headcount_monthly h
                JOIN dw.dim_date d USING (date_key) JOIN dw.dim_department dep USING (department_key)
                WHERE d.year_month = '2025-06' AND dep.department_name IN ('Sales', 'Support')""").set_index("department_name")
    assert hc.loc["Support", "transfers_in"] == 1 and hc.loc["Sales", "transfers_out"] == 1


def test_database_refuses_overlapping_employee_history(loaded):
    with pytest.raises(psycopg.errors.ExclusionViolation):
        with psycopg.connect(DSN) as conn:
            conn.execute("""INSERT INTO dw.dim_employee
                SELECT 999999999, employee_id, full_name, gender, date_of_birth, hire_date, exit_date, employment_status,
                       employment_type, department_key, role_key, role_title, job_level, manager_id, work_location, work_mode,
                       highest_education, valid_from + 5, valid_to, false, change_reason, hire_year, hire_month, tenure_days,
                       tenure_years, is_active
                FROM dw.dim_employee WHERE employee_id = 'EMP-0010' AND is_current""")


def test_database_refuses_a_fact_with_no_dimension_row(loaded):
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with psycopg.connect(DSN) as conn:
            conn.execute("""INSERT INTO dw.fact_payroll
                SELECT employee_id || '-X', date_key, 'PI-BAD', run_id, employee_key, -1, role_key, variable_pay_type, payable_days, lop_days,
                       overtime_hours_paid, monthly_fixed_gross, basic, hra, conveyance, medical, special_allowance, earned_fixed_pay,
                       overtime_pay, variable_pay, gross_pay, pf_employee, esi_employee, professional_tax, tds, other_deductions,
                       total_deductions, net_pay, pf_employer, esi_employer, employer_cost, headcount_flag
                FROM dw.fact_payroll LIMIT 1""")


def test_lost_rows_stop_the_load_and_roll_back(loaded):
    s, clean = loaded
    before = {t: sql(f"SELECT count(*) AS n FROM dw.{t}").n[0] for t in TABLES}
    broken = {k: v.copy() for k, v in clean.items()}
    broken["fact_payroll"] = broken["fact_payroll"].assign(department_id="D99")   # a department that does not exist
    with pytest.raises(WarehouseError, match="lost"):
        load_warehouse(broken, DSN)
    assert {t: sql(f"SELECT count(*) AS n FROM dw.{t}").n[0] for t in TABLES} == before


def test_current_flag_and_history_are_consistent(loaded):
    bad = sql("""SELECT employee_id FROM dw.dim_employee GROUP BY employee_id HAVING count(*) FILTER (WHERE is_current) <> 1""")
    assert bad.empty
    multi = sql("SELECT employee_id, count(*) AS n FROM dw.dim_employee GROUP BY employee_id HAVING count(*) > 1")
    assert len(multi) > 0 and (sql("SELECT count(*) AS n FROM dw.dim_employee WHERE valid_to = DATE '9999-12-31'").n[0] > 0)


# ---------- real workbook: only when PULSEIQ_WORKBOOK is set ----------
WORKBOOK = os.environ.get("PULSEIQ_WORKBOOK")


@pytest.mark.skipif(not WORKBOOK or not Path(WORKBOOK).exists(), reason="set PULSEIQ_WORKBOOK to run")
def test_real_workbook_warehouse(tmp_path):
    reset_schema()
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / Path(WORKBOOK).name).symlink_to(Path(WORKBOOK).resolve())
    s = settings_for(tmp_path, warehouse_dsn=DSN)
    assert run(s) == 0 and run(s) == 0
    for name, st in last_run(s)["warehouse"].items():
        assert st["inserted"] == st["updated"] == st["deleted"] == 0, name
    sheet = pd.read_excel(WORKBOOK, sheet_name="fact_headcount_monthly")
    wh = sql("""SELECT d.date_key, dep.department_id, f.headcount_start, f.hires, f.exits, f.voluntary_exits, f.transfers_in,
                f.transfers_out, f.headcount_end, f.attrition_rate_monthly_pct
                FROM dw.fact_headcount_monthly f JOIN dw.dim_date d USING (date_key) JOIN dw.dim_department dep USING (department_key)""")
    merged = sheet.merge(wh, on=["date_key", "department_id"], suffixes=("_wb", "_dw"))
    assert len(wh) == len(sheet) == len(merged) == 891
    for col in ["headcount_start", "hires", "exits", "voluntary_exits", "transfers_in", "transfers_out", "headcount_end"]:
        assert (merged[col + "_wb"].astype(int) == merged[col + "_dw"].astype(int)).all(), col
    # the workbook rounds half to even, PostgreSQL rounds half up: allow one cent of difference
    assert ((merged["attrition_rate_monthly_pct_wb"].astype(float) - merged["attrition_rate_monthly_pct_dw"].astype(float)).abs() <= 0.011).all()
    key = pd.read_excel(WORKBOOK, sheet_name="reconciliation_answer_key")
    mine = sql("""SELECT d.month_start_date AS month, count(*) AS employees_paid, sum(gross_pay) AS gross, sum(net_pay) AS net, sum(employer_cost) AS cost
                  FROM dw.fact_payroll f JOIN dw.dim_date d USING (date_key) GROUP BY 1""")
    key["month"] = pd.to_datetime(key["month"]).dt.date
    j = key.merge(mine, on="month")
    assert len(j) == len(key) == 18
    assert (j.employees_paid_x == j.employees_paid_y).all()
    for a, b in [("payroll_gross_pay", "gross"), ("payroll_net_pay", "net"), ("payroll_employer_cost", "cost")]:
        assert ((j[a].astype(float) - j[b].astype(float)).abs() <= 0.05).all(), a
    ref = pd.read_excel(WORKBOOK, sheet_name="reference_summary_dept_month")
    dept = sql("""SELECT dep.department_id, d.month_start_date AS month, sum(employer_cost) AS cost, count(*) AS paid
                  FROM dw.fact_payroll f JOIN dw.dim_date d USING (date_key) JOIN dw.dim_department dep USING (department_key) GROUP BY 1, 2""")
    ref["month"] = pd.to_datetime(ref["month"]).dt.date
    jr = ref.merge(dept, on=["department_id", "month"])
    assert len(jr) == len(ref) > 0
    assert ((jr.employer_cost.astype(float) - jr.cost.astype(float)).abs() <= 0.05).all()
    assert (jr.employees_paid.astype(int) == jr.paid.astype(int)).all()
    ex = sql("""SELECT d.year_month, dep.department_name FROM dw.fact_payroll f JOIN dw.dim_date d USING (date_key)
                JOIN dw.dim_department dep USING (department_key) WHERE f.employee_id = 'EMP-0194' AND d.year_month IN ('2026-01', '2026-02')
                ORDER BY 1""")
    assert ex.department_name.tolist() == ["Data & AI", "Product & Design"]
