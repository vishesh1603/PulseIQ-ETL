"""Orchestration: extract -> transform -> reject check -> validate -> load, with a run log."""
from __future__ import annotations

import hashlib
import logging

import pandas as pd

from . import transform as t
from .config import RECONCILIATION_SHEET, TABLE_ORDER, Settings
from .errors import ExtractError, PipelineError, RejectThresholdExceeded
from .extract import extract
from .load import write_audit, write_clean
from .run_log import RunLog, setup_logging
from .validate import validate_all
from .warehouse import load_warehouse

log = logging.getLogger(__name__)


def _reason_counts(rejected: pd.DataFrame) -> dict:
    if rejected.empty:
        return {}
    counts = rejected["reject_reason"].str.split(";").explode().value_counts()
    return {k: int(counts[k]) for k in sorted(counts.index)}


def _fingerprint(file_info: dict, settings: Settings, as_of: pd.Timestamp) -> str:
    parts = [f"{k}:{v['sha256']}" for k, v in sorted(file_info.items())]
    parts += [f"as_of:{as_of.date()}", f"fmt:{settings.output_format}", f"dayfirst:{settings.dayfirst}"]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def reconcile(clean: dict, source, settings: Settings) -> dict:
    """Compare monthly payroll totals with the workbook's reconciliation_answer_key, if it is present."""
    if not source.has(RECONCILIATION_SHEET):
        return {"status": "SKIPPED", "reason": f"no '{RECONCILIATION_SHEET}' sheet or csv in {settings.raw_dir}"}
    key, _ = source.read(RECONCILIATION_SHEET)
    key["month"] = pd.to_datetime(key["month"]).dt.to_period("M").dt.to_timestamp()
    cols = {"employees_paid": None, "payroll_gross_pay": "gross_pay", "payroll_net_pay": "net_pay", "payroll_employer_cost": "employer_cost"}
    pay = clean["fact_payroll"]
    mine = pay.groupby("month_start").agg(employees_paid=("employee_id", "nunique"), gross_pay=("gross_pay", "sum"),
                                           net_pay=("net_pay", "sum"), employer_cost=("employer_cost", "sum"))
    mismatches = []
    for _, row in key.iterrows():
        m = row["month"]
        if m not in mine.index:
            mismatches.append({"month": str(m.date()), "problem": "month missing from clean payroll"})
            continue
        for kcol, mcol in cols.items():
            expected = float(row[kcol])
            actual = float(mine.loc[m, mcol or "employees_paid"])
            if abs(expected - actual) > 0.05:
                mismatches.append({"month": str(m.date()), "column": kcol, "expected": expected, "actual": round(actual, 2)})
    result = {"status": "PASS" if not mismatches else "FAIL", "months_checked": len(key), "mismatches": mismatches[:20]}
    log.log(logging.INFO if not mismatches else logging.ERROR,
            "Reconciliation against answer key: %s (%d months, %d mismatches)", result["status"], len(key), len(mismatches))
    if mismatches and settings.reconcile_strict:
        raise PipelineError(f"Payroll totals do not match the reconciliation key: {mismatches[:3]}")
    return result


