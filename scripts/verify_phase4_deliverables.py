"""
PulseIQ Phase 4 — Automated Verification Suite
Task 20-B: 5 tests covering all Phase 4 deliverables.

Usage:
    python scripts/verify_phase4_deliverables.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PG_CONN = os.getenv("WAREHOUSE_DSN", "postgresql://pulseiq:pulseiq@localhost:5433/pulseiq")

PASS = "\033[92m PASS \033[0m"
FAIL = "\033[91m FAIL \033[0m"
INFO = "\033[94m INFO \033[0m"
WARN = "\033[93m WARN \033[0m"

results: list[tuple[str, bool, str]] = []


def check(name: str, passed: bool, detail: str = "") -> bool:
    tag = PASS if passed else FAIL
    print(f"  [{tag}] {name}")
    if detail:
        print(f"         {detail}")
    results.append((name, passed, detail))
    return passed


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1 — Task 16: Pipeline Automation & Scheduling
# ─────────────────────────────────────────────────────────────────────────────
def test_task16_scheduler() -> None:
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("TEST 1 — Task 16: Pipeline Automation & Scheduling")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # 1a: scheduler.py exists and is importable
    sched_path = PROJECT_ROOT / "scripts" / "scheduler.py"
    exists = sched_path.exists()
    check("scheduler.py exists", exists, str(sched_path))

    if exists:
        try:
            spec = importlib.util.spec_from_file_location("scheduler", sched_path)
            mod = importlib.util.load_module_from_spec(spec)   # type: ignore
            spec.loader.exec_module(mod)                       # type: ignore
            check("scheduler.py imports without error", True)
        except Exception as exc:
            check("scheduler.py imports without error", False, str(exc))

    # 1b: run_etl_now.ps1 exists
    ps1_path = PROJECT_ROOT / "scripts" / "run_etl_now.ps1"
    check("run_etl_now.ps1 exists", ps1_path.exists(), str(ps1_path))

    # 1c: docker-compose.yml has scheduler service
    compose_path = PROJECT_ROOT / "docker-compose.yml"
    if compose_path.exists():
        content = compose_path.read_text(encoding="utf-8")
        has_scheduler_svc = "scheduler:" in content and "scripts/scheduler.py" in content
        check(
            "docker-compose.yml contains scheduler service",
            has_scheduler_svc,
            "Look for 'scheduler:' block with command scripts/scheduler.py"
        )
    else:
        check("docker-compose.yml exists", False)

    # 1d: logs/scheduler.log exists (may be empty if never run — just check presence or --run-now works)
    sched_log = PROJECT_ROOT / "logs" / "scheduler.log"
    if not sched_log.exists():
        # Try to create it via --run-now (soft test)
        print(f"  [{INFO}] scheduler.log not yet created — testing --run-now import path only")
        check(
            "scheduler --run-now flag defined",
            exists and "run_now" in sched_path.read_text(encoding="utf-8"),
            "The --run-now argument must be present in scheduler.py"
        )
    else:
        entries = [
            json.loads(line) for line in sched_log.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        check(
            f"scheduler.log has entries ({len(entries)} lines)",
            len(entries) >= 1,
            str(sched_log)
        )


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2 — Task 17: Production Hardening & RBAC
# ─────────────────────────────────────────────────────────────────────────────
def test_task17_rbac() -> None:
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("TEST 2 — Task 17: Production Hardening & RBAC")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # 2a: sql files exist
    for fname in ["006_rbac.sql", "007_dq_monitoring.sql"]:
        path = PROJECT_ROOT / "sql" / fname
        check(f"sql/{fname} exists", path.exists(), str(path))

    # 2b: RBAC SQL contains the 3 required roles
    rbac_path = PROJECT_ROOT / "sql" / "006_rbac.sql"
    if rbac_path.exists():
        content = rbac_path.read_text(encoding="utf-8")
        for role in ["role_hr", "role_finance", "role_executive"]:
            check(f"006_rbac.sql defines {role}", role in content)

    # 2c: PostgreSQL roles exist (requires DB connection)
    try:
        import psycopg
        conn = psycopg.connect(PG_CONN)
        with conn.cursor() as cur:
            cur.execute("SELECT rolname FROM pg_roles WHERE rolname IN ('role_hr','role_finance','role_executive')")
            found_roles = {row[0] for row in cur.fetchall()}
        conn.close()

        for role in ["role_hr", "role_finance", "role_executive"]:
            check(
                f"PostgreSQL role '{role}' exists in pg_roles",
                role in found_roles,
                "Run: psql -U pulseiq -d pulseiq -f sql/006_rbac.sql" if role not in found_roles else ""
            )
    except Exception as exc:
        print(f"  [{WARN}] Cannot connect to warehouse to verify roles: {exc}")
        print(f"  [{INFO}] Make sure Docker warehouse is running: docker compose up -d warehouse")

    # 2d: dw.dq_check_log table exists and has >=14 rows
    try:
        import psycopg
        conn = psycopg.connect(PG_CONN)
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('dw.dq_check_log')")
            exists = cur.fetchone()[0] is not None
            check("dw.dq_check_log table exists", exists,
                  "Run: psql -U pulseiq -d pulseiq -f sql/007_dq_monitoring.sql")

            if exists:
                cur.execute("SELECT COUNT(*) FROM dw.dq_check_log")
                count = cur.fetchone()[0]
                check(
                    f"dw.dq_check_log has DQ results ({count} rows)",
                    count >= 14,
                    f"Run: python scripts/run_all_14_dq_checks.py (found {count} rows, need >=14)"
                )
        conn.close()
    except Exception as exc:
        print(f"  [{WARN}] DB check skipped: {exc}")

    # 2e: run_all_14_dq_checks.py has persistence code
    dq_path = PROJECT_ROOT / "scripts" / "run_all_14_dq_checks.py"
    if dq_path.exists():
        content = dq_path.read_text(encoding="utf-8")
        check(
            "run_all_14_dq_checks.py persists to dw.dq_check_log",
            "_persist_results" in content and "dq_check_log" in content
        )


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3 — Task 18: KPI Alerting & Webhook Notifications
# ─────────────────────────────────────────────────────────────────────────────
def test_task18_alerting() -> None:
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("TEST 3 — Task 18: KPI Alerting & Webhook Notifications")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # 3a: alerting.py exists and imports
    alert_path = PROJECT_ROOT / "scripts" / "alerting.py"
    exists = alert_path.exists()
    check("alerting.py exists", exists, str(alert_path))

    if exists:
        try:
            spec = importlib.util.spec_from_file_location("alerting", alert_path)
            mod = importlib.util.load_module_from_spec(spec)   # type: ignore
            spec.loader.exec_module(mod)                       # type: ignore
            has_fn = hasattr(mod, "run_all_kpi_checks")
            check("alerting.py defines run_all_kpi_checks()", has_fn)
            if has_fn:
                n_rules = len(mod.ALERT_RULES)
                check(f"alerting.py has KPI rules (found {n_rules})", n_rules >= 5)
        except Exception as exc:
            check("alerting.py imports without error", False, str(exc))

    # 3b: sql/008_alert_log.sql exists
    sql_path = PROJECT_ROOT / "sql" / "008_alert_log.sql"
    check("sql/008_alert_log.sql exists", sql_path.exists())

    # 3c: dw.alert_log table exists in DB
    try:
        import psycopg
        conn = psycopg.connect(PG_CONN)
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('dw.alert_log')")
            exists_in_db = cur.fetchone()[0] is not None
            check("dw.alert_log table exists in warehouse", exists_in_db,
                  "Run: psql -U pulseiq -d pulseiq -f sql/008_alert_log.sql")
        conn.close()
    except Exception as exc:
        print(f"  [{WARN}] DB check skipped: {exc}")

    # 3d: pages/11_Alert_Log.py exists
    page_path = PROJECT_ROOT / "pages" / "11_Alert_Log.py"
    check("pages/11_Alert_Log.py exists", page_path.exists())

    # 3e: Run alerting in dry-run mode — no DB writes
    if alert_path.exists():
        try:
            spec = importlib.util.spec_from_file_location("alerting2", alert_path)
            mod2 = importlib.util.load_module_from_spec(spec)  # type: ignore
            spec.loader.exec_module(mod2)                       # type: ignore
            triggered = mod2.run_all_kpi_checks(dry_run=True)
            check(
                f"alerting dry-run completed ({len(triggered)} breach(es) detected)",
                True,  # success = no crash
                f"{'No breaches — all KPIs on target' if not triggered else str([a['metric_code'] for a in triggered])}"
            )
        except Exception as exc:
            check("alerting dry-run completed without crash", False, str(exc))

    # 3f: logs/alerts.log exists (created by alerting)
    alerts_log = PROJECT_ROOT / "logs" / "alerts.log"
    check(
        "logs/alerts.log exists",
        alerts_log.exists(),
        "Will be created on first alerting run"
    )


# ─────────────────────────────────────────────────────────────────────────────
# TEST 4 — Task 19: Metric Lineage Catalog & Self-Service Docs
# ─────────────────────────────────────────────────────────────────────────────
def test_task19_lineage() -> None:
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("TEST 4 — Task 19: Metric Lineage Catalog & Self-Service Docs")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # 4a: docs/metric_lineage_catalog.md exists and contains all M codes
    catalog_path = PROJECT_ROOT / "docs" / "metric_lineage_catalog.md"
    exists = catalog_path.exists()
    check("docs/metric_lineage_catalog.md exists", exists)

    if exists:
        content = catalog_path.read_text(encoding="utf-8")
        # Check for all 29 metric codes M01..M29
        missing = []
        for i in range(1, 30):
            code = f"M{i:02d}"
            if code not in content:
                missing.append(code)
        check(
            f"metric_lineage_catalog.md contains all 29 metric codes",
            len(missing) == 0,
            f"Missing: {missing}" if missing else "All M01–M29 present"
        )

        # Check for RBAC section
        check(
            "metric_lineage_catalog.md has RBAC Access Matrix",
            "RBAC Access Matrix" in content
        )

    # 4b: docs/self_service_guide.md exists
    guide_path = PROJECT_ROOT / "docs" / "self_service_guide.md"
    exists_guide = guide_path.exists()
    check("docs/self_service_guide.md exists", exists_guide)
    if exists_guide:
        guide_content = guide_path.read_text(encoding="utf-8")
        for section in ["Getting Started", "Executive Scorecard", "Drilling Down",
                        "AI Signals", "Frequently Asked Questions"]:
            check(f"self_service_guide.md has section '{section}'", section in guide_content)

    # 4c: pages/0_About_and_Lineage.py exists and is syntactically valid
    page_path = PROJECT_ROOT / "pages" / "0_About_and_Lineage.py"
    exists_page = page_path.exists()
    check("pages/0_About_and_Lineage.py exists", exists_page)
    if exists_page:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(page_path)],
            capture_output=True, text=True
        )
        check(
            "pages/0_About_and_Lineage.py has valid Python syntax",
            result.returncode == 0,
            result.stderr.strip() if result.returncode != 0 else ""
        )


# ─────────────────────────────────────────────────────────────────────────────
# TEST 5 — Task 20: Production Release & Final Report
# ─────────────────────────────────────────────────────────────────────────────
def test_task20_release() -> None:
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("TEST 5 — Task 20: Production Release & Final Report")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # 5a: README.md mentions Phase 4
    readme_path = PROJECT_ROOT / "README.md"
    if readme_path.exists():
        content = readme_path.read_text(encoding="utf-8")
        check("README.md mentions Phase 4", "phase-4" in content.lower() or "Phase 4" in content)
        check("README.md documents RBAC", "role_hr" in content or "RBAC" in content)
        check("README.md documents scheduler", "scheduler" in content.lower())
    else:
        check("README.md exists", False)

    # 5b: Phase 4 PDF report exists (may need to be generated)
    pdf_path = PROJECT_ROOT / "reports" / "DataAnalytics_Vishesh_Phase4_Report.pdf"
    pdf_exists = pdf_path.exists()
    check(
        "DataAnalytics_Vishesh_Phase4_Report.pdf exists",
        pdf_exists,
        "Run: python scripts/generate_phase4_pdf.py" if not pdf_exists else str(pdf_path)
    )

    # 5b2: If PDF exists, check it has reasonable size (> 10 KB)
    if pdf_exists:
        size_kb = pdf_path.stat().st_size / 1024
        check(
            f"PDF has reasonable size ({size_kb:.0f} KB)",
            size_kb > 10,
            f"File: {pdf_path}"
        )

    # 5c: Git tag phase-4 exists
    try:
        result = subprocess.run(
            ["git", "tag", "--list", "phase-4"],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=10
        )
        has_tag = "phase-4" in result.stdout.strip()
        check(
            "git tag 'phase-4' exists",
            has_tag,
            "Run: git tag phase-4 && git push origin main --tags" if not has_tag else ""
        )
    except Exception as exc:
        print(f"  [{WARN}] Could not check git tags: {exc}")

    # 5d: All 12 pages exist
    expected_pages = [
        "0_About_and_Lineage.py",
        "1_Attendance_and_Leave.py",
        "2_Attrition_Analytics.py",
        "3_Team_Productivity.py",
        "4_Payroll_Cost_and_Reconciliation.py",
        "5_Budget_vs_Actual_Variance.py",
        "6_Profit_and_Loss.py",
        "7_Invoices_and_Cash_Flow.py",
        "8_Cross_Department_Impact.py",
        "9_AI_Signals.py",
        "10_Executive_Scorecard.py",
        "11_Alert_Log.py",
    ]
    pages_dir = PROJECT_ROOT / "pages"
    for page in expected_pages:
        check(f"pages/{page} exists", (pages_dir / page).exists())

    # 5e: verify_phase4_deliverables.py itself exists
    verify_path = PROJECT_ROOT / "scripts" / "verify_phase4_deliverables.py"
    check("scripts/verify_phase4_deliverables.py exists", verify_path.exists())


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  PulseIQ Phase 4 — Automated Verification Suite")
    print("  Tasks 16–20: Release and Scale")
    print("=" * 65)

    test_task16_scheduler()
    test_task17_rbac()
    test_task18_alerting()
    test_task19_lineage()
    test_task20_release()

    # Summary
    print("\n" + "=" * 65)
    n_pass = sum(1 for _, ok, _ in results if ok)
    n_fail = sum(1 for _, ok, _ in results if not ok)
    n_total = len(results)
    print(f"  PHASE 4 SUMMARY: {n_pass}/{n_total} checks PASSED | {n_fail} FAILED")
    print("=" * 65)

    if n_fail > 0:
        print("\nFailed checks:")
        for name, ok, detail in results:
            if not ok:
                print(f"  ✗ {name}")
                if detail:
                    print(f"    → {detail}")
        sys.exit(1)
    else:
        print("\n  ✅ All Phase 4 checks passed!")
        sys.exit(0)
