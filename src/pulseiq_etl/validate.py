"""Validate: pandera rules on the cleaned tables. Any violation stops the run.

transform.py already moves known-bad rows to the rejected files. These schemas are the
safety net, and they also hold rules that cannot be fixed row by row (a new category,
a gap in an employee's history). If one fires, nothing is written to clean/.
"""
from __future__ import annotations

import logging

import pandas as pd

try:
    import pandera.pandas as pa
except ImportError:  # older pandera
    import pandera as pa

from .config import PAYROLL_MONEY, SPECS
from .errors import ValidationFailed

log = logging.getLogger(__name__)

MIN_DATE, MAX_DATE = pd.Timestamp("1950-01-01"), pd.Timestamp("2100-01-01")
DTYPE = {"id": "string", "text": "string", "cat": "string", "flag": "string", "int": "int64",
         "num": "float64", "date": "datetime64[ns]", "date_open": "datetime64[ns]"}

CATEGORIES = {
    ("dim_employee", "gender"): ["Male", "Female", "Other"],
    ("dim_employee", "employment_status"): ["Active", "Resigned", "Terminated", "Contract Ended"],
    ("dim_employee", "employment_type"): ["Permanent", "Fixed-Term Contract"],
    ("dim_employee", "work_mode"): ["Onsite", "Hybrid", "Remote"],
    ("dim_employee", "change_reason"): ["Joining", "Promotion", "Transfer", "Manager Change", "Manager Exit / Reassignment"],
    ("fact_payroll", "variable_pay_type"): ["None", "Performance Bonus", "Sales Incentive", "Festival Bonus", "Spot Award"],
    ("fact_leave", "status"): ["Approved", "Rejected", "Cancelled", "Pending"],
}
FLAGS = ["Y", "N"]


def _columns(table: str, extra: dict | None = None) -> dict:
    """Build the column rules from the table's Spec, then add helper columns and extra checks."""
    spec = SPECS[table]
    cols = {}
    for name, kind in spec.cols.items():
        checks = []
        if kind in ("date", "date_open"):
            checks.append(pa.Check(lambda s: s.isna() | s.between(MIN_DATE, MAX_DATE), error=f"{name} outside 1950..2100"))
        if kind == "flag":
            checks.append(pa.Check.isin(FLAGS))
        if (table, name) in CATEGORIES:
            checks.append(pa.Check.isin(CATEGORIES[(table, name)]))
        nullable = name not in spec.required and name not in spec.filled
        cols[name] = pa.Column(DTYPE[kind], checks=checks or None, nullable=nullable, coerce=True)
    for name, column in (extra or {}).items():
        cols[name] = column
    return cols


def _col(dtype, *checks, nullable=False):
    return pa.Column(dtype, checks=list(checks) or None, nullable=nullable, coerce=True)


GE0 = pa.Check.ge(0)
MONTH = pa.Check.in_range(1, 12)
INT, BOOL = "int64", "bool"
NOT_NEGATIVE = {c: None for c in PAYROLL_MONEY}


def _employee_schema() -> "pa.DataFrameSchema":
    constant = ["date_of_birth", "hire_date", "exit_date", "gender", "employment_status", "employment_type"]

    def one_current(df):
        n = df.groupby("employee_id")["is_current"].apply(lambda s: (s == "Y").sum())
        return df["employee_id"].map(n) == 1

    def contiguous(df):
        g = df.sort_values(["employee_id", "valid_from"], kind="mergesort")
        prev_to = g.groupby("employee_id")["valid_to"].shift()
        first = prev_to.isna()
        ok = first | ((g["valid_from"] - prev_to).dt.days == 1)
        return ok.reindex(df.index)

    def constant_per_employee(df):
        n = df.groupby("employee_id")[constant].nunique(dropna=False).le(1).all(axis=1)
        return df["employee_id"].map(n)

    cols = _columns("dim_employee", {
        "hire_year": _col(INT), "hire_month": _col(INT, MONTH),
        "tenure_days": _col(INT, GE0), "tenure_years": _col("float64", GE0), "is_active": _col(BOOL),
    })
    cols["employee_key"] = _col(INT, nullable=False, )
    cols["job_level"] = _col(INT, pa.Check.in_range(1, 7))
    return pa.DataFrameSchema(
        cols, strict=True, unique=["employee_key"],
        checks=[
            pa.Check(lambda df: df["exit_date"].isna() | (df["exit_date"] >= df["hire_date"]), error="exit_date is before hire_date"),
            pa.Check(lambda df: df["valid_to"].isna() | (df["valid_to"] >= df["valid_from"]), error="valid_to is before valid_from"),
            pa.Check(one_current, error="employee must have exactly one current version"),
            pa.Check(contiguous, error="employee versions overlap or leave a gap"),
            pa.Check(constant_per_employee, error="birth date, hire date, exit date, gender, status or type differ between versions"),
        ],
    )


