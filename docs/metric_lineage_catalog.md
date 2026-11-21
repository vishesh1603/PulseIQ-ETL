# PulseIQ — Metric Lineage Catalog

> **Phase 4 — Task 19** | Author: Vishesh Chaturvedi | Repo: [vishesh1603/PulseIQ-ETL](https://github.com/vishesh1603/PulseIQ-ETL)

This catalog provides complete traceability for every number on the PulseIQ dashboard — from raw source table to business KPI. Every metric in this catalog maps to a governed SQL view in the `dw` schema. No dashboard number is ever computed ad-hoc; all values are sourced exclusively from these views.

---

## How to Read This Catalog

| Column | Meaning |
| :--- | :--- |
| **Code** | Unique metric identifier (M01–M29) used throughout the platform |
| **SQL View** | The PostgreSQL view in `dw` that is the single source of truth |
| **Source Tables** | Raw fact / dimension tables the view reads from |
| **Formula** | Exact computation in business-readable pseudocode |
| **Grain** | The lowest level of detail (rows returned per slice) |
| **Privacy Rule** | Whether small group suppression applies (< N employees → NULL) |
| **Target** | Operational KPI target from `dw.kpi_targets` |
| **Owner** | Team responsible for the metric |

> [!IMPORTANT]
> **Privacy Suppression:** All HR/people metrics suppress values where the group has fewer than the `minimum_group_size` employees (usually 5 or 10). This prevents individual identification. The raw (unsuppressed) column is available to privileged `role_hr` users only.

---

## HR Analytics Metrics (M01 – M06)

| Code | Metric Name | SQL View | Source Tables | Formula | Grain | Privacy | Target | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **M01** | Headcount | `dw.metric_m01_headcount` | `fact_headcount_monthly`, `dim_employee`, `dim_department`, `dim_date` | `COUNT(DISTINCT employee_id) WHERE is_active = TRUE` at month-end | Department × Month | Suppress if headcount_end < 5 | ≥ 420 | HR Analytics |
| **M02** | Hires | `dw.metric_m02_hires` | `fact_headcount_monthly`, `dim_department`, `dim_date` | `COUNT(employee_id) WHERE hire_date IN month` | Department × Month | Suppress if headcount_end < 5 | — | HR Analytics |
| **M03** | Exits | `dw.metric_m03_exits` | `fact_headcount_monthly`, `dim_department`, `dim_date` | `COUNT(employee_id) WHERE exit_date IN month` | Department × Month | Suppress if headcount_end < 5 | — | HR Analytics |
| **M04** | Monthly Attrition Rate | `dw.metric_m04_attrition_rate_monthly` | `fact_headcount_monthly`, `dim_department`, `dim_date` | `exits / headcount_start × 100` | Department × Month | Suppress if headcount_start < 10 | ≤ 3%/mo | HR Analytics |
| **M05** | 12-Month Attrition Rate | `dw.metric_m05_attrition_rate_12m` | `fact_headcount_monthly`, `dim_department`, `dim_date` | `SUM(exits, 12M rolling) / AVG(headcount_end, 12M rolling) × 100` | Department × Month | Suppress if avg_headcount < 10 | ≤ 12% | HR Analytics |
| **M06** | Voluntary Attrition Rate (12M) | `dw.metric_m06_voluntary_attrition_rate_12m` | `fact_headcount_monthly`, `dim_department`, `dim_date` | `SUM(voluntary_exits, 12M) / AVG(headcount_end, 12M) × 100` | Department × Month | Suppress if avg_headcount < 10 | — | HR Analytics |

### Lineage Detail — M05 (12-Month Attrition Rate)
```
dim_date ──────────────────────────────────┐
                                           ▼
fact_headcount_monthly  ──► WINDOW(ROWS 11 PRECEDING AND CURRENT ROW)
     exits (monthly)             SUM(exits)   →  exits_12m
     headcount_end                AVG(HC)    →  avg_headcount_12m
                                           │
                               exits_12m / avg_headcount_12m × 100
                                           │
                             dw.metric_m05_attrition_rate_12m
                                           │
                             Page 2: Attrition Analytics
```

---

## Payroll Metrics (M07 – M12)

| Code | Metric Name | SQL View | Source Tables | Formula | Grain | Privacy | Target | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **M07** | Gross Pay | `dw.metric_m07_gross_pay` | `fact_payroll`, `dim_department`, `dim_date` | `SUM(gross_pay)` — total earnings before deductions | Department × Month | Suppress if employees < 5 | — | Payroll |
| **M08** | Net Pay | `dw.metric_m08_net_pay` | `fact_payroll`, `dim_department`, `dim_date` | `SUM(net_pay)` — take-home after all deductions | Department × Month | Suppress if employees < 5 | — | Payroll |
| **M09** | Payroll Cost (Employer) | `dw.metric_m09_payroll_cost` | `fact_payroll`, `dim_department`, `dim_date` | `SUM(employer_cost)` = gross + employer PF/ESI | Department × Month | Suppress if employees < 5 | — | Finance |
| **M10** | Cost Per Head | `dw.metric_m10_cost_per_head` | `fact_payroll`, `dim_department`, `dim_date` | `SUM(employer_cost) / COUNT(DISTINCT employee_id)` | Department × Month | Suppress if employees < 5 | — | Finance |
| **M11** | Overtime Share | `dw.metric_m11_overtime_share` | `fact_payroll`, `dim_department`, `dim_date` | `SUM(overtime_pay) / SUM(employer_cost) × 100` | Department × Month | Suppress if employees < 5 | — | Payroll |
| **M12** | Variable Pay Share | `dw.metric_m12_variable_pay_share` | `fact_payroll`, `dim_department`, `dim_date` | `SUM(variable_pay) / SUM(gross_pay) × 100` | Department × Month | Suppress if employees < 5 | — | Payroll |

> [!NOTE]
> **Payroll Reconciliation:** The 18-month payroll totals in M07/M09 are verified against `dw.reconciliation_answer_key` on every ETL run. The verified difference is **₹0.00**. 4 dirty rows (PI-X0001 to PI-X0004) are quarantined in `data/rejected/` and excluded from all metrics.

---

## Attendance & Leave Metrics (M13 – M15)

| Code | Metric Name | SQL View | Source Tables | Formula | Grain | Privacy | Target | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **M13** | Attendance Rate | `dw.metric_m13_attendance_rate` | `fact_attendance_monthly`, `dim_department`, `dim_date` | `(SUM(present_days) + 0.5×SUM(half_days_unpaid)) / SUM(scheduled_days)` | Department × Month | Suppress if employees < 5 | ≥ 90% | HR Analytics |
| **M14** | Late Arrival Rate | `dw.metric_m14_late_arrival_rate` | `fact_attendance_monthly`, `dim_department`, `dim_date` | `SUM(late_arrivals) / SUM(present_days)` | Department × Month | Suppress if employees < 5 | — | HR Analytics |
| **M15** | Leave Without Pay (LOP) | `dw.metric_m15_lop_days` | `fact_payroll`, `dim_department`, `dim_date` | `SUM(lop_days)` — unpaid absence and LOP | Department × Month | Suppress if employees < 5 | — | Payroll |

### Attendance Rate Working Day Rule
```
scheduled_days = working days in month (Mon–Fri, excluding 19 Indian holidays)
present_days   = actual present days (including WFH)
half_days      = 0.5 weight for half-day absence
attendance_rate = (present_days + 0.5 × half_days_unpaid) / scheduled_days
```

---

## Finance Metrics (M16 – M21)

| Code | Metric Name | SQL View | Source Tables | Formula | Grain | Privacy | Target | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **M16** | Revenue | `dw.metric_m16_revenue` | `fact_ledger` (accounts 4001–4004), `dim_account` | `-SUM(signed_amount_debit_positive)` for revenue accounts | Account × Month | None | ≥ ₹7.5 Cr/mo | Finance |
| **M17** | Net Profit | `dw.metric_m17_net_profit` | `fact_ledger` (accounts ≥ 4000) | `-SUM(revenue accounts) − SUM(expense accounts)` | Month | None | ≥ ₹0 | Finance |
| **M18** | Operating Margin | `dw.metric_m18_operating_margin` | `dw.metric_m17_net_profit` (view-on-view) | `net_profit / revenue × 100` | Month | None | ≥ 10% | Finance |
| **M19** | Payroll % of Revenue | `dw.metric_m19_payroll_pct_revenue` | `fact_payroll`, `fact_ledger` | `SUM(employer_cost) / revenue × 100` | Month | None | — | Finance |
| **M20** | Days Sales Outstanding | `dw.metric_m20_dso` | `fact_ledger` (account 1100), `fact_invoice` | `receivables_balance / (90d invoice revenue) × 90` | Month | None | ≤ 60 days | Finance |
| **M21** | Overdue Receivables | `dw.metric_m21_overdue_receivables` | `fact_invoice`, `dim_client` | `SUM(balance_due) WHERE status IN ('SENT','OVERDUE','PARTIALLY_PAID')` | Client | None | — | Finance |

> [!IMPORTANT]
> **Account Hierarchy Rule (DQ-04):** The ledger contains both group (heading) accounts and detail accounts. Only **detail accounts** are included in M16–M19. Summing a group account and its children together would double-count. The check `dq_check_log.check_code = 'DQ-C01'` verifies this monthly.

---

## Engineering Operations Metrics (M22 – M25)

| Code | Metric Name | SQL View | Source Tables | Formula | Grain | Privacy | Target | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **M22** | Task Completion Rate | `dw.metric_m22_task_completion_rate` | `fact_task`, `dim_team`, `dim_sprint` | `COUNT(status='Done') / COUNT(status ≠ 'Cancelled') × 100` | Team × Sprint | Suppress if tasks < 5 | ≥ 70% | Eng Ops |
| **M23** | On-Time Delivery Rate | `dw.metric_m23_ontime_delivery_rate` | `fact_task`, `dim_team`, `dim_sprint` | `COUNT(Done AND completed_on_time='Y') / COUNT(Done) × 100` | Team × Sprint | Suppress if Done < 5 | — | Eng Ops |
| **M24** | Velocity | `dw.metric_m24_velocity` | `fact_task`, `dim_team`, `dim_sprint` | `SUM(story_points) WHERE status = 'Done'` | Team × Sprint | None | — | Eng Ops |
| **M25** | Average Cycle Time | `dw.metric_m25_average_cycle_time` | `fact_task`, `dim_team`, `dim_sprint` | `AVG(completed_date − started_date)` for Done tasks with cycle_time ≥ 0 | Team × Sprint | Suppress if Done < 5 | — | Eng Ops |

---

## AI / ML Metrics (M26 – M28)

| Code | Metric Name | SQL View | Source Tables | Formula | Grain | Privacy | Target | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **M26** | Anomaly Flag Rate | `dw.metric_m26_anomaly_flag_rate` | `fact_anomaly` | `COUNT(flagged='Y') / COUNT(*) × 100` | Source × Month | None | — | AI/ML |
| **M27** | High-Risk Attrition Share | `dw.metric_m27_high_risk_share` | `fact_attrition_risk`, `dim_department` | `COUNT(risk_band='High') / COUNT(*) × 100` | Department | Suppress if scored < 10 | — | AI/ML |
| **M28** | Forecast Error (MAPE) | `dw.metric_m28_forecast_error` | `fact_forecast`, `fact_headcount_monthly`, `dim_department`, `dim_date` | `AVG(|actual − forecast| / actual) × 100` | Dept × Month | None | — | AI/ML |

---

## Mini Challenge Metric (M29)

| Code | Metric Name | SQL View | Source Tables | Formula | Grain | Privacy | Target | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **M29** | WFH Share | `dw.metric_m29_wfh_share` | `fact_attendance_monthly`, `dim_department`, `dim_date` | `SUM(wfh_days) / SUM(present_days) × 100` | Department × Month | Suppress if employees < 5 | — | HR Analytics |

> [!TIP]
> M29 was added as the Phase 1 Mini Challenge. It proves the platform's extensibility — a new metric can be added in under 45 minutes by defining the view in `sql/005_metric_views.sql` and adding a widget to the relevant Streamlit page.

---

## Data Quality Rules Linked to Metrics

| DQ Check | Rule | Metrics Protected | Severity |
| :--- | :--- | :--- | :--- |
| DQ-C01 | Payroll totals match ledger accounts 5001–5005 within ₹0.01 | M07, M09, M19 | Critical |
| DQ-C02 | Journal entries balanced (debit = credit per entry_id) | M16, M17, M18 | Critical |
| DQ-C03 | One payroll row per employee per month | M07–M12, M15 | Critical |
| DQ-C04 | No fact rows for employees absent from dim_employee | M01–M15 | Critical |
| DQ-C05 | No attendance records after employee exit date | M13, M14 | Warning |
| DQ-C06 | Unpaid absence in attendance reflected as LOP in payroll | M15 | Warning |
| DQ-C07 | Invoice paid ≤ total; balance_due ≥ 0 | M20, M21 | Warning |
| DQ-C08 | Expense total = amount_excl_gst + gst_amount within ₹0.01 | Finance pages | Warning |
| DQ-C09 | Task completed_date ≥ started_date; Done tasks have a date | M22–M25 | Warning |
| DQ-C10 | Leave end_date ≥ start_date | Leave analytics | Warning |
| DQ-C11 | AI predictions within 7 days of latest as_of_date | M26, M27 | Warning |
| DQ-C12 | SCD Type 2 valid_from…valid_to intervals do not overlap | All HR metrics | Critical |
| DQ-C13 | Pipeline completed within 24-hour SLA | All metrics | Critical |
| DQ-C14 | Small group suppression enforced at SQL view layer | All HR/privacy | Critical |

All 14 DQ check results are persisted to `dw.dq_check_log` after every ETL run (Phase 4, Task 17).

---

## RBAC Access Matrix

| Role | Raw Tables | Metric Views | Use Case |
| :--- | :--- | :--- | :--- |
| `role_hr` → `hr_readonly` | HR fact/dim tables | M01–M15, M27, M29 | HR managers & people analytics |
| `role_finance` → `fin_readonly` | Finance fact/dim tables | M16–M21, M09, M07 | Finance team — P&L and cash |
| `role_executive` → `exec_readonly` | **None** (no raw tables) | All 29 metric views | CEO/Founder — read-only KPI access |

Apply with: `psql -U pulseiq -d pulseiq -f sql/006_rbac.sql`

---

## Metric Catalog SQL Reference

The live metric catalog is queryable directly from the database:
```sql
SELECT metric_id, metric_name, business_definition, formula, source_table, grain, owner_team, unit
FROM dw.metric_catalog
ORDER BY metric_id;
```

The interactive searchable version is on the Streamlit dashboard: **Page 0 — About & Metric Lineage**.

---

*Last updated: Phase 4 — November 2026 | PulseIQ v4.0*
