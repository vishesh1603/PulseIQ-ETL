# PulseIQ metric dictionary

Started in Task 1 with five metrics. The IDs (M01, M04 and so on) come from the `metric_dictionary` sheet of the star-schema workbook, so this file and the workbook use the same names. The formulas below are written against the clean tables in `data/clean/`.

Each metric was checked against numbers in the workbook (`fact_headcount_monthly`, `reference_summary_dept_month`, `reconciliation_answer_key`). The last column shows one of those checks.

| ID | Metric | Business question | Formula on the clean tables | Grain | Edge cases | Check value |
|----|--------|-------------------|-----------------------------|-------|-----------|-------------|
| M01 | Headcount | How many people work here on the last day of a month? | Count distinct `employee_id` in `dim_employee` where `hire_date <= month_end` and (`exit_date` is blank or `exit_date > month_end`) | Department x month | `dim_employee` has one row per version, so always count distinct `employee_id`. For a department, use the version whose `valid_from <= month_end <= valid_to` (blank `valid_to` means still open). Contract staff count. | 380 on 30 Apr 2025, 441 on 30 Sep 2026 (matches `fact_headcount_monthly`) |
| M04 | Attrition rate (monthly) | What share of people left in the month? | Employees with `exit_date` in the month / headcount on the last day of the previous month x 100 | Department x month | Includes resignations, terminations and contract ends. Aggregates for small groups can be unstable, see `minimum_group_size` in the workbook's metric sheet. | Mar 2026: 6 / 409 x 100 = 1.47 |
| M07 | Gross pay | How much did employees earn before deductions? | Sum of `gross_pay` in `fact_payroll` for the month | Employee x month | Rows rejected by the pipeline are not included. Check `rows_rejected` in `logs/last_run.json` before quoting a total. | Apr 2025: 52,740,110.43 (matches `reconciliation_answer_key`) |
| M09 | Payroll cost (employer cost) | What do employees cost the company? | Sum of `employer_cost` in `fact_payroll` for the month. `employer_cost = gross_pay + pf_employer + esi_employer` | Employee x month | Same as M07. Cost per head (M10) divides by distinct `employee_id`, not by row count. | Apr 2025: 53,363,392.08 across 386 employees |
| M13 | Attendance rate | How often do people turn up? | (sum of `present_days` + 0.5 x sum of `half_days_unpaid`) / sum of `scheduled_days` in `fact_attendance_monthly` | Department x month | Always divide the sums, never average the per-row `attendance_rate` column. `present_days` already includes work from home. | Engineering (D01), Apr 2025: 0.9509 (matches `reference_summary_dept_month`) |
| M14 | Late arrival rate | How often do present employees check in late? | `sum(late_arrivals) / sum(present_days)` in `fact_attendance_monthly` | Department x month | WFH days evaluate check-in timestamp against schedule start. Zero present days yields NULL. | Sep 2026: 7.1% (company-wide) |
| M15 | Leave without pay days | What is the total volume of unpaid absences and leaves? | `sum(unpaid_absence_days + 0.5 * half_days_unpaid)` in `fact_attendance_monthly` | Department x month | Half-day unpaid counts 0.5 days. Also tracked as `sum(lop_days)` in `fact_payroll`. | Sep 2026: 85.5 days (company-wide) |
| M26 | Anomaly flag rate | How many records did AI flag for behavioral or pattern anomalies? | `count(flagged = 'Y')` in `fact_anomaly` | Source x month | Flags are operational leads for HR inquiry, not proof of misconduct. | Sep 2026: 10 attendance flags; 221 total attendance flags across 18 months |

## Warehouse SQL

Task 2 and Task 4 add these metrics as direct queries on the warehouse.

| ID | Metric | SQL |
|----|--------|-----|
| M01 | Headcount | `headcount_end` in `dw.fact_headcount_monthly` (query `q2_headcount_by_department_month.sql`) |
| M04 | Attrition rate (monthly) | `attrition_rate_monthly_pct` in `dw.fact_headcount_monthly` |
| M07 | Gross pay | `sum(gross_pay)` from `dw.fact_payroll` grouped by `dw.dim_date.year_month` |
| M09 | Payroll cost | `sum(employer_cost)` from `dw.fact_payroll` (query `q1_cost_by_department_month.sql`) |
| M13 | Attendance rate | `(sum(present_days) + 0.5 * sum(half_days_unpaid)) / nullif(sum(scheduled_days), 0)` from `dw.fact_attendance_monthly` |
| M14 | Late arrival rate | `sum(late_arrivals)::numeric / nullif(sum(present_days), 0)` from `dw.fact_attendance_monthly` |
| M15 | Leave without pay days | `sum(unpaid_absence_days + 0.5 * half_days_unpaid)` from `dw.fact_attendance_monthly` |
| M26 | Anomaly flags | `count(*)` from `dw.fact_anomaly WHERE source_dataset = 'attendance_monthly_features'` |

## Change log

- Task 1: five metrics defined and checked against the workbook.
- Task 2: warehouse SQL added for the same five metrics.
- Task 4: added attendance metrics M13, M14, M15 and AI anomaly metric M26 with verified SQL and checkpoints.
