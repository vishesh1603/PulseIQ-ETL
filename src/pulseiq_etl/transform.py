"""Transform: fix types, standardise values, remove duplicates, fill gaps, add helper columns.

Every table function returns a TableResult:
  clean     rows that passed every rule
  rejected  rows that broke a rule, with raw values and a reason (never silently dropped)
  repairs   values changed by a documented repair rule, with old and new value
  warnings  things worth a look that do not block a row
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .config import PAYROLL_MONEY, SPECS, Spec

NA_TOKENS = {"", "na", "n/a", "nan", "null", "none", "nil", "-", "--", "nat"}
MONTH_END = pd.offsets.MonthEnd(0)
ONE_DAY = pd.Timedelta(days=1)
REPAIR_COLS = ["source_row", "column", "old_value", "new_value", "rule"]


@dataclass
class Ctx:
    """What a table needs to know about the tables cleaned before it."""
    as_of: pd.Timestamp
    dayfirst: bool = False
    dept_ids: set = field(default_factory=set)
    role_ids: set = field(default_factory=set)
    leave_types: set = field(default_factory=set)
    employees: pd.DataFrame | None = None  # clean dim_employee


@dataclass
class TableResult:
    name: str
    raw: pd.DataFrame
    clean: pd.DataFrame
    rejected: pd.DataFrame
    filled: dict = field(default_factory=dict)
    repairs: pd.DataFrame = field(default_factory=lambda: pd.DataFrame(columns=REPAIR_COLS))
    warnings: dict = field(default_factory=dict)


# ---------- cleaning helpers ----------

def blank_to_na(s: pd.Series) -> pd.Series:
    s = s.astype("string").str.strip()
    return s.mask(s.str.lower().isin(NA_TOKENS))


def _to_id(s):
    return blank_to_na(s).str.upper().str.replace(r"\s+", "", regex=True)


def _to_text(s):
    return blank_to_na(s).str.replace(r"\s+", " ", regex=True)


def to_number(s: pd.Series) -> pd.Series:
    cleaned = blank_to_na(s).str.replace(r"(?i)rs\.?|inr|[₹$,\s]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def to_date(s: pd.Series, dayfirst: bool) -> pd.Series:
    out = pd.to_datetime(blank_to_na(s), errors="coerce", format="mixed", dayfirst=dayfirst)
    return out.dt.normalize().astype("datetime64[ns]")


def _is_open_date(s: pd.Series) -> pd.Series:
    """9999-12-31 style placeholder for a version that is still open."""
    return blank_to_na(s).str.match(r"^9999-").fillna(False).astype(bool)


def _date_key(d: pd.Series) -> pd.Series:
    """20250430 style number for a date column (NaN where the date is missing)."""
    return d.dt.year * 10000 + d.dt.month * 100 + d.dt.day


def _parse(raw: pd.DataFrame, spec: Spec, dayfirst: bool):
    """Type every column of a table. Returns (typed frame, generic rules, raw with all columns)."""
    raw = raw.copy()
    for col in spec.cols:
        if col not in raw.columns:
            raw[col] = ""
    p = pd.DataFrame({"source_row": raw["source_row"]}, index=raw.index)
    rules = []
    for col, kind in spec.cols.items():
        text = blank_to_na(raw[col])
        if kind == "id":
            p[col] = _to_id(raw[col])
        elif kind == "text":
            p[col] = _to_text(raw[col])
        elif kind == "cat":
            p[col] = _to_text(raw[col]).str.title()
        elif kind == "flag":
            u = text.str.upper()
            p[col] = u.map({"Y": "Y", "YES": "Y", "TRUE": "Y", "1": "Y", "N": "N", "NO": "N", "FALSE": "N", "0": "N"}).astype("string")
        elif kind == "num":
            p[col] = to_number(raw[col])
        elif kind == "int":
            n = to_number(raw[col])
            p[col] = n.where(n == n.round()).astype("Int64")
        elif kind in ("date", "date_open"):
            p[col] = to_date(raw[col], dayfirst)
        else:
            raise ValueError(f"unknown kind {kind}")
        is_open = _is_open_date(raw[col]) if kind == "date_open" else pd.Series(False, index=raw.index)
        rules.append((f"bad_{col}", text.notna() & p[col].isna() & ~is_open))
        if col in spec.required:
            rules.append((f"missing_{col}", text.isna()))
    return p, rules, raw


def _duplicate_rules(p: pd.DataFrame, spec: Spec):
    """exact_duplicate: same values as an earlier row (surrogate ids ignored), the first copy is kept.
    conflicting_duplicate: same key, different values. All copies are rejected."""
    value_cols = [c for c in p.columns if c != "source_row" and c not in spec.ignore_in_dup]
    exact = p.duplicated(subset=value_cols, keep="first")
    rest = p[~exact]
    conflict = pd.Series(False, index=p.index)
    for key in spec.keys:
        has_key = p[key].notna().all(axis=1)
        dup = rest.index[rest.duplicated(subset=key, keep=False) & has_key[rest.index]]
        conflict.loc[dup] = True
    return [("exact_duplicate", exact), ("conflicting_duplicate", conflict)]


def _route(table: str, raw: pd.DataFrame, p: pd.DataFrame, rules: list):
    """Split p into (good, rejected). rules is a list of (reason, boolean Series)."""
    names = [r for r, _ in rules]
    flags = np.column_stack([m.fillna(False).astype(bool).to_numpy() for _, m in rules])
    reasons = pd.Series([";".join(n for n, f in zip(names, row) if f) for row in flags], index=p.index)
    bad = reasons != ""
    rejected = raw.loc[bad].copy()
    rejected.insert(0, "reject_reason", reasons[bad])
    rejected.insert(0, "source_table", table)
    rejected = rejected.sort_values("source_row", kind="mergesort").reset_index(drop=True)
    return p.loc[~bad].copy(), rejected


def _repair_rows(source_rows, column, old, new, rule) -> pd.DataFrame:
    return pd.DataFrame({"source_row": list(source_rows), "column": column,
                         "old_value": [str(v)[:10] for v in old], "new_value": [str(v)[:10] for v in new],
                         "rule": rule}, columns=REPAIR_COLS)


def _fill_count(filled: dict, key: str, n: int) -> None:
    if n:
        filled[key] = int(n)


# ---------- reference dimensions ----------

def transform_date(raw, ctx: Ctx) -> TableResult:
    spec = SPECS["dim_date"]
    p, rules, raw = _parse(raw, spec, ctx.dayfirst)
    month_start = p["date"].dt.to_period("M").dt.to_timestamp().astype("datetime64[ns]")
    rules += [
        ("date_key_differs_from_date", p["date_key"].astype("float64") != _date_key(p["date"])),
        ("month_start_date_wrong", p["month_start_date"] != month_start),
        ("month_end_date_wrong", p["month_end_date"] != (p["date"] + MONTH_END)),
        ("is_month_end_wrong", (p["is_month_end"] == "Y") != (p["date"] == p["month_end_date"])),
    ]
    good, rejected = _route("dim_date", raw, p, rules + _duplicate_rules(p, spec))
    return TableResult("dim_date", raw, good, rejected)


def transform_department(raw, ctx: Ctx) -> TableResult:
    spec = SPECS["dim_department"]
    p, rules, raw = _parse(raw, spec, ctx.dayfirst)
    good, rejected = _route("dim_department", raw, p, rules + _duplicate_rules(p, spec))
    return TableResult("dim_department", raw, good, rejected)


def transform_role(raw, ctx: Ctx) -> TableResult:
    spec = SPECS["dim_role"]
    p, rules, raw = _parse(raw, spec, ctx.dayfirst)
    rules += [
        ("unknown_department", ~p["department_id"].isin(ctx.dept_ids)),
        ("band_not_ascending", ~((p["band_min_annual"] <= p["band_mid_annual"]) & (p["band_mid_annual"] <= p["band_max_annual"]))),
    ]
    good, rejected = _route("dim_role", raw, p, rules + _duplicate_rules(p, spec))
    return TableResult("dim_role", raw, good, rejected)


def transform_leave_type(raw, ctx: Ctx) -> TableResult:
    spec = SPECS["dim_leave_type"]
    p, rules, raw = _parse(raw, spec, ctx.dayfirst)
    good, rejected = _route("dim_leave_type", raw, p, rules + _duplicate_rules(p, spec))
    return TableResult("dim_leave_type", raw, good, rejected)


# ---------- dim_employee (SCD Type 2: one row per version of an employee) ----------

def transform_employee(raw, ctx: Ctx) -> TableResult:
    spec = SPECS["dim_employee"]
    p, rules, raw = _parse(raw, spec, ctx.dayfirst)
    filled: dict = {}
    n_blank = p["highest_education"].isna().sum()
    p["highest_education"] = p["highest_education"].fillna("Not stated")
    _fill_count(filled, "dim_employee.highest_education", n_blank)

    rules += [
        # The "joining after leaving" rule. See README.
        ("exit_before_hire", p["exit_date"] < p["hire_date"]),
        ("version_ends_before_it_starts", p["valid_to"] < p["valid_from"]),
        ("exit_date_and_status_disagree", p["exit_date"].isna() != (p["employment_status"] == "Active")),
        ("unknown_department", ~p["department_id"].isin(ctx.dept_ids)),
        ("unknown_role", ~p["role_id"].isin(ctx.role_ids)),
    ]
    good, rejected = _route("dim_employee", raw, p, rules + _duplicate_rules(p, spec))

    # Repair: a version that overlaps the next one is closed the day before the next starts (DQ-C12 fix).
    g = good.sort_values(["employee_id", "valid_from"], kind="mergesort")
    next_from = g.groupby("employee_id")["valid_from"].shift(-1)
    overlap = g["valid_to"].notna() & next_from.notna() & (g["valid_to"] >= next_from)
    repairs = _repair_rows(g.loc[overlap, "source_row"], "valid_to", g.loc[overlap, "valid_to"],
                           (next_from - ONE_DAY)[overlap], "overlapping_version_closed")
    good.loc[overlap[overlap].index, "valid_to"] = (next_from - ONE_DAY)[overlap]

    # Helper columns
    good["hire_year"] = good["hire_date"].dt.year
    good["hire_month"] = good["hire_date"].dt.month
    left = good["exit_date"].notna() & (good["exit_date"] <= ctx.as_of)
    end = good["exit_date"].where(left, ctx.as_of)
    days = (end - good["hire_date"]).dt.days.clip(lower=0)
    good["tenure_days"] = days
    good["tenure_years"] = (days / 365.25).round(2)
    good["is_active"] = good["employment_status"] == "Active"
    return TableResult("dim_employee", raw, good, rejected, filled, repairs)


# ---------- facts: shared checks ----------

def _employee_rules(p: pd.DataFrame, ctx: Ctx, with_role: bool = False) -> list:
    """Every fact row must point at a real employee version and agree with it."""
    emp = ctx.employees
    ver = emp.set_index("employee_key")[["employee_id", "department_id", "role_id", "hire_date", "exit_date"]]
    v = p[["employee_key"]].join(ver, on="employee_key", rsuffix="_dim")
    known = v["employee_id"].notna()
    exit_month_end = v["exit_date"] + MONTH_END
    rules = [
        ("unknown_employee", ~p["employee_id"].isin(set(emp["employee_id"]))),
        ("unknown_employee_key", ~known),
        ("employee_key_belongs_to_other_employee", known & (v["employee_id"] != p["employee_id"])),
        ("department_differs_from_employee_version", known & (v["department_id"] != p["department_id"])),
    ]
    if with_role:
        rules.append(("role_differs_from_employee_version", known & (v["role_id"] != p["role_id"])))
    if "period_end_date" in p:
        rules += [
            ("activity_after_exit_month", p["period_end_date"] > exit_month_end),
            ("activity_before_hire", p["period_end_date"] < v["hire_date"]),
        ]
    return rules


def _period_rules(p: pd.DataFrame) -> list:
    d = p["period_end_date"]
    return [
        ("period_end_not_month_end", d != (d + MONTH_END)),
        ("date_key_differs_from_period_end", p["date_key"].astype("float64") != _date_key(d)),
    ]


def _add_month_helpers(good: pd.DataFrame, col: str, names=("year", "month")) -> None:
    good[names[0]] = good[col].dt.year
    good[names[1]] = good[col].dt.month


# ---------- fact_payroll ----------

def transform_payroll(raw, ctx: Ctx) -> TableResult:
    spec = SPECS["fact_payroll"]
    p, rules, raw = _parse(raw, spec, ctx.dayfirst)
    filled: dict = {}
    no_bonus = p["variable_pay_type"].isna() & (p["variable_pay"] == 0)
    p.loc[no_bonus, "variable_pay_type"] = "None"
    _fill_count(filled, "fact_payroll.variable_pay_type", no_bonus.sum())

    near = lambda a, b, tol=0.05: (a - b).abs() > tol
    negative = (p[list(PAYROLL_MONEY) + ["payable_days", "lop_days", "overtime_hours_paid"]] < 0).any(axis=1)
    rules += [
        ("negative_amount", negative),
        ("earned_fixed_pay_differs_from_components", near(p["earned_fixed_pay"], p[["basic", "hra", "conveyance", "medical", "special_allowance"]].sum(axis=1), 1.0)),
        ("gross_pay_differs_from_parts", near(p["gross_pay"], p["earned_fixed_pay"] + p["overtime_pay"] + p["variable_pay"])),
        ("total_deductions_differ_from_parts", near(p["total_deductions"], p[["pf_employee", "esi_employee", "professional_tax", "tds", "other_deductions"]].sum(axis=1))),
        ("net_pay_differs_from_gross_minus_deductions", near(p["net_pay"], p["gross_pay"] - p["total_deductions"])),
        ("employer_cost_differs_from_gross_plus_employer_contributions", near(p["employer_cost"], p["gross_pay"] + p["pf_employer"] + p["esi_employer"])),
        ("payable_days_over_31", p["payable_days"] > 31),
        ("overtime_hours_over_cap_of_50", p["overtime_hours_paid"] > 50),
        ("run_id_differs_from_period", p["run_id"] != "PR-" + p["period_end_date"].dt.strftime("%Y-%m")),
        ("variable_pay_without_type", (p["variable_pay"] > 0) & p["variable_pay_type"].isna()),
    ]
    rules += _period_rules(p) + _employee_rules(p, ctx, with_role=True) + _duplicate_rules(p, spec)
    good, rejected = _route("fact_payroll", raw, p, rules)
    _add_month_helpers(good, "period_end_date")
    good["month_start"] = good["period_end_date"].dt.to_period("M").dt.to_timestamp().astype("datetime64[ns]")
    return TableResult("fact_payroll", raw, good, rejected, filled)


# ---------- fact_attendance_monthly ----------

def transform_attendance(raw, ctx: Ctx) -> TableResult:
    spec = SPECS["fact_attendance_monthly"]
    p, rules, raw = _parse(raw, spec, ctx.dayfirst)
    num_cols = ["scheduled_days", "present_days", "wfh_days", "half_days_unpaid", "paid_leave_days",
                "unpaid_absence_days", "late_arrivals", "avg_hours_worked", "overtime_hours", "attendance_rate"]
    expected_rate = ((p["present_days"] + 0.5 * p["half_days_unpaid"]) / p["scheduled_days"].where(p["scheduled_days"] > 0))
    rules += [
        ("negative_value", (p[num_cols] < 0).any(axis=1)),
        ("scheduled_days_over_31", p["scheduled_days"] > 31),
        ("present_exceeds_scheduled", p["present_days"] > p["scheduled_days"]),
        ("wfh_exceeds_present", p["wfh_days"] > p["present_days"]),
        ("avg_hours_over_24", p["avg_hours_worked"] > 24),
        ("attendance_rate_outside_0_to_1", (p["attendance_rate"] < 0) | (p["attendance_rate"] > 1)),
        ("attendance_rate_differs_from_days", (p["attendance_rate"] - expected_rate).abs() > 0.01),
    ]
    rules += _period_rules(p) + _employee_rules(p, ctx) + _duplicate_rules(p, spec)
    good, rejected = _route("fact_attendance_monthly", raw, p, rules)
    _add_month_helpers(good, "period_end_date")
    good["month_start"] = good["period_end_date"].dt.to_period("M").dt.to_timestamp().astype("datetime64[ns]")
    return TableResult("fact_attendance_monthly", raw, good, rejected)


# ---------- fact_leave ----------

def transform_leave(raw, ctx: Ctx) -> TableResult:
    spec = SPECS["fact_leave"]
    p, rules, raw = _parse(raw, spec, ctx.dayfirst)

    # Repair: start and end dates swapped, and the two date keys confirm the original order.
    swapped = ((p["end_date"] < p["start_date"])
               & (_date_key(p["end_date"]) == p["start_date_key"].astype("float64"))
               & (_date_key(p["start_date"]) == p["end_date_key"].astype("float64")))
    repairs = pd.concat([
        _repair_rows(p.loc[swapped, "source_row"], "start_date", p.loc[swapped, "start_date"], p.loc[swapped, "end_date"], "swapped_dates_confirmed_by_date_keys"),
        _repair_rows(p.loc[swapped, "source_row"], "end_date", p.loc[swapped, "end_date"], p.loc[swapped, "start_date"], "swapped_dates_confirmed_by_date_keys"),
    ], ignore_index=True)
    p.loc[swapped, ["start_date", "end_date"]] = p.loc[swapped, ["end_date", "start_date"]].to_numpy()

    emp = ctx.employees
    ver = emp.set_index("employee_key")["employee_id"]
    key_owner = p["employee_key"].map(ver)
    rules += [
        ("end_before_start", p["end_date"] < p["start_date"]),
        ("days_not_positive", p["days"] <= 0),
        ("start_date_key_differs_from_start_date", p["start_date_key"].astype("float64") != _date_key(p["start_date"])),
        ("end_date_key_differs_from_end_date", p["end_date_key"].astype("float64") != _date_key(p["end_date"])),
        ("decided_before_applied", p["decided_on"] < p["applied_on"]),
        ("missing_decision_date", p["decided_on"].isna() & (p["status"] != "Pending")),
        ("unknown_leave_type", ~p["leave_type_code"].isin(ctx.leave_types)),
        ("unknown_employee", ~p["employee_id"].isin(set(emp["employee_id"]))),
        ("unknown_employee_key", key_owner.isna()),
        ("employee_key_belongs_to_other_employee", key_owner.notna() & (key_owner != p["employee_id"])),
    ] + _duplicate_rules(p, spec)
    good, rejected = _route("fact_leave", raw, p, rules)
    repairs = repairs[repairs["source_row"].isin(good["source_row"])].reset_index(drop=True)

    good["calendar_days"] = (good["end_date"] - good["start_date"]).dt.days + 1
    good["start_year"] = good["start_date"].dt.year
    good["start_month"] = good["start_date"].dt.month
    no_approver = good["approver_id"].isna() & (good["status"].isin(["Approved", "Rejected"]))
    warnings = {"decided_without_approver": int(no_approver.sum())} if no_approver.any() else {}
    return TableResult("fact_leave", raw, good, rejected, {}, repairs, warnings)


TRANSFORMS = {
    "dim_date": transform_date,
    "dim_department": transform_department,
    "dim_role": transform_role,
    "dim_leave_type": transform_leave_type,
    "dim_employee": transform_employee,
    "fact_payroll": transform_payroll,
    "fact_attendance_monthly": transform_attendance,
    "fact_leave": transform_leave,
}


def infer_as_of(raw: dict, dayfirst: bool) -> pd.Timestamp:
    """Reference date when AS_OF_DATE is not set: latest period in payroll and attendance."""
    dates = [to_date(raw[t]["period_end_date"], dayfirst).max() for t in ("fact_payroll", "fact_attendance_monthly")]
    dates.append(to_date(raw["dim_employee"]["hire_date"], dayfirst).max())
    latest = max((d for d in dates if pd.notna(d)), default=None)
    if latest is None:
        raise ValueError("Cannot infer a reference date. Set AS_OF_DATE.")
    return latest
