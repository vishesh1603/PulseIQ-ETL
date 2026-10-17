import hashlib
import json
import os
from pathlib import Path

import pandas as pd
import pytest

from make_sample_data import main as make_sample
from pulseiq_etl.config import Settings
from pulseiq_etl.errors import ValidationFailed
from pulseiq_etl.pipeline import run
from pulseiq_etl.validate import validate_all

CLEAN_TABLES = ["dim_date", "dim_department", "dim_role", "dim_leave_type", "dim_employee",
                "fact_payroll", "fact_attendance_monthly", "fact_leave"]


def settings_for(tmp_path: Path, **kw) -> Settings:
    return Settings(raw_dir=tmp_path / "raw", clean_dir=tmp_path / "clean",
                    rejected_dir=tmp_path / "rejected", log_dir=tmp_path / "logs", **kw)


@pytest.fixture
def sample(tmp_path):
    make_sample(tmp_path / "raw")
    return tmp_path


def digest(folder: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(folder.glob("*.parquet")):
        h.update(f.name.encode() + f.read_bytes())
    return h.hexdigest()


def last_run(s: Settings) -> dict:
    return json.loads((s.log_dir / "last_run.json").read_text())


def reasons(s: Settings, table: str) -> pd.DataFrame:
    return pd.read_csv(s.rejected_dir / f"{table}_rejected.csv")


def test_runs_and_is_repeatable(sample):
    s = settings_for(sample)
    assert run(s) == 0
    first = digest(s.clean_dir)
    assert run(s) == 0
    assert digest(s.clean_dir) == first
    assert last_run(s)["identical_to_previous_run"] is True
    assert len(list(s.clean_dir.glob("*.parquet"))) == len(CLEAN_TABLES)


def test_rows_add_up_and_audit_files_match_the_log(sample):
    s = settings_for(sample)
    assert run(s) == 0
    for name, t in last_run(s)["tables"].items():
        assert t["rows_in"] == t["rows_out"] + t["rows_rejected"]
        assert len(reasons(s, name)) == t["rows_rejected"]
        assert len(pd.read_csv(s.rejected_dir / f"{name}_repaired.csv")) == t["values_repaired"]


def test_every_planted_defect_is_caught(sample):
    s = settings_for(sample)
    run(s)
    pay = reasons(s, "fact_payroll").reject_reason.str.split(";").explode().value_counts()
    assert pay["exact_duplicate"] == 2
    assert pay["net_pay_differs_from_gross_minus_deductions"] == 1
    assert pay["unknown_employee"] >= 2
    att = reasons(s, "fact_attendance_monthly").reject_reason.str.split(";").explode().value_counts()
    assert att["activity_after_exit_month"] == 2
    assert reasons(s, "fact_leave").reject_reason.tolist() == ["end_before_start"]
    assert len(pd.read_csv(s.rejected_dir / "fact_leave_repaired.csv")) == 4  # 2 rows x 2 date columns
    emp_repairs = pd.read_csv(s.rejected_dir / "dim_employee_repaired.csv")
    assert emp_repairs.rule.tolist() == ["overlapping_version_closed"]


def test_exit_before_hire_is_rejected_and_history_follows(sample):
    s = settings_for(sample)
    run(s)
    bad = reasons(s, "dim_employee")
    assert set(bad.employee_id) == {"EMP-0003"} and (bad.reject_reason == "exit_before_hire").all()
    for table in ("fact_payroll", "fact_attendance_monthly", "fact_leave"):
        clean = pd.read_parquet(s.clean_dir / f"{table}.parquet")
        assert "EMP-0003" not in set(clean.employee_id)
    assert (reasons(s, "fact_payroll").query("employee_id == 'EMP-0003'").reject_reason.str.contains("unknown_employee")).all()


def test_overlap_repair_makes_history_contiguous(sample):
    s = settings_for(sample)
    run(s)
    emp = pd.read_parquet(s.clean_dir / "dim_employee.parquet").query("employee_id == 'EMP-0002'").sort_values("valid_from")
    assert emp.valid_to.iloc[0] == emp.valid_from.iloc[1] - pd.Timedelta(days=1)


def test_open_ended_versions_have_blank_valid_to(sample):
    s = settings_for(sample)
    run(s)
    emp = pd.read_parquet(s.clean_dir / "dim_employee.parquet")
    active = emp[emp.is_active & (emp.is_current == "Y")]
    assert active.valid_to.isna().all() and len(active) > 0


def test_pandera_fails_loudly_on_bad_data(sample):
    s = settings_for(sample)
    run(s)
    clean = {n: pd.read_parquet(s.clean_dir / f"{n}.parquet") for n in CLEAN_TABLES}
    clean["fact_payroll"].loc[0, "net_pay"] = -1
    clean["dim_employee"].loc[1, "employee_key"] = clean["dim_employee"].loc[0, "employee_key"]
    clean["fact_leave"].loc[0, "status"] = "Maybe"
    with pytest.raises(ValidationFailed) as exc:
        validate_all(clean)
    msg = str(exc.value)
    assert "net_pay" in msg and "employee_key" in msg and "status" in msg


def test_too_many_rejects_stops_the_run_and_keeps_old_output(sample):
    s = settings_for(sample)
    assert run(s) == 0
    before = digest(s.clean_dir)
    strict = settings_for(sample, max_reject_pct=1.0)
    assert run(strict) == 1
    assert digest(strict.clean_dir) == before
    assert last_run(s)["status"] == "FAILED"


def test_missing_required_column_fails_clearly(sample):
    s = settings_for(sample)
    path = s.raw_dir / "fact_payroll.csv"
    pd.read_csv(path).drop(columns=["net_pay"]).to_csv(path, index=False)
    assert run(s) == 1
    assert "net_pay" in last_run(s)["error"]


# Runs only when the real workbook is available: PULSEIQ_WORKBOOK=/path/to/PulseIQ_Star_Schema_Dataset.xlsx
WORKBOOK = os.environ.get("PULSEIQ_WORKBOOK")


@pytest.mark.skipif(not WORKBOOK or not Path(WORKBOOK).exists(), reason="set PULSEIQ_WORKBOOK to run")
def test_real_workbook_matches_the_answer_key(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / Path(WORKBOOK).name).symlink_to(Path(WORKBOOK).resolve())
    s = settings_for(tmp_path)
    assert run(s) == 0
    info = last_run(s)
    assert info["reconciliation"]["status"] == "PASS" and info["reconciliation"]["months_checked"] == 18
    assert info["tables"]["fact_payroll"]["rows_rejected"] == 4
    assert info["tables"]["fact_attendance_monthly"]["rows_rejected"] == 4
    assert info["tables"]["dim_employee"]["values_repaired"] == 1
    assert info["tables"]["fact_leave"]["values_repaired"] == 4
    first = digest(s.clean_dir)
    assert run(s) == 0 and digest(s.clean_dir) == first