def _run(settings: Settings, rl: RunLog) -> None:
    # 1. Extract
    raw, file_info, source = extract(settings)
    for name, df in raw.items():
        if df.empty:
            raise ExtractError(f"{file_info[name]['file']} has no data rows.")
    as_of = pd.Timestamp(settings.as_of_date) if settings.as_of_date else t.infer_as_of(raw, settings.dayfirst)
    log.info("Reference date for tenure: %s", as_of.date())
    rl["as_of_date"] = str(as_of.date())
    rl["input_files"] = file_info
    rl["input_fingerprint"] = _fingerprint(file_info, settings, as_of)

    # 2. Transform. Dimensions first: facts are checked against the clean dimensions.
    ctx = t.Ctx(as_of=as_of, dayfirst=settings.dayfirst)
    results: dict[str, t.TableResult] = {}
    for name in TABLE_ORDER:
        results[name] = t.TRANSFORMS[name](raw[name], ctx)
        if name == "dim_department":
            ctx.dept_ids = set(results[name].clean["department_id"])
        elif name == "dim_role":
            ctx.role_ids = set(results[name].clean["role_id"])
        elif name == "dim_leave_type":
            ctx.leave_types = set(results[name].clean["leave_type_code"])
        elif name == "dim_employee":
            ctx.employees = results[name].clean

    # 3. Count, reconcile row counts, save rejected and repaired rows (written even if the run fails later)
    problems = []
    for name, res in results.items():
        n_in, n_rej, n_out = len(raw[name]), len(res.rejected), len(res.clean)
        if n_in != n_rej + n_out:
            raise PipelineError(f"{name}: row count does not add up ({n_in} in, {n_out} out, {n_rej} rejected)")
        pct = round(100 * n_rej / n_in, 2)
        entry = {"rows_in": n_in, "rows_out": n_out, "rows_rejected": n_rej, "rejected_pct": pct,
                 "reject_reasons": _reason_counts(res.rejected), "values_repaired": len(res.repairs),
                 "missing_values_filled": res.filled}
        if res.warnings:
            entry["warnings"] = res.warnings
        rl.data["tables"][name] = entry
        log.info("Transformed %-24s in=%-6d out=%-6d rejected=%-4d repaired=%-3d (%.2f%% rejected)",
                 name, n_in, n_out, n_rej, len(res.repairs), pct)
        if pct > settings.max_reject_pct:
            problems.append(f"{name}: {pct}% rejected, limit is {settings.max_reject_pct}%")
    rl["audit_files"] = write_audit(settings, results)
    if problems:
        raise RejectThresholdExceeded("Too many rejected rows. " + "; ".join(problems))

    # 4. Validate with pandera. Raises ValidationFailed and stops before anything is loaded.
    clean = {n: r.clean.drop(columns="source_row").reset_index(drop=True) for n, r in results.items()}
    clean = validate_all(clean)

    # 5. Check payroll totals against the answer key when the workbook has one
    rl["reconciliation"] = reconcile(clean, source, settings)

    # 6. Load
    rl["outputs"] = write_clean(settings, clean)

    # 6b. Load the warehouse (one transaction: everything is loaded or nothing is)
    if settings.warehouse_dsn:
        rl["warehouse"] = load_warehouse(clean, settings.warehouse_dsn)
    else:
        rl["warehouse"] = {"status": "SKIPPED", "reason": "WAREHOUSE_DSN is not set"}
        log.info("Warehouse load skipped: WAREHOUSE_DSN is not set")

    # 7. Repeatability check against the last successful run
    prev = rl.previous_success()
    if prev and prev.get("input_fingerprint") == rl.data["input_fingerprint"]:
        same = {k: v["sha256"] for k, v in prev.get("outputs", {}).items()} == {k: v["sha256"] for k, v in rl.data["outputs"].items()}
        rl["identical_to_previous_run"] = same
        log.info("Same input as the previous run. Output identical: %s", same)
        if not same:
            log.warning("Output differs for identical input. The pipeline is not repeatable, investigate.")
    else:
        rl["identical_to_previous_run"] = None

    log.info("%-25s %8s %8s %9s %9s", "table", "rows_in", "rows_out", "rejected", "repaired")
    for name, info in rl.data["tables"].items():
        log.info("%-25s %8d %8d %9d %9d", name, info["rows_in"], info["rows_out"], info["rows_rejected"], info["values_repaired"])


def run(settings: Settings) -> int:
    setup_logging(settings.log_dir)
    rl = RunLog(settings.log_dir)
    log.info("PulseIQ ETL run %s started", rl.data["run_id"])
    try:
        _run(settings, rl)
    except PipelineError as exc:
        log.error("Run FAILED: %s", exc)
        rl.finish("FAILED", str(exc))
        return 1
    except Exception as exc:  # unexpected bug: log it, still write the run log
        log.exception("Run crashed")
        rl.finish("FAILED", repr(exc))
        return 2
    rl.finish("SUCCESS")
    log.info("Run SUCCESS in %.1fs", rl.data["duration_seconds"])
    return 0
