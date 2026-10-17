"""Foundation Phase (Phase 1: Tasks 1-4) Consolidated Verification Script.

Executes all reference checks and proof criteria specified in the Data Analyst Guide:
- Task 2 proofs: Payroll PR-2025-04 cost, PR-2026-09 employee count, 745/441/1606 employee counts.
- Task 3 proofs: Headcount, joiners, leavers, and attrition rate for Sep 2026.
- Task 4 proofs: Engineering Apr 2025 attendance checkpoint (0.9509), Sep 2026 KPIs,
                 anomaly row counts & referential integrity, weekday leave constraints.
"""
import os
import sys
import psycopg

WAREHOUSE_DSN = os.environ.get(
    "WAREHOUSE_DSN",
    "postgresql://pulseiq:pulseiq@localhost:5433/pulseiq"
)

def run_checks():
    print("=" * 70)
    print("PULSEIQ FOUNDATION PHASE (PHASE 1: TASKS 1-4) VERIFICATION SUITE")
    print("=" * 70)
    
    failures = []

    with psycopg.connect(WAREHOUSE_DSN) as conn:
        with conn.cursor() as cur:
            # ----------------------------------------------------
            # Task 2 Proofs: Payroll & Employee Integrity
            # ----------------------------------------------------
            print("\n[TASK 2] Checking Warehouse Facts and Dimensions...")
            
            # Check 1: PR-2025-04 Employer Cost
            cur.execute("""
                SELECT sum(employer_cost) 
                FROM dw.fact_payroll 
                WHERE date_key = 20250430;
            """)
            pr_2025_04_cost = float(cur.fetchone()[0])
            expected_cost = 53363392.08
            diff = abs(pr_2025_04_cost - expected_cost)
            if diff < 0.01:
                print(f"  [PASS] PR-2025-04 Employer Cost = ₹{pr_2025_04_cost:,.2f} (matches {expected_cost:,.2f})")
            else:
                failures.append(f"PR-2025-04 Cost mismatch: got {pr_2025_04_cost}, expected {expected_cost}")
                print(f"  [FAIL] PR-2025-04 Employer Cost mismatch!")

            # Check 2: PR-2026-09 Employees Paid
            cur.execute("""
                SELECT count(DISTINCT employee_id), sum(gross_pay), sum(employer_cost)
                FROM dw.fact_payroll 
                WHERE date_key = 20260930;
            """)
            paid_emp, gross_pay, emp_cost = cur.fetchone()
            if paid_emp == 444 and abs(float(gross_pay) - 54788660.03) < 0.01:
                print(f"  [PASS] PR-2026-09 Employees Paid = {paid_emp}, Gross = ₹{float(gross_pay):,.2f}")
            else:
                failures.append(f"PR-2026-09 Paid Employees mismatch: got {paid_emp}, expected 444")
                print(f"  [FAIL] PR-2026-09 Employees mismatch!")

            # Check 3: Employee Counts (745 total, 441 active, 1606 versions)
            cur.execute("""
                SELECT 
                    count(DISTINCT employee_id),
                    count(DISTINCT employee_id) FILTER (WHERE is_active),
                    count(*)
                FROM dw.dim_employee;
            """)
            tot_emp, act_emp, tot_ver = cur.fetchone()
            if tot_emp == 745 and act_emp == 441 and tot_ver == 1606:
                print(f"  [PASS] dim_employee Counts = {tot_emp} total / {act_emp} active / {tot_ver} versions")
            else:
                failures.append(f"Employee counts mismatch: {tot_emp}/{act_emp}/{tot_ver}, expected 745/441/1606")
                print(f"  [FAIL] Employee counts mismatch!")

            # ----------------------------------------------------
            # Task 3 Proofs: Headcount & Departments KPIs
            # ----------------------------------------------------
            print("\n[TASK 3] Checking Headcount & Demographics Dashboard Metrics...")
            cur.execute("""
                SELECT 
                    sum(headcount_end),
                    sum(hires),
                    sum(exits),
                    round(sum(exits)::numeric / nullif(sum(headcount_start), 0) * 100, 2)
                FROM dw.fact_headcount_monthly
                WHERE date_key = 20260930;
            """)
            hc_end, hires, exits, attr_rate = cur.fetchone()
            if hc_end == 441 and hires == 17 and exits == 3 and float(attr_rate) == 0.70:
                print(f"  [PASS] Sep 2026 Headcount = {hc_end}, Hires = {hires}, Exits = {exits}, Attrition = {attr_rate}%")
            else:
                failures.append(f"Task 3 KPI mismatch: {hc_end}/{hires}/{exits}/{attr_rate}")
                print(f"  [FAIL] Task 3 KPIs mismatch!")

            # ----------------------------------------------------
            # Task 4 Proofs: Attendance, Leaves & Anomaly Metrics
            # ----------------------------------------------------
            print("\n[TASK 4] Checking Attendance, Leaves & AI Anomalies...")
            
            # Check 1: M13 Engineering Apr 2025 Checkpoint (0.9509)
            cur.execute("""
                SELECT round((sum(f.present_days) + 0.5 * sum(f.half_days_unpaid)) / sum(f.scheduled_days), 4)
                FROM dw.fact_attendance_monthly f
                JOIN dw.dim_department d ON d.department_key = f.department_key
                JOIN dw.dim_date dt ON dt.date_key = f.date_key
                WHERE d.department_id = 'D01' AND dt.year_month = '2025-04';
            """)
            eng_att_rate = float(cur.fetchone()[0])
            if eng_att_rate == 0.9509:
                print(f"  [PASS] M13 Engineering Apr 2025 Checkpoint = {eng_att_rate} (exact match)")
            else:
                failures.append(f"M13 Checkpoint mismatch: got {eng_att_rate}, expected 0.9509")
                print(f"  [FAIL] M13 Engineering Checkpoint mismatch!")

            # Check 2: Sep 2026 Attendance KPIs
            cur.execute("""
                SELECT 
                    round((sum(present_days) + 0.5 * sum(half_days_unpaid)) / sum(scheduled_days) * 100, 1),
                    round(sum(late_arrivals)::numeric / sum(present_days) * 100, 1),
                    round(sum(unpaid_absence_days + 0.5 * half_days_unpaid), 1),
                    (SELECT count(*) FROM dw.fact_anomaly WHERE period_key = 20260930 AND source_dataset = 'attendance_monthly_features')
                FROM dw.fact_attendance_monthly
                WHERE date_key = 20260930;
            """)
            att_pct, late_pct, lop_days, anom_cnt = cur.fetchone()
            if float(att_pct) == 95.2 and float(late_pct) == 7.1 and float(lop_days) == 85.5 and anom_cnt == 10:
                print(f"  [PASS] Sep 2026 Attendance = {att_pct}%, Late Rate = {late_pct}%, LOP = {lop_days}d, Anomalies = {anom_cnt}")
            else:
                failures.append(f"Sep 2026 Attendance KPI mismatch: {att_pct}/{late_pct}/{lop_days}/{anom_cnt}")
                print(f"  [FAIL] Sep 2026 Attendance KPIs mismatch!")

            # Check 3: AI Anomaly Rows & Referential Integrity
            cur.execute("SELECT count(*) FROM dw.fact_anomaly;")
            total_anom = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM dw.fact_anomaly WHERE source_dataset = 'attendance_monthly_features';")
            att_anom = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM dw.fact_anomaly WHERE source_dataset = 'payroll_monthly_features';")
            pay_anom = cur.fetchone()[0]
            cur.execute("""
                SELECT count(*) 
                FROM dw.fact_anomaly a
                LEFT JOIN dw.dim_date d ON d.date_key = a.period_key
                WHERE d.date_key IS NULL;
            """)
            orphan_anom = cur.fetchone()[0]

            if total_anom == 405 and att_anom == 221 and pay_anom == 184 and orphan_anom == 0:
                print(f"  [PASS] fact_anomaly = {total_anom} total ({att_anom} attendance, {pay_anom} payroll, 0 orphans)")
            else:
                failures.append(f"Anomaly counts mismatch: total={total_anom}, att={att_anom}, pay={pay_anom}, orphans={orphan_anom}")
                print(f"  [FAIL] fact_anomaly counts mismatch!")

            # Check 4: Weekday Leave Distribution Constraints
            cur.execute("""
                SELECT 
                    count(*),
                    count(*) FILTER (WHERE d.day_of_week IN ('Saturday', 'Sunday')),
                    count(*) FILTER (WHERE d.day_of_week = 'Friday'),
                    count(*) FILTER (WHERE d.day_of_week = 'Monday')
                FROM dw.fact_leave f
                JOIN dw.dim_date d ON d.date_key = f.start_date_key;
            """)
            tot_leave, weekend_leave, fri_leave, mon_leave = cur.fetchone()
            if tot_leave == 3441 and weekend_leave == 0 and fri_leave == 720 and mon_leave == 649:
                print(f"  [PASS] fact_leave = {tot_leave} requests (Mon-Fri only; Fri={fri_leave}, Mon={mon_leave})")
            else:
                failures.append(f"Leave distribution mismatch: total={tot_leave}, weekend={weekend_leave}")
                print(f"  [FAIL] fact_leave distribution mismatch!")

    print("\n" + "=" * 70)
    if not failures:
        print("ALL FOUNDATION PHASE (PHASE 1) CHECKS PASSED PERFECTLY!")
        print("=" * 70)
        return 0
    else:
        print(f"FAILURES DETECTED ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(run_checks())