def _payroll_schema() -> "pa.DataFrameSchema":
    extra = {"year": _col(INT), "month": _col(INT, MONTH), "month_start": _col("datetime64[ns]")}
    cols = _columns("fact_payroll", extra)
    for c in list(PAYROLL_MONEY) + ["payable_days", "lop_days", "overtime_hours_paid"]:
        cols[c] = _col("float64", pa.Check.ge(0, error=f"negative {c}"))
    return pa.DataFrameSchema(
        cols, strict=True, unique=["payroll_item_id"],
        checks=[
            pa.Check(lambda df: ~df.duplicated(["employee_id", "run_id"], keep=False), error="more than one payroll row for an employee in a run"),
            pa.Check(lambda df: (df["net_pay"] - (df["gross_pay"] - df["total_deductions"])).abs() <= 0.05, error="net_pay differs from gross_pay minus total_deductions"),
            pa.Check(lambda df: (df["gross_pay"] - (df["earned_fixed_pay"] + df["overtime_pay"] + df["variable_pay"])).abs() <= 0.05, error="gross_pay differs from its parts"),
            pa.Check(lambda df: (df["employer_cost"] - (df["gross_pay"] + df["pf_employer"] + df["esi_employer"])).abs() <= 0.05, error="employer_cost differs from gross plus employer contributions"),
        ],
    )


def _attendance_schema() -> "pa.DataFrameSchema":
    cols = _columns("fact_attendance_monthly", {"year": _col(INT), "month": _col(INT, MONTH), "month_start": _col("datetime64[ns]")})
    for c in ["scheduled_days", "present_days", "wfh_days", "half_days_unpaid", "paid_leave_days",
              "unpaid_absence_days", "late_arrivals", "avg_hours_worked", "overtime_hours"]:
        cols[c] = _col("float64", GE0)
    cols["attendance_rate"] = _col("float64", pa.Check.in_range(0, 1))
    return pa.DataFrameSchema(
        cols, strict=True, unique=["attendance_fact_id"],
        checks=[
            pa.Check(lambda df: ~df.duplicated(["employee_id", "date_key"], keep=False), error="more than one attendance row for an employee in a month"),
            pa.Check(lambda df: df["present_days"] <= df["scheduled_days"], error="present_days exceeds scheduled_days"),
        ],
    )


def _leave_schema() -> "pa.DataFrameSchema":
    cols = _columns("fact_leave", {"calendar_days": _col(INT, pa.Check.ge(1)), "start_year": _col(INT), "start_month": _col(INT, MONTH)})
    cols["days"] = _col("float64", pa.Check.gt(0))
    return pa.DataFrameSchema(
        cols, strict=True, unique=["leave_request_id"],
        checks=[pa.Check(lambda df: df["end_date"] >= df["start_date"], error="end_date is before start_date")],
    )


def _dim_schema(table: str, unique: str, checks=None) -> "pa.DataFrameSchema":
    return pa.DataFrameSchema(_columns(table), strict=True, unique=[unique], checks=checks)


def _date_dim_schema() -> "pa.DataFrameSchema":
    def no_gaps(df):
        return df.sort_values("date")["date"].diff().dropna().dt.days.eq(1).all()

    cols = _columns("dim_date")
    cols["month_number"] = _col(INT, MONTH)
    cols["quarter"] = _col(INT, pa.Check.in_range(1, 4))
    return pa.DataFrameSchema(
        cols, strict=True, unique=["date_key", "date"],
        checks=[
            pa.Check(lambda df: df["date_key"] == df["date"].dt.year * 10000 + df["date"].dt.month * 100 + df["date"].dt.day, error="date_key is not yyyymmdd of date"),
            pa.Check(no_gaps, error="dim_date has a gap in its days"),
        ],
    )


SCHEMAS = {
    "dim_date": _date_dim_schema(),
    "dim_department": _dim_schema("dim_department", "department_id"),
    "dim_role": _dim_schema("dim_role", "role_id", [pa.Check(lambda df: (df["band_min_annual"] <= df["band_mid_annual"]) & (df["band_mid_annual"] <= df["band_max_annual"]), error="salary band not ascending")]),
    "dim_leave_type": _dim_schema("dim_leave_type", "leave_type_code"),
    "dim_employee": _employee_schema(),
    "fact_payroll": _payroll_schema(),
    "fact_attendance_monthly": _attendance_schema(),
    "fact_leave": _leave_schema(),
}


def validate_all(clean: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Validate every table. Collect all failures first so one run shows every problem."""
    validated, failures = {}, []
    for name, df in clean.items():
        try:
            validated[name] = SCHEMAS[name].validate(df, lazy=True)
            log.info("Validation passed for %-24s (%d rows)", name, len(df))
        except pa.errors.SchemaErrors as exc:
            cases = exc.failure_cases
            summary = cases.groupby(["column", "check"], dropna=False).size().reset_index(name="rows").to_string(index=False)
            log.error("Validation FAILED for %s:\n%s", name, summary)
            failures.append(f"{name}: {len(cases)} failing value(s)\n{summary}")
    if failures:
        raise ValidationFailed("Pandera validation failed.\n" + "\n\n".join(failures))
    return validated
