"""Settings and table definitions for the PulseIQ star-schema workbook.

Each table is described once here: column kinds, required columns, unique keys,
and sort order. To add another sheet, add a Spec and a transform function.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional outside Docker
    pass

# Column kinds:
#   id        trimmed, upper-cased code (EMP-0001, D01)
#   text      trimmed, whitespace collapsed
#   cat       like text, but Title Case (categories such as "Resigned")
#   flag      Y / N
#   int, num  whole number, decimal (currency symbols and commas allowed)
#   date      calendar date
#   date_open calendar date where 9999-12-31 means "still open" and becomes blank


@dataclass(frozen=True)
class Spec:
    cols: dict
    required: tuple
    keys: tuple                      # each entry is a list of columns that must be unique
    sort: tuple
    ignore_in_dup: tuple = ()        # surrogate ids ignored when deciding "exact duplicate"
    filled: tuple = ()               # columns where blanks are filled by a documented rule
    kind: str = "fact"               # dim | fact


def _spec(cols, required=None, **kw):
    required = tuple(cols) if required is None else tuple(required)
    return Spec(cols=cols, required=required, **kw)


_MONEY = ["monthly_fixed_gross", "basic", "hra", "conveyance", "medical", "special_allowance",
          "earned_fixed_pay", "overtime_pay", "variable_pay", "gross_pay", "pf_employee",
          "esi_employee", "professional_tax", "tds", "other_deductions", "total_deductions",
          "net_pay", "pf_employer", "esi_employer", "employer_cost"]
PAYROLL_MONEY = tuple(_MONEY)

SPECS = {
    "dim_date": _spec(
        dict(date="date", date_key="int", year="int", quarter="int", month_number="int", month_name="text",
             year_month="text", week_of_year="int", day_of_week="text", is_weekend="flag", is_holiday="flag",
             is_working_day="flag", financial_year="text", fiscal_quarter="text", fiscal_month_number="int",
             is_month_end="flag", month_start_date="date", month_end_date="date"),
        keys=(["date_key"], ["date"]), sort=("date",), kind="dim"),
    "dim_department": _spec(
        dict(department_id="id", department_name="text", cost_center="id", description="text", is_leadership="flag"),
        required=["department_id", "department_name", "cost_center", "is_leadership"],
        keys=(["department_id"],), sort=("department_id",), kind="dim"),
    "dim_role": _spec(
        dict(role_id="id", department_id="id", role_title="text", level="int", grade="text",
             band_min_annual="num", band_mid_annual="num", band_max_annual="num",
             overtime_eligible="flag", band_reference_year="int"),
        required=["role_id", "department_id", "role_title", "level", "band_min_annual",
                  "band_mid_annual", "band_max_annual", "overtime_eligible"],
        keys=(["role_id"],), sort=("role_id",), kind="dim"),
    "dim_leave_type": _spec(
        dict(leave_type_code="id", leave_type_name="text", pay_type="cat", annual_quota_days="num",
             prorated_for_joiners="flag", carry_forward_allowed="flag", max_carry_forward_days="num",
             policy_note="text"),
        required=["leave_type_code", "leave_type_name", "pay_type"],
        keys=(["leave_type_code"],), sort=("leave_type_code",), kind="dim"),
    "dim_employee": _spec(
        dict(employee_key="int", employee_id="id", full_name="text", gender="cat", date_of_birth="date",
             hire_date="date", exit_date="date", employment_status="cat", employment_type="cat",
             department_id="id", role_id="id", role_title="text", job_level="int", manager_id="id",
             work_location="text", work_mode="cat", highest_education="text", valid_from="date",
             valid_to="date_open", is_current="flag", change_reason="cat"),
        required=["employee_key", "employee_id", "full_name", "gender", "date_of_birth", "hire_date",
                  "employment_status", "employment_type", "department_id", "role_id", "role_title",
                  "job_level", "work_location", "work_mode", "valid_from", "is_current", "change_reason"],
        keys=(["employee_key"], ["employee_id", "valid_from"]),
        sort=("employee_id", "valid_from"), filled=("highest_education",), kind="dim"),
    "fact_payroll": _spec(
        dict(payroll_item_id="id", run_id="id", employee_id="id", date_key="int", employee_key="int",
             period_end_date="date", department_id="id", role_id="id", payable_days="num", lop_days="num",
             overtime_hours_paid="num", variable_pay_type="cat", **{m: "num" for m in _MONEY},
             headcount_flag="int"),
        required=[c for c in ["payroll_item_id", "run_id", "employee_id", "date_key", "employee_key",
                              "period_end_date", "department_id", "role_id", "payable_days", "lop_days",
                              "overtime_hours_paid", *_MONEY, "headcount_flag"]],
        keys=(["payroll_item_id"], ["employee_id", "run_id"]),
        ignore_in_dup=("payroll_item_id",), sort=("period_end_date", "employee_id"),
        filled=("variable_pay_type",)),
    "fact_attendance_monthly": _spec(
        dict(attendance_fact_id="id", employee_id="id", date_key="int", employee_key="int",
             department_id="id", scheduled_days="num", present_days="num", wfh_days="num",
             half_days_unpaid="num", paid_leave_days="num", unpaid_absence_days="num",
             late_arrivals="num", avg_hours_worked="num", overtime_hours="num",
             attendance_rate="num", period_end_date="date"),
        keys=(["attendance_fact_id"], ["employee_id", "date_key"]),
        ignore_in_dup=("attendance_fact_id",), sort=("period_end_date", "employee_id")),
    "fact_leave": _spec(
        dict(leave_request_id="id", employee_id="id", employee_key="int", leave_type_code="id",
             start_date_key="int", end_date_key="int", start_date="date", end_date="date", days="num",
             status="cat", applied_on="date", decided_on="date", approver_id="id", reason="text"),
        required=["leave_request_id", "employee_id", "employee_key", "leave_type_code", "start_date_key",
                  "end_date_key", "start_date", "end_date", "days", "status", "applied_on"],
        keys=(["leave_request_id"],), sort=("start_date", "employee_id", "leave_request_id")),
}

# Order matters: dimensions first, because facts are checked against them.
TABLE_ORDER = ["dim_date", "dim_department", "dim_role", "dim_leave_type", "dim_employee",
               "fact_payroll", "fact_attendance_monthly", "fact_leave"]

# Optional sheet used only to check the finished payroll numbers.
RECONCILIATION_SHEET = "reconciliation_answer_key"


def _bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


@dataclass(frozen=True)
class Settings:
    raw_dir: Path
    clean_dir: Path
    rejected_dir: Path
    log_dir: Path
    output_format: str = "parquet"
    max_reject_pct: float = 10.0
    as_of_date: date | None = None
    dayfirst: bool = False
    reconcile_strict: bool = False
    warehouse_dsn: str = ""          # empty = skip the warehouse load

    @classmethod
    def from_env(cls) -> "Settings":
        env = os.environ.get
        as_of = (env("AS_OF_DATE") or "").strip()
        fmt = (env("OUTPUT_FORMAT") or "parquet").strip().lower()
        if fmt not in {"parquet", "csv"}:
            raise ValueError(f"OUTPUT_FORMAT must be parquet or csv, got {fmt!r}")
        return cls(
            raw_dir=Path(env("RAW_DIR") or "data/raw"),
            clean_dir=Path(env("CLEAN_DIR") or "data/clean"),
            rejected_dir=Path(env("REJECTED_DIR") or "data/rejected"),
            log_dir=Path(env("LOG_DIR") or "logs"),
            output_format=fmt,
            max_reject_pct=float(env("MAX_REJECT_PCT") or 10),
            as_of_date=date.fromisoformat(as_of) if as_of else None,
            dayfirst=_bool(env("DATES_DAYFIRST") or "false"),
            reconcile_strict=_bool(env("RECONCILE_STRICT") or "false"),
            warehouse_dsn=(env("WAREHOUSE_DSN") or "").strip(),
        )
